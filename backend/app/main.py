from __future__ import annotations
import os
import re
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Literal
import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .importers import extract_document, extract_webpage_report
from .vision_ocr import build_ocr_prompt, make_gemini_vision_parts, make_openai_vision_content, normalize_page_image

PROJECT_DIR = Path(__file__).resolve().parents[1]
if not (PROJECT_DIR / "frontend").is_dir():
    PROJECT_DIR = PROJECT_DIR.parent
app = FastAPI(title="AI Story Reader API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

# Lightweight per-process abuse guard. Configure limits through environment variables.
_rate_buckets: dict[tuple[str, str], list[float]] = {}
_RATE_WINDOW_SECONDS = 60

@app.middleware("http")
async def protect_expensive_endpoints(request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in {"/api/health", "/api/config"}:
        client_ip = request.client.host if request.client else "unknown"
        bucket = "ai" if path in {"/api/narrate", "/api/import/comic", "/api/audio"} else "import"
        limit = int(os.getenv("AI_REQUESTS_PER_MINUTE" if bucket == "ai" else "IMPORT_REQUESTS_PER_MINUTE", "8" if bucket == "ai" else "20"))
        now = time.monotonic()
        key = (client_ip, bucket)
        recent = [stamp for stamp in _rate_buckets.get(key, []) if now - stamp < _RATE_WINDOW_SECONDS]
        if len(recent) >= max(1, limit):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429, content={"detail": "Batas permintaan sementara tercapai. Coba lagi dalam satu menit."}, headers={"Retry-After": "60"})
        recent.append(now)
        _rate_buckets[key] = recent
        if len(_rate_buckets) > 10000:
            for old_key, stamps in list(_rate_buckets.items()):
                if not stamps or now - stamps[-1] >= _RATE_WINDOW_SECONDS:
                    _rate_buckets.pop(old_key, None)
    return await call_next(request)


class NarrateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    title: str = "Bab tanpa judul"
    language: str = "id"
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = None
    model: str | None = None
    style: str = "MASTER FORM V2"

class AudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    voice: str = "id-ID-GadisNeural"
    rate: int = Field(default=0, ge=-50, le=50)

class NarrateResponse(BaseModel):
    narration: str
    provider: str
    model: str
    chunks_processed: int

def provider_config(provider: str | None, model: str | None):
    selected = provider or os.getenv("AI_PROVIDER", "openrouter")
    selected_model = model or os.getenv("AI_MODEL", "openai/gpt-4o-mini")
    api_key = os.getenv("AI_API_KEY", "")
    base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    if selected == "openai":
        base_url, selected_model = "https://api.openai.com/v1", model or os.getenv("AI_MODEL", "gpt-4o-mini")
    elif selected == "custom":
        base_url = os.getenv("AI_BASE_URL", "").rstrip("/")
    elif selected == "gemini":
        selected_model = model or os.getenv("AI_MODEL", "gemini-2.5-flash")
    return selected, selected_model, api_key, base_url

def split_into_chunks(text: str, limit: int = 16000) -> list[str]:
    paragraphs = [p.strip() for p in text.replace("\r\n", "\n").split("\n") if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        while len(paragraph) > limit:
            if current:
                chunks.append(current)
                current = ""
            cut = paragraph.rfind(" ", 0, limit)
            if cut < limit // 2:
                cut = limit
            chunks.append(paragraph[:cut].strip())
            paragraph = paragraph[cut:].strip()
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > limit and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text]

async def generate_text(client, provider, model, api_key, base_url, system_prompt, user_prompt):
    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        response = await client.post(url, json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": float(os.getenv("AI_TEMPERATURE", "0.4"))},
        })
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    if not base_url:
        raise HTTPException(status_code=503, detail="AI_BASE_URL belum diatur.")
    response = await client.post(f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": float(os.getenv("AI_TEMPERATURE", "0.4")),
              "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]})
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-story-reader-api", "version": app.version}

@app.get("/api/config")
def public_config():
    return {"configured": bool(os.getenv("AI_API_KEY")), "provider": os.getenv("AI_PROVIDER", "openrouter"),
            "model": os.getenv("AI_MODEL", "openai/gpt-4o-mini"),
            "supported_providers": ["openai", "openrouter", "gemini", "custom"], "max_upload_mb": 40}

@app.post("/api/import/url")
async def import_url(payload: dict):
    url = str(payload.get("url", "")).strip()
    if not url:
        raise HTTPException(status_code=400, detail="Masukkan URL chapter.")
    return await extract_webpage_report(url)

@app.post("/api/import/file")
async def import_file(file: UploadFile = File(...)):
    filename = file.filename or "chapter.txt"
    content = await file.read(40 * 1024 * 1024 + 1)
    title, text = extract_document(filename, content)
    if not text:
        raise HTTPException(status_code=422, detail="Teks tidak ditemukan. PDF hasil scan memerlukan OCR.")
    return {"title": title, "text": text, "characters": len(text), "filename": filename}

@app.post("/api/narrate", response_model=NarrateResponse)
async def narrate(request: NarrateRequest):
    provider, model, api_key, base_url = provider_config(request.provider, request.model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum dikonfigurasi. Tambahkan AI_API_KEY pada environment server.")
    chunks = split_into_chunks(request.text)
    system_prompt = ("Kamu adalah AI Story Reader profesional. Ceritakan ulang sumber menjadi narasi bahasa Indonesia "
        "yang natural, kronologis, mengalir seperti mendongeng. Ikuti MASTER FORM V2: pertahankan kejadian, tindakan, "
        "dialog penting dengan parafrasa, ekspresi, emosi, suasana, pertarungan, dan perkembangan konflik. Jangan "
        "mengarang kejadian atau meringkas berlebihan. Jangan membuat heading atau pembagian buatan. Jaga nama, "
        "istilah, sudut pandang, urutan waktu, dan kesinambungan.")
    outputs, previous_context = [], ""
    try:
        async with httpx.AsyncClient(timeout=240) as client:
            for index, chunk in enumerate(chunks):
                continuation = ("Mulai narasi dari awal chapter." if index == 0 else
                    "Lanjutkan langsung dari potongan sebelumnya. Jangan mengulang peristiwa yang sudah diceritakan. "
                    "Ceritakan seluruh peristiwa baru dalam potongan ini.")
                user_prompt = (f"Judul: {request.title}\nGaya: {request.style}\nBahasa: {request.language}\n"
                    f"Potongan {index + 1}/{len(chunks)}. {continuation}\n"
                    f"KONTEKS NARASI SEBELUMNYA (jangan diulang):\n{previous_context or '[awal chapter]'}\n\n"
                    f"TEKS SUMBER POTONGAN INI:\n{chunk}")
                output = (await generate_text(client, provider, model, api_key, base_url, system_prompt, user_prompt)).strip()
                outputs.append(output)
                previous_context = output[-2200:]
        return NarrateResponse(narration="\n\n".join(outputs), provider=provider, model=model, chunks_processed=len(chunks))
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider AI mengembalikan HTTP {exc.response.status_code}.") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Respons provider AI tidak sesuai format.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat terhubung ke provider AI.") from exc


@app.post("/api/audio")
async def generate_chapter_audio(payload: AudioRequest):
    """Generate one MP3 for the complete story part using Edge TTS."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(payload.text, payload.voice, rate=f"{payload.rate:+d}%")
        chunks = []
        total_bytes = 0
        async for item in communicate.stream():
            if item.get("type") == "audio":
                data = item.get("data", b"")
                total_bytes += len(data)
                if total_bytes > 80 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="Audio chapter melebihi batas 80 MB.")
                chunks.append(data)
        if not chunks:
            raise HTTPException(status_code=502, detail="Provider TTS tidak menghasilkan audio.")
        return Response(content=b"".join(chunks), media_type="audio/mpeg", headers={"Content-Disposition": 'attachment; filename="ai-story-reader-chapter.mp3"', "Cache-Control": "no-store"})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Gagal membuat MP3. Periksa koneksi server ke layanan TTS dan coba lagi.") from exc

@app.post("/api/import/comic")
async def import_comic_pages(
    files: list[UploadFile] = File(...),
    direction: Literal["rtl", "ltr", "vertical"] = Form("vertical"),
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = Form(None),
    model: str | None = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="Pilih minimal satu halaman komik.")
    page_inputs: list[tuple[str, bytes, str]] = []
    try:
        if len(files) == 1 and (files[0].filename or "").lower().endswith((".cbz", ".zip")):
            archive_bytes = await files[0].read(40 * 1024 * 1024 + 1)
            if len(archive_bytes) > 40 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Arsip komik melebihi batas 40 MB.")
            with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
                image_names = [name for name in archive.namelist() if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and not name.startswith("__MACOSX/")]
                image_names.sort(key=lambda name: [(0, int(part)) if part.isdigit() else (1, part.casefold()) for part in re.split(r"(\d+)", name)])
                if not image_names:
                    raise HTTPException(status_code=422, detail="Arsip tidak berisi halaman JPG, PNG, atau WEBP.")
                if len(image_names) > 30:
                    raise HTTPException(status_code=413, detail="Maksimal 30 halaman per proses.")
                total_uncompressed = 0
                for name in image_names:
                    raw = archive.read(name)
                    total_uncompressed += len(raw)
                    if len(raw) > 15 * 1024 * 1024 or total_uncompressed > 100 * 1024 * 1024:
                        raise HTTPException(status_code=413, detail="Ukuran halaman atau total isi arsip terlalu besar.")
                    suffix = Path(name).suffix.lower()
                    media = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}[suffix]
                    page_inputs.append((Path(name).name, raw, media))
        else:
            if len(files) > 30:
                raise HTTPException(status_code=413, detail="Maksimal 30 halaman per proses.")
            for upload in files:
                raw = await upload.read(15 * 1024 * 1024 + 1)
                if len(raw) > 15 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="Setiap halaman dibatasi 15 MB.")
                page_inputs.append((upload.filename or "page", raw, upload.content_type or ""))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Arsip CBZ/ZIP rusak atau tidak valid.") from exc

    selected, selected_model, api_key, base_url = provider_config(provider, model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum dikonfigurasi. Tambahkan AI_API_KEY pada environment server.")
    pages = []
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            for index, (filename, raw, media_type) in enumerate(page_inputs, start=1):
                image_bytes = normalize_page_image(raw, media_type)
                prompt = build_ocr_prompt(index, len(page_inputs), direction)
                if selected == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
                    response = await client.post(url, json={
                        "contents": [{"role": "user", "parts": make_gemini_vision_parts(prompt, image_bytes)}],
                        "generationConfig": {"temperature": 0.1},
                    })
                    response.raise_for_status()
                    transcription = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    if not base_url:
                        raise HTTPException(status_code=503, detail="AI_BASE_URL belum diatur.")
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": selected_model, "temperature": 0.1,
                              "messages": [{"role": "user", "content": make_openai_vision_content(prompt, image_bytes)}]},
                    )
                    response.raise_for_status()
                    transcription = response.json()["choices"][0]["message"]["content"]
                pages.append({"page": index, "filename": filename or f"page-{index}", "text": transcription.strip()})
        combined = "\n\n".join(f"[Halaman {page['page']}]\n{page['text']}" for page in pages)
        return {"title": "Hasil OCR komik", "pages": pages, "text": combined, "characters": len(combined),
                "provider": selected, "model": selected_model, "reading_direction": direction}
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider AI gagal memproses gambar (HTTP {exc.response.status_code}). Pastikan model mendukung input gambar.") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Respons OCR dari provider tidak sesuai format.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat terhubung ke provider OCR/vision.") from exc

app.mount("/", StaticFiles(directory=PROJECT_DIR / "frontend", html=True), name="frontend")
