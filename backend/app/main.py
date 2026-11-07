from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parents[1]
app = FastAPI(title="AI Story Reader API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NarrateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)
    title: str = "Bab tanpa judul"
    language: str = "id"
    provider: Literal["openai", "openrouter", "gemini", "custom"] | None = None
    model: str | None = None
    style: str = "MASTER FORM V2"


class NarrateResponse(BaseModel):
    narration: str
    provider: str
    model: str


def provider_config(provider: str | None, model: str | None):
    selected = provider or os.getenv("AI_PROVIDER", "openrouter")
    selected_model = model or os.getenv("AI_MODEL", "openai/gpt-4o-mini")
    api_key = os.getenv("AI_API_KEY", "")
    base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    if selected == "openai":
        base_url = "https://api.openai.com/v1"
        selected_model = model or os.getenv("AI_MODEL", "gpt-4o-mini")
    elif selected == "openrouter":
        base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    elif selected == "custom":
        base_url = os.getenv("AI_BASE_URL", "").rstrip("/")
    elif selected == "gemini":
        selected_model = model or os.getenv("AI_MODEL", "gemini-2.5-flash")
    return selected, selected_model, api_key, base_url


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-story-reader-api", "version": app.version}


@app.get("/api/config")
def public_config():
    # Never return API keys or secret values to the browser.
    return {
        "configured": bool(os.getenv("AI_API_KEY")),
        "provider": os.getenv("AI_PROVIDER", "openrouter"),
        "model": os.getenv("AI_MODEL", "openai/gpt-4o-mini"),
        "supported_providers": ["openai", "openrouter", "gemini", "custom"],
    }


@app.post("/api/narrate", response_model=NarrateResponse)
async def narrate(request: NarrateRequest):
    provider, model, api_key, base_url = provider_config(request.provider, request.model)
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI belum dikonfigurasi. Tambahkan AI_API_KEY pada environment server.",
        )

    system_prompt = (
        "Kamu adalah AI Story Reader profesional. Ceritakan ulang sumber menjadi "
        "narasi bahasa Indonesia yang natural, kronologis, mengalir seperti mendongeng. "
        "Ikuti MASTER FORM V2: pertahankan semua kejadian penting, tindakan, dialog "
        "penting dengan parafrasa, ekspresi, emosi, suasana, pertarungan, dan perkembangan "
        "konflik. Jangan mengarang fakta atau kejadian. Jangan meringkas secara berlebihan. "
        "Jangan menghilangkan detail yang membangun kesinambungan. Jangan membuat judul "
        "bagian tambahan atau membagi chapter menjadi bagian-bagian buatan. Jika input "
        "terpotong, jangan berpura-pura mengetahui kelanjutannya."
    )
    user_prompt = (
        f"Judul sumber: {request.title}\nGaya: {request.style}\n"
        f"Bahasa keluaran: {request.language}\n\nSUMBER:\n{request.text}"
    )

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            if provider == "gemini":
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent?key={api_key}"
                )
                payload = {
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {"temperature": float(os.getenv("AI_TEMPERATURE", "0.4"))},
                }
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                output = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                if not base_url:
                    raise HTTPException(status_code=503, detail="AI_BASE_URL belum diatur.")
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": float(os.getenv("AI_TEMPERATURE", "0.4")),
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
                response.raise_for_status()
                output = response.json()["choices"][0]["message"]["content"]
        return NarrateResponse(narration=output, provider=provider, model=model)
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider AI mengembalikan HTTP {exc.response.status_code}.") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Respons dari provider AI tidak sesuai format.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat terhubung ke provider AI.") from exc


# Keep the catch-all frontend mount last so API routes remain reachable.
app.mount("/", StaticFiles(directory=PROJECT_DIR / "frontend", html=True), name="frontend")
