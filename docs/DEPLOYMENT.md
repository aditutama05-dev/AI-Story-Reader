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

A root `index.html` redirect is also included so the current `main` branch / root publishing mode can route visitors into `frontend/` while Pages is being switched to Actions.

The repository contains the `Deploy website to GitHub Pages` workflow, which publishes `frontend/` when run. The repository configuration and most recent run should still be checked in GitHub Actions/Settings before treating the live URL as verified. The repository slug remains `AI-Story-Reader` to preserve this URL, while the visible product brand is Novelith AI.

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

The Render Blueprint defaults to the Free web-service plan to avoid a required monthly compute charge. Free services can spin down after 15 minutes without traffic and may take about a minute to wake up; their filesystem is ephemeral and the service can restart. The story library, reading progress, and bookmarks therefore stay in browser IndexedDB on each user's device, not on the API container. This is the local-storage portion of the hybrid architecture; the API still needs a running backend host for URL extraction, OCR, and AI processing. Free compute is suitable for a low-traffic trial, not a latency-sensitive production service. See [Render's free-service limits](https://render.com/docs/free).

## Cloudflare Workers note

Cloudflare Workers does not run the current Python FastAPI application unchanged. If Workers is selected, implement and test an equivalent Worker API before pointing the GitHub Pages frontend at it. The current FastAPI backend can remain the local/reference implementation until endpoint parity is achieved.

## Release checklist

- [x] Pages deployment workflow is present and configured to publish the `frontend/` directory when the repository Pages source is set to GitHub Actions.
- [ ] Confirm the repository Settings → Pages source is set to GitHub Actions and verify the latest deployment run in Actions.
- [ ] API is deployed and health check succeeds.
- [ ] API CORS permits only the required website origins.
- [ ] Public API base URL is configured.
- [ ] Provider secrets exist only in backend secret storage.
- [ ] Import, narration, OCR, and accessibility flows are manually checked.
