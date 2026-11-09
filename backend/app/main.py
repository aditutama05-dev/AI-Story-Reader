from __future__ import annotations
import os
import hmac
import re
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Literal
from contextvars import ContextVar
import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .importers import _validate_archive_limits, _validate_public_url, extract_document, extract_webpage_report
from .vision_ocr import build_comic_source, build_document_page_prompt, build_ocr_prompt, make_gemini_vision_parts, make_openai_vision_content, normalize_page_image, parse_comic_ocr_response

PROJECT_DIR = Path(__file__).resolve().parents[1]
if not (PROJECT_DIR / "frontend").is_dir():
    PROJECT_DIR = PROJECT_DIR.parent
app = FastAPI(title="AI Story Reader API", version="0.2.0")
MAX_BATCH_IMPORT_CHARS = 20_000_000
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "https://aditutama05-dev.github.io").split(",") if origin.strip()], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

# Lightweight per-process abuse guard. Configure limits through environment variables.
_rate_buckets: dict[tuple[str, str], list[float]] = {}
_RATE_WINDOW_SECONDS = 60
_request_provider_api_key: ContextVar[str] = ContextVar('request_provider_api_key', default='')

@app.middleware("http")
async def protect_expensive_endpoints(request, call_next):
    path = request.url.path
    supplied_provider_key = request.headers.get("x-provider-api-key", "").strip()
    if len(supplied_provider_key) > 512:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"detail": "API key terlalu panjang."})
    key_context = _request_provider_api_key.set(supplied_provider_key)
    if path.startswith("/api/") and path not in {"/api/health", "/api/config"}:
        access_token = os.getenv("APP_ACCESS_TOKEN", "")
        if access_token:
            supplied = request.headers.get("authorization", "")
            supplied_token = supplied[7:].strip() if supplied.lower().startswith("bearer ") else ""
            if not hmac.compare_digest(supplied_token, access_token):
                from fastapi.responses import JSONResponse
                _request_provider_api_key.reset(key_context)
                return JSONResponse(status_code=401, content={"detail": "Token akses aplikasi tidak valid atau belum diisi."}, headers={"WWW-Authenticate": "Bearer"})
        client_ip = request.client.host if request.client else "unknown"
        bucket = "ai" if path in {"/api/narrate", "/api/continuity/extract", "/api/continuity/check", "/api/import/comic", "/api/import/pdf-ocr", "/api/audio"} else "import"
        limit = int(os.getenv("AI_REQUESTS_PER_MINUTE" if bucket == "ai" else "IMPORT_REQUESTS_PER_MINUTE", "8" if bucket == "ai" else "20"))
        now = time.monotonic()
        key = (client_ip, bucket)
        recent = [stamp for stamp in _rate_buckets.get(key, []) if now - stamp < _RATE_WINDOW_SECONDS]
        if len(recent) >= max(1, limit):
            from fastapi.responses import JSONResponse
            _request_provider_api_key.reset(key_context)
            return JSONResponse(status_code=429, content={"detail": "Batas permintaan sementara tercapai. Coba lagi dalam satu menit."}, headers={"Retry-After": "60"})
        recent.append(now)
        _rate_buckets[key] = recent
        if len(_rate_buckets) > 10000:
            for old_key, stamps in list(_rate_buckets.items()):
                if not stamps or now - stamps[-1] >= _RATE_WINDOW_SECONDS:
                    _rate_buckets.pop(old_key, None)
    try:
        return await call_next(request)
    finally:
        _request_provider_api_key.reset(key_context)


class NarrateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    title: str = "Bab tanpa judul"
    language: str = "id"
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = None
    model: str | None = None
    style: str = "MASTER FORM V2"
    continuity_context: str = Field(default="", max_length=12000)

class ContinuityExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=120000)
    title: str = Field(default="Chapter tanpa judul", max_length=200)
    existing_facts: list[dict] = Field(default_factory=list, max_length=100)
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = None
    model: str | None = None


class ContinuityCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=120000)
    title: str = Field(default="Chapter tanpa judul", max_length=200)
    prior_facts: list[dict] = Field(min_length=1, max_length=240)
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = None
    model: str | None = None


class URLBatchRequest(BaseModel):
    urls: list[str] = Field(min_length=2, max_length=10)

class AudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    voice: Literal["id-ID-GadisNeural", "id-ID-ArdiNeural"] = "id-ID-GadisNeural"
    rate: int = Field(default=0, ge=-50, le=50)

class NarrateResponse(BaseModel):
    narration: str
    provider: str
    model: str
    chunks_processed: int
    verification: dict = Field(default_factory=dict)

def provider_config(provider: str | None, model: str | None):
    selected = provider or os.getenv("AI_PROVIDER", "openrouter")
    selected_model = model or os.getenv("AI_MODEL", "openai/gpt-4o-mini")
    api_key = _request_provider_api_key.get() or os.getenv("AI_API_KEY", "")
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        response = await client.post(url, headers={"x-goog-api-key": api_key}, json={
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
    """Expose safe capability flags only; never return provider credentials or private tokens."""
    ai_available = bool(os.getenv("AI_API_KEY", "").strip())
    access_required = bool(os.getenv("APP_ACCESS_TOKEN", "").strip())
    return {
        "configured": ai_available,
        "ai_available": ai_available,
        "access_required": access_required,
        "public_mode": not access_required,
        "provider": os.getenv("AI_PROVIDER", "openrouter"),
        "model": os.getenv("AI_MODEL", "openai/gpt-4o-mini"),
        "supported_providers": ["openai", "openrouter", "gemini", "custom"],
        "max_upload_mb": 40,
        "personal_api_key_supported": True,
    }

@app.post("/api/import/url")
async def import_url(payload: dict):
    url = str(payload.get("url", "")).strip()
    if not url:
        raise HTTPException(status_code=400, detail="Masukkan URL chapter.")
    return await extract_webpage_report(url)

@app.post("/api/import/urls")
async def import_url_pages(payload: URLBatchRequest):
    """Combine explicitly supplied pages from one source domain in user-provided order."""
    from urllib.parse import urlparse
    urls = [value.strip() for value in payload.urls]
    if any(not value for value in urls) or len(set(urls)) != len(urls):
        raise HTTPException(status_code=400, detail="URL halaman harus terisi dan tidak boleh duplikat.")
    # Validate every URL before making the first outbound request. This prevents
    # partially fetching a batch when a later page is malformed or targets a
    # private/local address.
    validated_urls = [_validate_public_url(value) for value in urls]
    hosts = {urlparse(value).hostname.casefold().rstrip(".") for value in validated_urls}
    if len(hosts) != 1:
        raise HTTPException(status_code=400, detail="Semua halaman harus berasal dari domain yang sama.")
    results = []
    total_characters = 0
    for index, url in enumerate(validated_urls, start=1):
        result = await extract_webpage_report(url)
        total_characters += len(result["text"])
        if total_characters > MAX_BATCH_IMPORT_CHARS:
            raise HTTPException(status_code=413, detail="Gabungan halaman chapter melebihi batas 20 juta karakter.")
        results.append(result)
    combined_parts = []
    segments = []
    cursor = 0
    for index, item in enumerate(results, start=1):
        prefix = f"[Halaman {index}]\n"
        if combined_parts:
            cursor += 2
        cursor += len(prefix)
        start = cursor
        combined_parts.append(prefix + item["text"])
        cursor += len(item["text"])
        segments.append({"index": index, "url": item["source_url"], "characters": len(item["text"]), "source_start": start, "source_end": cursor})
    combined = "\n\n".join(combined_parts)
    warnings = ["Halaman digabung sesuai urutan URL yang dimasukkan pengguna.", "Pastikan semua URL adalah bagian dari chapter yang sama; endpoint tidak menebak atau mengikuti tautan chapter berikutnya."]
    return {"title": results[0]["title"], "text": combined, "characters": len(combined), "source_domain": next(iter(hosts)), "segments": segments, "verification": {"status": "review_required", "page_count": len(results), "warnings": warnings}}

@app.post("/api/import/file")
async def import_file(file: UploadFile = File(...)):
    filename = file.filename or "chapter.txt"
    content = await file.read(40 * 1024 * 1024 + 1)
    title, text = extract_document(filename, content)
    if not text:
        raise HTTPException(status_code=422, detail="Teks tidak ditemukan. PDF hasil scan memerlukan OCR.")
    return {"title": title, "text": text, "characters": len(text), "filename": filename}

@app.post("/api/import/pdf-ocr")
async def import_scanned_pdf(
    file: UploadFile = File(...),
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = Form(None),
    model: str | None = Form(None),
):
    """Render scanned PDF pages and transcribe them with a vision model."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Pilih file PDF.")
    raw_pdf = await file.read(40 * 1024 * 1024 + 1)
    if len(raw_pdf) > 40 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF melebihi batas 40 MB.")
    try:
        import fitz
        document = fitz.open(stream=raw_pdf, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PDF rusak atau tidak dapat dibuka.") from exc
    if document.needs_pass:
        document.close()
        raise HTTPException(status_code=403, detail="PDF terenkripsi atau memerlukan kata sandi.")
    if len(document) > 30:
        document.close()
        raise HTTPException(status_code=413, detail="OCR PDF dibatasi 30 halaman per proses.")
    if not len(document):
        document.close()
        raise HTTPException(status_code=422, detail="PDF tidak memiliki halaman.")
    page_images = []
    try:
        total_rendered_pixels = 0
        for index, page in enumerate(document, start=1):
            width = max(1, int(page.rect.width * 1.5))
            height = max(1, int(page.rect.height * 1.5))
            page_pixels = width * height
            total_rendered_pixels += page_pixels
            if max(width, height) > 6000 or page_pixels > 20_000_000 or total_rendered_pixels > 100_000_000:
                raise HTTPException(status_code=413, detail="Resolusi atau total area halaman PDF terlalu besar untuk OCR.")
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            image_data = pixmap.tobytes("png")
            page_images.append((index, normalize_page_image(image_data, "image/png")))
    finally:
        document.close()
    selected, selected_model, api_key, base_url = provider_config(provider, model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum tersedia. Masukkan API key pribadi di website atau konfigurasi AI_API_KEY pada environment server.")
    transcriptions = []
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            for index, image_bytes in page_images:
                prompt = build_document_page_prompt(index, len(page_images))
                if selected == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
                    response = await client.post(url, headers={"x-goog-api-key": api_key}, json={"contents": [{"role": "user", "parts": make_gemini_vision_parts(prompt, image_bytes)}], "generationConfig": {"temperature": 0.1}})
                    response.raise_for_status()
                    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    if not base_url:
                        raise HTTPException(status_code=503, detail="AI_BASE_URL belum diatur.")
                    response = await client.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": selected_model, "temperature": 0.1, "messages": [{"role": "user", "content": make_openai_vision_content(prompt, image_bytes)}]})
                    response.raise_for_status()
                    text = response.json()["choices"][0]["message"]["content"]
                transcriptions.append({"page": index, "text": text.strip()})
        cursor = 0
        for index, item in enumerate(transcriptions):
            if index:
                cursor += 2
            item["source_start"] = cursor
            cursor += len(item["text"])
            item["source_end"] = cursor
        combined = "\n\n".join(item["text"] for item in transcriptions)
        return {"title": Path(file.filename or "scanned-document.pdf").stem, "pages": transcriptions, "segments": [{"index": item["page"], "characters": len(item["text"]), "source_start": item["source_start"], "source_end": item["source_end"]} for item in transcriptions], "text": combined, "characters": len(combined), "provider": selected, "model": selected_model, "verification": {"status": "review_required", "page_count": len(transcriptions), "warnings": ["Hasil OCR harus diperiksa terhadap halaman PDF asli, terutama nama, angka, tanda baca, dan tata letak kompleks."]}}
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider OCR mengembalikan HTTP {exc.response.status_code}.") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Respons OCR dari provider tidak sesuai format.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat terhubung ke provider OCR.") from exc

def build_narration_verification(chunks: list[str], outputs: list[str]) -> dict:
    """Run conservative structural checks without claiming semantic completeness."""
    metrics, seen, duplicates, compressed, empty = [], {}, [], [], []
    for index, (source, narration) in enumerate(zip(chunks, outputs), start=1):
        normalized = re.sub(r"\s+", " ", narration).strip().casefold()
        duplicate_of = seen.get(normalized) if normalized else None
        if normalized and duplicate_of is None:
            seen[normalized] = index
        nonempty = bool(normalized)
        if not nonempty:
            empty.append(index)
        if not nonempty or len(narration) < max(80, int(len(source) * 0.18)):
            compressed.append(index)
        if duplicate_of is not None:
            duplicates.append({"chunk": index, "duplicate_of": duplicate_of})
        metrics.append({"chunk": index, "source_characters": len(source), "narration_characters": len(narration), "nonempty": nonempty, "duplicate_of": duplicate_of})
    warnings = [
        "Pemeriksaan ini hanya mendeteksi keluaran kosong, pemadatan ekstrem, dan keluaran potongan yang identik; belum membuktikan kesetiaan semantik atau urutan setiap peristiwa sumber.",
        "Bandingkan narasi dengan sumber asli, terutama transisi antarpotongan.",
    ]
    if empty:
        warnings.insert(0, "Ada potongan tanpa narasi; hasil belum lengkap.")
    if compressed:
        warnings.insert(0, "Ada potongan yang kosong atau jauh lebih pendek dari sumber; periksa kemungkinan detail terlewat.")
    if duplicates:
        warnings.insert(0, "Ada potongan yang menghasilkan narasi identik dengan potongan sebelumnya; periksa kemungkinan pengulangan.")
    return {"status":"review_required","method":"chunk_length_and_duplicate_output_checks","chunks":metrics,"empty_chunks":empty,"compressed_chunks":compressed,"duplicate_output_chunks":duplicates,"warnings":warnings}


def find_source_span(source: str, excerpt: str) -> tuple[int, int] | None:
    """Find a case-insensitive exact phrase while tolerating whitespace differences."""
    words = excerpt.split()
    if not words:
        return None
    pattern = r"\s+".join(re.escape(word) for word in words)
    match = re.search(pattern, source, flags=re.IGNORECASE)
    if not match:
        return None
    return match.start(), match.end()


@app.post("/api/continuity/extract")
async def extract_continuity_facts(request: ContinuityExtractRequest):
    provider, model, api_key, base_url = provider_config(request.provider, request.model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum tersedia. Masukkan API key pribadi di website atau konfigurasi AI_API_KEY pada environment server.")
    system = (
        "Ekstrak fakta kontinuitas yang eksplisit dari teks cerita. Kembalikan HANYA JSON valid berbentuk "
        '{"facts":[{"category":"character|relationship|location|term|event|conflict","fact":"...","sourceExcerpt":"..."}]}. '
        "Jangan simpulkan hal yang tidak dinyatakan. Kutipan sumber harus disalin verbatim dari teks input, bukan diparafrase. "
        "Jangan mengubah fakta lama; usulkan hanya fakta yang benar-benar didukung teks. Maksimal 30 fakta paling penting. "
        "Utamakan identitas tokoh, relasi yang dinyatakan, lokasi, istilah/kemampuan bernama, peristiwa penting, dan konflik aktif. "
        "Abaikan spekulasi, prediksi, dan opini narator."
    )
    user = f"Bagian: {request.title}\nFakta yang sudah tersimpan (hindari duplikasi): {request.existing_facts[:100]}\n\nTEKS SUMBER:\n{request.text}"
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            raw = await generate_text(client, provider, model, api_key, base_url, system, user)
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            raise ValueError("JSON tidak ditemukan")
        payload = __import__("json").loads(match.group(0))
        candidates = payload.get("facts", [])
        if not isinstance(candidates, list):
            raise ValueError("facts bukan array")
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise HTTPException(status_code=502, detail="Gagal mengambil fakta dari provider AI.") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI mengembalikan format fakta yang tidak valid.") from exc
    allowed = {"character", "relationship", "location", "term", "event", "conflict"}
    normalized_source = re.sub(r"\s+", " ", request.text).casefold()
    accepted, rejected = [], 0
    for item in candidates[:30]:
        if not isinstance(item, dict):
            rejected += 1
            continue
        category = str(item.get("category", "")).strip().lower()
        fact = str(item.get("fact", "")).strip()[:500]
        excerpt = str(item.get("sourceExcerpt", "")).strip()[:500]
        normalized_excerpt = re.sub(r"\s+", " ", excerpt).casefold()
        if category not in allowed or not fact or not excerpt or normalized_excerpt not in normalized_source:
            rejected += 1
            continue
        span = find_source_span(request.text, excerpt)
        if not span:
            rejected += 1
            continue
        accepted.append({"category": category, "fact": fact, "sourceExcerpt": excerpt,
                         "sourceStart": span[0], "sourceEnd": span[1]})
    return {"facts": accepted, "accepted": len(accepted), "rejected": rejected,
            "verification": {"status": "review_required", "method": "verbatim_source_excerpt_match",
            "warnings": ["Fakta diusulkan AI dan wajib ditinjau sebelum disimpan.", "Kutipan diperiksa sebagai teks verbatim setelah normalisasi spasi; makna fakta tidak diverifikasi otomatis."]}}


@app.post("/api/continuity/check")
async def check_continuity_contradictions(request: ContinuityCheckRequest):
    provider, model, api_key, base_url = provider_config(request.provider, request.model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum tersedia. Masukkan API key pribadi di website atau konfigurasi AI_API_KEY pada environment server.")
    facts = request.prior_facts[:240]
    system = (
        "Periksa apakah teks chapter SAAT INI secara eksplisit bertentangan dengan fakta kontinuitas dari bagian SEBELUMNYA. "
        "Kembalikan HANYA JSON valid: "
        '{"contradictions":[{"fact_index":0,"current_excerpt":"kutipan persis dari teks saat ini","explanation":"alasan pertentangan langsung","severity":"low|medium|high"}]}. '
        "fact_index adalah indeks nol-based dari daftar fakta yang diberikan. "
        "Laporkan hanya pertentangan langsung yang dinyatakan eksplisit oleh teks baru terhadap fakta lama. "
        "JANGAN menganggap fakta lama salah hanya karena tidak disebut lagi, tidak muncul, atau karena perubahan situasi/waktu yang masih masuk akal. "
        "Jangan menganggap perkembangan cerita, penyamaran, kebohongan tokoh, sudut pandang terbatas, atau informasi ambigu sebagai kontradiksi pasti. "
        "Jika ragu, abaikan. Kutipan current_excerpt wajib disalin verbatim dari teks chapter saat ini. "
        "Jangan mengubah, menghapus, atau memperbaiki fakta lama. Maksimal 40 temuan."
    )
    user = f"CHAPTER SAAT INI: {request.title}\nFAKTA DARI BAGIAN SEBELUMNYA (indeks dimulai dari 0):\n{facts}\n\nTEKS SUMBER CHAPTER SAAT INI:\n{request.text}"
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            raw = await generate_text(client, provider, model, api_key, base_url, system, user)
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            raise ValueError("JSON tidak ditemukan")
        payload = __import__("json").loads(match.group(0))
        candidates = payload.get("contradictions", [])
        if not isinstance(candidates, list):
            raise ValueError("contradictions bukan array")
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise HTTPException(status_code=502, detail="Gagal memeriksa kontinuitas melalui provider AI.") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI mengembalikan format pemeriksaan kontinuitas yang tidak valid.") from exc

    normalized_source = re.sub(r"\s+", " ", request.text).casefold()
    accepted, rejected = [], 0
    for item in candidates[:40]:
        if not isinstance(item, dict):
            rejected += 1
            continue
        fact_index = item.get("fact_index")
        excerpt = str(item.get("current_excerpt", "")).strip()[:700]
        explanation = str(item.get("explanation", "")).strip()[:700]
        severity = str(item.get("severity", "medium")).strip().lower()
        normalized_excerpt = re.sub(r"\s+", " ", excerpt).casefold()
        if (not isinstance(fact_index, int) or isinstance(fact_index, bool)
                or fact_index < 0 or fact_index >= len(facts)
                or not excerpt or normalized_excerpt not in normalized_source
                or not explanation or severity not in {"low", "medium", "high"}):
            rejected += 1
            continue
        fact = facts[fact_index]
        span = find_source_span(request.text, excerpt)
        if not span:
            rejected += 1
            continue
        accepted.append({
            "fact_index": fact_index,
            "current_start": span[0],
            "current_end": span[1],
            "prior_fact": str(fact.get("fact", ""))[:500],
            "prior_category": str(fact.get("category", ""))[:40],
            "prior_chapter": str(fact.get("chapterTitle", ""))[:200],
            "current_excerpt": excerpt,
            "explanation": explanation,
            "severity": severity,
        })
    return {
        "contradictions": accepted, "accepted": len(accepted), "rejected": rejected,
        "verification": {
            "status": "review_required",
            "method": "prior_fact_index_and_verbatim_current_excerpt_match",
            "warnings": [
                "Temuan adalah dugaan AI, bukan keputusan kanon. Tinjau konteks cerita sebelum mengubah fakta apa pun.",
                "Kutipan baru dicocokkan dengan teks chapter saat ini; pemeriksaan ini tidak membuktikan bahwa interpretasi kontradiksi benar.",
                "Tidak ada fakta lama yang diubah atau dihapus otomatis.",
            ],
        },
    }



@app.post("/api/narrate", response_model=NarrateResponse)
async def narrate(request: NarrateRequest):
    provider, model, api_key, base_url = provider_config(request.provider, request.model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum tersedia. Masukkan API key pribadi di website atau konfigurasi AI_API_KEY pada environment server.")
    chunks = split_into_chunks(request.text)
    system_prompt = ("Kamu adalah narator cerita profesional untuk AI Story Reader. Ubah teks sumber menjadi narasi bahasa Indonesia yang natural, "
        "mengalir seperti seseorang sedang menceritakan seluruh kejadian kepada pendengar. Untuk keluaran Bahasa Indonesia, gunakan bahasa yang jelas dan nyaman didengar; "
        "jika dialog atau teks OCR berasal dari bahasa lain, sampaikan maknanya dalam Bahasa Indonesia secara setia tanpa menebak. Pertahankan nama, gelar, istilah khas, angka, dan SFX penting; "
        "jangan menerjemahkan nama atau istilah secara spekulatif. Terapkan MASTER FORM V2 dengan prioritas utama pada kelengkapan, "
        "ketepatan, dan urutan kronologis; hasilnya bukan ringkasan, resensi, analisis, atau sinopsis. "
        "Ceritakan setiap kejadian penting dan perkembangan kecil yang mengubah situasi: siapa melakukan apa, kepada siapa, dengan cara apa, di mana, kapan, "
        "apa pemicunya, bagaimana reaksi tokoh lain, dan apa akibat langsungnya. Pertahankan urutan adegan, perpindahan tempat/waktu, tindakan, gerak tubuh, "
        "ekspresi wajah, bahasa tubuh, emosi, suasana, ketegangan, detail pertarungan, strategi, luka, kemampuan, benda, petunjuk, serta perubahan hubungan dan konflik. "
        "Pertahankan isi dialog penting melalui parafrasa yang setia; jangan menghilangkan maksud, respons, perdebatan, ancaman, lelucon, atau informasi yang disampaikan. "
        "Jangan menggabungkan beberapa kejadian menjadi satu kalimat ringkasan jika detailnya bermakna. Jangan mempercepat cerita dengan frasa seperti mereka lalu bertarung "
        "ketika sumber menjelaskan rangkaian gerakan atau strategi. Jangan mengarang dialog, motif, pikiran, latar, kemampuan, atau kejadian yang tidak didukung sumber. "
        "Jika sumber ambigu atau terpotong, pertahankan ketidakpastian dan jangan menebak. Jaga nama tokoh, sapaan, istilah, gelar, sudut pandang, hubungan, dan fakta dunia cerita secara konsisten. "
        "Jangan menambah pembukaan, penutup, komentar AI, heading, daftar, nomor bagian, atau pemisah buatan. Mulai langsung dari peristiwa sumber dan akhiri pada batas sumber. "
        "Jika sumber komik memakai penanda struktural seperti [Halaman n], [Panel n], [Dialog n], [Pikiran n], [Caption n], atau [SFX n], gunakan penanda itu hanya untuk memahami urutan dan jenis teks; jangan membacakan labelnya sebagai bagian cerita. Ceritakan isi teksnya secara natural dan jangan menebak identitas pembicara. "
        "Jika input terdiri dari potongan, sambungkan dengan mulus tanpa mengulang narasi sebelumnya dan jangan menghilangkan peristiwa baru pada potongan saat ini.")
    continuity_context = request.continuity_context.strip()
    if continuity_context:
        system_prompt += (" Gunakan CATATAN KONTINUITAS hanya sebagai referensi tambahan untuk menjaga konsistensi nama, relasi, lokasi, istilah, dan konflik. "
            "CATATAN INI BUKAN SUMBER KEJADIAN CHAPTER SAAT INI: jangan memasukkan kejadian, dialog, motif, atau detail yang tidak ada di teks sumber. "
            "Jika catatan bertentangan dengan teks sumber saat ini, utamakan teks sumber dan pertahankan ketidakpastian.\n")
    outputs, previous_context = [], ""
    try:
        async with httpx.AsyncClient(timeout=240) as client:
            for index, chunk in enumerate(chunks):
                continuation = ("Mulai narasi dari awal chapter." if index == 0 else
                    "Lanjutkan langsung dari potongan sebelumnya. Jangan mengulang peristiwa yang sudah diceritakan. "
                    "Ceritakan seluruh peristiwa baru dalam potongan ini.")
                continuity_block = (f"CATATAN KONTINUITAS (referensi sekunder, bukan bukti kejadian):\n{continuity_context}\n\n" if continuity_context else "")
                user_prompt = (continuity_block + f"Judul: {request.title}\nGaya: {request.style}\nBahasa: {request.language}\n"
                    f"Potongan {index + 1}/{len(chunks)}. {continuation}\n"
                    f"KONTEKS NARASI SEBELUMNYA (jangan diulang):\n{previous_context or '[awal chapter]'}\n\n"
                    f"TEKS SUMBER POTONGAN INI:\n{chunk}")
                output = (await generate_text(client, provider, model, api_key, base_url, system_prompt, user_prompt)).strip()
                outputs.append(output)
                previous_context = output[-2200:]
        verification = build_narration_verification(chunks, outputs)
        return NarrateResponse(narration="\n\n".join(outputs), provider=provider, model=model, chunks_processed=len(chunks), verification=verification)
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
    archive_files = [upload for upload in files if Path(upload.filename or "").suffix.lower() in {".cbz", ".zip"}]
    if archive_files and len(files) != 1:
        raise HTTPException(status_code=400, detail="Unggah satu arsip CBZ/ZIP saja atau pilih halaman gambar satu per satu; arsip tidak dapat dicampur dengan gambar.")
    page_inputs: list[tuple[str, bytes, str]] = []
    try:
        if len(files) == 1 and (files[0].filename or "").lower().endswith((".cbz", ".zip")):
            archive_bytes = await files[0].read(40 * 1024 * 1024 + 1)
            if len(archive_bytes) > 40 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Arsip komik melebihi batas 40 MB.")
            with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
                _validate_archive_limits(archive)
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
            total_upload_bytes = 0
            for upload in files:
                raw = await upload.read(15 * 1024 * 1024 + 1)
                if len(raw) > 15 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="Setiap halaman dibatasi 15 MB.")
                total_upload_bytes += len(raw)
                if total_upload_bytes > 100 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="Total seluruh halaman komik dibatasi 100 MB per proses.")
                page_inputs.append((upload.filename or "page", raw, upload.content_type or ""))

    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Arsip CBZ/ZIP rusak atau tidak valid.") from exc

    selected, selected_model, api_key, base_url = provider_config(provider, model)
    if not api_key:
        raise HTTPException(status_code=503, detail="AI belum tersedia. Masukkan API key pribadi di website atau konfigurasi AI_API_KEY pada environment server.")

    pages = []
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            for index, (filename, raw, media_type) in enumerate(page_inputs, start=1):
                image_bytes = normalize_page_image(raw, media_type)
                prompt = build_ocr_prompt(index, len(page_inputs), direction)
                if selected == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
                    response = await client.post(url, headers={"x-goog-api-key": api_key}, json={
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

                parsed = parse_comic_ocr_response(transcription)
                pages.append({
                    "page": index,
                    "filename": filename or f"page-{index}",
                    "text": parsed["text"],
                    "panels": parsed["panels"],
                    "warnings": parsed["warnings"],
                    "structured": parsed["structured"],
                })

        combined, segments = build_comic_source(pages)
        panel_count = sum(len(page["panels"]) for page in pages)
        structured_page_count = sum(1 for page in pages if page["structured"])
        fallback_page_count = len(pages) - structured_page_count
        warnings = [
            "Urutan panel dan balon disusun oleh model vision berdasarkan gambar, bukan diverifikasi secara independen. Periksa ulang panel inset, tata letak tidak biasa, teks kecil, nama, angka, dan SFX.",
            "Hasil OCR dapat keliru atau melewatkan teks. Sumber gambar asli tetap menjadi acuan; tinjau dan edit transkripsi sebelum membuat narasi.",
        ]
        for page in pages:
            warnings.extend(f"Halaman {page['page']}: {warning}" for warning in page["warnings"])
        if len(warnings) > 22:
            warnings = warnings[:22] + ["Sebagian peringatan tambahan tidak ditampilkan."]

        return {
            "title": "Hasil OCR komik",
            "pages": pages,
            "segments": segments,
            "text": combined,
            "characters": len(combined),
            "provider": selected,
            "model": selected_model,
            "reading_direction": direction,
            "verification": {
                "status": "review_required",
                "page_count": len(pages),
                "panel_count": panel_count,
                "structured_page_count": structured_page_count,
                "fallback_page_count": fallback_page_count,
                "warnings": warnings,
            },
        }
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider AI gagal memproses gambar (HTTP {exc.response.status_code}). Pastikan model mendukung input gambar.") from exc
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Respons OCR dari provider tidak sesuai format atau terlalu besar.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat terhubung ke provider OCR/vision.") from exc

# GitHub Pages hosts the frontend separately. Keep local combined hosting optional;
# Vercel excludes frontend/ from the Python Function bundle to reduce its size.
_frontend_dir = PROJECT_DIR / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
