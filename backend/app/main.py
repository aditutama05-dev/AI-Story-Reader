from __future__ import annotations
import os
from pathlib import Path
from typing import Literal
import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .importers import extract_document, extract_webpage

PROJECT_DIR = Path(__file__).resolve().parents[2]
app = FastAPI(title="AI Story Reader API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

class NarrateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    title: str = "Bab tanpa judul"
    language: str = "id"
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = None
    model: str | None = None
    style: str = "MASTER FORM V2"

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
    title, text = await extract_webpage(url)
    return {"title": title, "text": text, "characters": len(text), "source_url": url}

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

app.mount("/", StaticFiles(directory=PROJECT_DIR / "frontend", html=True), name="frontend")
