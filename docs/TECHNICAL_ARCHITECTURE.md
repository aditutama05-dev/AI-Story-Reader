# Technical Architecture

## Product shape

The deliverable is a browser website. The repository currently contains a static HTML/CSS/JavaScript frontend and a Python FastAPI backend. The intended low-cost deployment direction is a static frontend on GitHub Pages with a separately hosted API service. Cloudflare Workers is a candidate API runtime, but the current Python FastAPI backend cannot be deployed to Workers unchanged.

## Current repository implementation

- `frontend/index.html`: browser UI, import controls, image OCR form, narration request, accessibility preferences, and browser speech synthesis.
- `backend/app/main.py`: FastAPI endpoints for health, configuration, URL import, file import, comic OCR, and narration.
- `backend/app/importers.py`: document extraction, safe URL fetching, and structured extraction reports.
- `backend/app/source_adapters.py`: adapter protocol, registry, and generic HTML fallback; domain-specific adapters can be registered independently.
- `backend/app/vision_ocr.py`: image normalization and vision prompts.
- `backend/tests/`: OCR and frontend accessibility tests.
- `.github/workflows/backend-tests.yml`: automated Python tests, JavaScript syntax check, and Python compile check.

## Current API endpoints

- `GET /api/health`
- `GET /api/config`
- `POST /api/import/url`
- `POST /api/import/file`
- `POST /api/import/comic`
- `POST /api/narrate`

## Deployment target

- Frontend: GitHub Pages (static HTML/CSS/JS).
- API: a separately deployed backend endpoint. Cloudflare Workers may be used after implementing a compatible JavaScript/TypeScript API layer or adapter.
- AI providers: OpenRouter, OpenAI, Gemini, or compatible provider configured server-side.
- Secrets: runtime environment variables or platform secret storage only.
- Persistent story library/audio storage: choose only after comparing free-tier limits, data durability, privacy, and expected file sizes.

## Important compatibility notes

- GitHub Pages serves static files and does not execute Python/FastAPI.
- A static frontend must call an absolute configured API base URL when the API is on another host.
- The API must explicitly allow the deployed Pages origin through CORS.
- A Cloudflare Worker is not a drop-in host for FastAPI. Porting requires a Worker implementation and endpoint parity tests.
- Browser TTS is not server-generated MP3 output.
- Local browser storage is suitable for user preferences and lightweight reading progress, not a durable shared library or large audio archive.

## Security requirements

- Never expose the operator's shared provider API key to browser JavaScript.
- Optional visitor-owned provider keys may be entered in the browser, kept in session storage for the active session, and sent only over HTTPS in `X-Provider-API-Key` to AI endpoints. The backend reads them through request-scoped context and does not persist them. Browser session storage is not a secure vault.
- Validate all URL fetches against SSRF and redirect-based private-network access.
- Limit upload sizes, image dimensions, request durations, and AI input length.
- Do not log full private story text or credentials.
- Keep user-uploaded content and generated audio out of Git.
- Add rate limiting and abuse controls before public deployment.
