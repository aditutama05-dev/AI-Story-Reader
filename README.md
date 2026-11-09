# Novelith AI

> **Buka aplikasi:** [Novelith AI — Website](https://aditutama05-dev.github.io/AI-Story-Reader/)
>
> Website statis sudah berhasil diterbitkan melalui GitHub Actions. Fitur yang membutuhkan API (impor URL/file, OCR, narasi AI, dan MP3) tetap menunggu deployment backend. Halaman README ini adalah dokumentasi proyek, bukan antarmuka aplikasi.

Novelith AI is a personal **website** for turning novels, light novels, web novels, digital books, manga, manhwa, manhua, and comics into detailed Indonesian narration that can be read and listened to in a browser.

The product is a browser website, not a native Android or desktop application.

## Product requirements and project documents

- [Feature specification](FEATURES.md)
- [Project context](docs/PROJECT_CONTEXT.md)
- [Feature roadmap](docs/FEATURE_ROADMAP.md)
- [Accessibility and screen-access boundaries](docs/SCREEN_ACCESS_LIMITS.md)
- [URL and file source ingestion](docs/SOURCE_INGESTION.md)
- [Story data model](docs/STORY_DATA_MODEL.md)
- [Technical architecture](docs/TECHNICAL_ARCHITECTURE.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Story narration standard — MASTER FORM V2](docs/STORY_NARRATION_STANDARD.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Changelog](docs/CHANGELOG.md)

## Current implementation

### Website frontend

- Responsive HTML/CSS/JavaScript interface.
- Dark navy and bright-blue visual palette.
- Accessibility baseline: semantic landmarks, labels, keyboard focus, skip navigation, high contrast, text sizing, reading spacing, reduced motion, and local preference persistence.
- TalkBack and screen-reader-compatible story text.
- Optional browser speech synthesis with voice/speed selection and active-paragraph highlighting.
- Complete-chapter MP3 generation, in-page audio playback, ±15-second seek, and MP3 download.
- Local chapter restoration, automatic reading-position persistence, bookmark, and resume controls using browser IndexedDB.
- URL, explicitly ordered same-domain multi-page URL, file, pasted-text, and multi-image input controls.
- CBZ/ZIP comic archive upload with natural page ordering, plus structured panel/dialogue/thought/caption/SFX OCR and page/panel/balloon evidence selection.
- Series → Arc → Volume → Chapter library with separate original-source and narration storage, using IndexedDB plus JSON backup/restore.
- Configurable public API base URL in `frontend/config.js`. This file may contain a public API origin only; never put API keys or provider secrets in it.

### Python API backend

- FastAPI application in `backend/app/main.py`.
- URL import with generic HTML extraction, source warnings, and explicit multi-page chapter assembly.
- In-memory per-client rate limits for import and AI/audio endpoints.
- TXT, Markdown, HTML, text-based PDF, scanned PDF OCR (vision model), DOCX, and EPUB extraction.
- Multi-image, CBZ/ZIP, and scanned-PDF OCR for JPG/JPEG, PNG, and WEBP page images using a configurable vision-capable provider.
- Structured comic OCR output preserves model-proposed panel and balloon order, falls back to plain text when JSON is invalid, and remains review-required before narration.
- Full-chapter MP3 generation using Edge TTS.
- Context-aware chunked Indonesian narration.
- Provider configuration for OpenAI, OpenRouter, Gemini, and compatible endpoints through server environment variables.

## Pilihan penggunaan AI: API key pribadi atau layanan bersama

Pengguna dapat memasukkan API key provider miliknya sendiri. Kunci dikirim melalui header HTTPS ke backend, hanya disimpan di `sessionStorage` browser selama sesi, dan tidak disimpan permanen oleh website. Biaya penggunaan ditagihkan langsung oleh provider kepada pemilik API key. Pengelola juga dapat menyediakan satu key bersama melalui secret backend `AI_API_KEY`; dalam mode itu pengelola menanggung seluruh biaya dan risiko penyalahgunaan. Jangan pernah menaruh key di file frontend atau Git. Backend tetap diperlukan untuk impor URL, OCR, dan pemrosesan AI; GitHub Pages hanya meng-host file website statis. Perpustakaan, progres, dan bookmark tetap tersimpan lokal di IndexedDB perangkat pengguna.
## Run locally

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
```

Copy `.env.example` to `.env`, then configure the provider key in the server environment. Do not commit `.env`.

Run:

```bash
uvicorn backend.app.main:app --reload --env-file .env
```

Open the local address shown by Uvicorn (normally `http://127.0.0.1:8000`).

If running from inside the `backend/` directory instead, use:

```bash
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend
python -m unittest discover -s tests -v
```

GitHub Actions also checks Python tests, frontend JavaScript syntax, and backend compilation.

## Hosting direction

The low-cost hybrid hosting split is:

- Website: GitHub Pages (static files from `frontend/`).
- API: a separately deployed backend service.
- A Vercel Python Function deployment is prepared at the repository root using the existing FastAPI application. The free Hobby plan is intended for personal projects and has usage limits; confirm the account's signup/billing prompts before proceeding. Vercel Functions also enforce a 4.5 MB request/response body limit, so large PDF/EPUB/comic uploads need a future direct-to-storage flow or a different backend host.

When the API is deployed separately, set `window.AI_STORY_READER_API_BASE` in `frontend/config.js` to the public API origin. The backend defaults CORS to the GitHub Pages origin; configure `CORS_ORIGINS` in Vercel only if additional trusted origins are needed. The API base URL is public configuration, not a secret.

The static frontend is published through GitHub Pages. Vercel Python/FastAPI deployment files (`index.py`, root `requirements.txt`, and `vercel.json`) are prepared, but the backend is not live until the repository owner imports the project into a free Hobby account and the `/api/health` endpoint is verified. Server-dependent import, OCR, AI narration, and MP3 generation remain unavailable from the public website until the API is connected.

## Security and privacy

- Never commit API keys, passwords, tokens, private source files, or generated private audio.
- For visitor-owned provider keys, use the website's session-scoped BYOK flow; for any shared provider key, keep it only in server-side environment variables or platform secrets.
- URL fetching must reject private/local network destinations and must not bypass login, paywalls, CAPTCHA, or other access controls.
- Imported story content should not be logged unnecessarily.

## Current limitations

The repository is an active implementation, not yet a finished public service. See [Known Limitations](docs/KNOWN_LIMITATIONS.md) and [Feature Roadmap](docs/FEATURE_ROADMAP.md) for what remains.
