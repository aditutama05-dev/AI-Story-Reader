# Website Deployment

## Target

- Static website: GitHub Pages, published from the `frontend/` directory by GitHub Actions.
- API: a separate service. The current Python FastAPI backend is not executed by GitHub Pages.
- Public frontend API configuration: `frontend/config.js`.

## GitHub Pages setup

1. Open the repository Settings.
2. Open Pages.
3. Under Build and deployment, select **GitHub Actions** as the source.
4. Run the **Deploy website to GitHub Pages** workflow manually from Actions.
5. After a successful deployment, GitHub displays the website URL. For this repository, the expected default URL is `https://aditutama05-dev.github.io/AI-Story-Reader/`.

A root `index.html` fallback is included only for legacy branch/root publishing. The Actions workflow uploads `frontend/` as the site root, so the normal Pages URL should open the frontend directly; it should not append `/frontend/` to the public URL.

Verified: the `Deploy website to GitHub Pages` workflow successfully published `frontend/` for commit `45af27c5acf1a1e8f132988ce5ec37637d914ea8` on 2026-11-08 (run `42470903901`). Future pushes to `main` trigger the workflow automatically. A later run for commit `bad38b126f8a0b5b6e61d4698b5b744af519ce62` is currently running after the latest documentation and credential-hardening changes. The repository slug remains `AI-Story-Reader` to preserve the existing URL, while the visible product brand is Novelith AI.

## API connection

GitHub Pages only serves static assets. It does not run Python, FastAPI, or provider API calls.

The deployed API is connected to the website. The owner verified `/api/health` in a browser and the scheduled smoke workflow checks live health, public configuration, and CORS. Provider-backed import, OCR, narration, and MP3 still need real-key functional testing. For a new deployment or recovery:

1. Deploy the API to a supported backend host.
2. Choose one AI access model:
   - **Bring your own key (default option):** each visitor enters their own provider key in the website. The browser keeps it in `sessionStorage` for the current tab session and sends it to the API in the `X-Provider-API-Key` HTTPS header. The backend uses it only for that request; provider charges go to that visitor's provider account. Do not use this on shared/public devices.
   - **Shared key (optional):** configure `AI_API_KEY` plus `AI_PROVIDER`, `AI_MODEL`, and `AI_BASE_URL` as server secrets. Visitors do not need provider accounts, but the site owner pays for all usage and must enforce strict quotas and spending controls.
   Provider keys are never placed in the repository or public frontend config.
3. For a public website, leave `APP_ACCESS_TOKEN` unset so visitors do not need a shared password. For a restricted private deployment, set a strong `APP_ACCESS_TOKEN`; share it only through a private channel. Never put it in `frontend/config.js` or publish it in the repository.
4. Configure API CORS to allow the GitHub Pages origin.
5. Set `window.AI_STORY_READER_API_BASE` in `frontend/config.js` to the API origin (for example, `https://api.example.com`).
6. Verify `GET /api/health`, URL import, file import, comic OCR, and narration against the deployed API.

Never place AI provider keys in `frontend/config.js`. The API base URL is public; provider credentials are not. Per-user keys are transient request credentials, not server-stored accounts. The browser's session storage is not a secure vault; users should use their own devices and rotate a key if they suspect exposure.

A shared provider key makes the owner responsible for API charges and abuse risk. The current in-memory per-IP rate limit is only a lightweight trial safeguard, not production-grade billing, account quotas, or bot protection. Before widely sharing the public site, add persistent/distributed rate limiting, provider budget alerts or hard spend caps, monitoring, and a way to disable AI quickly. Do not publish a shared `APP_ACCESS_TOKEN` as a substitute: anyone who obtains it can use the backend.

## Vercel API deployment (live health endpoint verified)

Render is no longer the recommended deployment path because its setup requested a payment card. The repository includes a Vercel Python entrypoint (`index.py`), root dependency file (`requirements.txt`), and `vercel.json` for the existing FastAPI application. The owner has now imported the repository and reports that the Vercel deployment reached **Ready**. The reported deployment origin is `https://ai-story-reader-beige.vercel.app`. The owner supplied a live browser screenshot of `/api/health` returning `{"status":"ok","service":"ai-story-reader-api","version":"0.2.0"}` on 2026-11-09. The frontend API base is configured, and a scheduled GitHub Actions smoke test now checks health, public configuration, and GitHub Pages CORS.

1. [x] Owner imported the repository into Vercel and confirmed deployment Ready.
2. [x] Live `/api/health` response confirmed by owner screenshot.
3. [x] `frontend/config.js` points to the Vercel API origin.
4. [x] A scheduled GitHub Actions smoke workflow checks `/api/health`, `/api/config`, and CORS every six hours; it can also be run manually.
5. [ ] Complete authenticated-provider smoke tests for URL/file import, narration, OCR, and MP3. These require a real provider key and must not place it in CI logs or repository secrets unless the owner explicitly configures protected secrets.

The Vercel project is already imported and active. No credentials or payment details should be shared in chat.

**Important upload limitation:** Vercel Functions cap both request and response bodies at 4.5 MB, regardless of the larger upload limits accepted by the FastAPI handlers. Therefore large PDFs, EPUBs, comic images/CBZ files, and large OCR/narration responses may fail with HTTP 413 on Vercel even though the application code accepts larger files. Keep Vercel as a lightweight API trial only; supporting large books and manga requires browser-direct uploads to object storage (with authenticated upload tokens) or a host that supports larger request bodies. Do not advertise 40–100 MB uploads as working on this Vercel deployment.

## Free local-first fallback

If no backend host can be used without a payment card, GitHub Pages can continue serving the website and the library/progress/bookmarks remain stored in each user's browser IndexedDB. This does **not** make the existing FastAPI endpoints run locally in the public website: URL extraction, AI narration, OCR, and MP3 export still require either a deployed API or a separately implemented browser-side version. Do not claim those server-backed functions are available in local-only mode until that browser implementation exists.

## Cloudflare Workers note

Cloudflare advertises a free Workers tier without a card, but the current backend is Python/FastAPI and cannot be deployed there unchanged. Selecting Workers would require a separately implemented JavaScript/TypeScript API and parity tests for each required endpoint. It is a future migration option, not a ready drop-in replacement.


## Release checklist

- [x] Pages deployment workflow is present and configured to publish the `frontend/` directory when the repository Pages source is set to GitHub Actions.
- [x] GitHub Pages deployment succeeds from the `frontend/` directory (latest completed successful run: `42470903901`; later run `42471292833` was in progress at last check).
- [x] Vercel project imported and deployment reported Ready by the owner.
- [x] Live API health check returns `{"status":"ok","service":"ai-story-reader-api","version":"0.2.0"}` (verified from owner's browser screenshot, 2026-11-09).
- [x] Backend default CORS allowlist is restricted to the GitHub Pages origin.
- [x] Public API base URL is configured in `frontend/config.js`.
- [ ] Provider secrets exist only in backend secret storage.
- [ ] Real-provider URL/file import, narration, OCR, and MP3 are manually checked with a user-owned API key.
- [ ] Android TalkBack and responsive mobile/desktop interaction are manually checked.
- [x] Scheduled live API health/config/CORS smoke workflow added.
