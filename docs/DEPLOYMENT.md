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

Before the deployed site can import URLs/files or generate narration:

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

The Vercel Blueprint defaults to the Free web-service plan and does not require a shared application access token; public visitors can use their own provider API key. Do not add a shared provider key unless the owner deliberately chooses to pay for all visitors' usage. Free services can spin down after 15 minutes without traffic and may take about a minute to wake up; their filesystem is ephemeral and the service can restart. The story library, reading progress, and bookmarks therefore stay in browser IndexedDB on each user's device, not on the API container. This is the local-storage portion of the hybrid architecture; the API still needs a running backend host for URL extraction, OCR, and AI processing. Free compute is suitable for a low-traffic trial, not a latency-sensitive production service. See [Render's free-service limits](https://render.com/docs/free).

## Cloudflare Workers note

Cloudflare Workers does not run the current Python FastAPI application unchanged. If Workers is selected, implement and test an equivalent Worker API before pointing the GitHub Pages frontend at it. The current FastAPI backend can remain the local/reference implementation until endpoint parity is achieved.

## One-time owner actions (account access required)

These are the only steps that require the repository owner's own GitHub/Render account. No password, personal access token, or provider key should be sent in chat.

1. **Render API:** sign in to Render, choose New → Blueprint, connect the `aditutama05-dev/AI-Story-Reader` repository, review the detected `render.yaml`, and create the service using the **Free** plan. Confirm that no paid plan or paid add-on is selected. The blueprint intentionally does not require `APP_ACCESS_TOKEN` or a shared `AI_API_KEY`.
2. When Render finishes, copy the service's public `onrender.com` URL. In `frontend/config.js`, set `window.AI_STORY_READER_API_BASE` to that URL (without a trailing slash), then commit the change. The API CORS allowlist already includes the GitHub Pages origin.
3. Verify `https://<render-service>/api/health` returns JSON with `status: "ok"`, then test import, personal-key narration, comic OCR, and MP3 generation from the deployed website.

If the user does not want to create a Render account, the frontend can still be published on GitHub Pages, and local library features continue to work; server-backed features will remain offline. Render Free is a hobby/testing tier, not a production uptime guarantee.

## Release checklist

- [x] Pages deployment workflow is present and configured to publish the `frontend/` directory when the repository Pages source is set to GitHub Actions.
- [x] GitHub Pages deployment succeeds from the `frontend/` directory (latest completed successful run: `42470903901`; later run `42471292833` was in progress at last check).
- [ ] API is deployed and health check succeeds.
- [ ] API CORS permits only the required website origins.
- [ ] Public API base URL is configured.
- [ ] Provider secrets exist only in backend secret storage.
- [ ] Import, narration, OCR, and accessibility flows are manually checked.
