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

The workflow is committed. GitHub Pages is not enabled yet: the deployment action was unable to create the Pages site because the connected GitHub integration does not have permission to change that repository setting. An owner must enable Pages and select GitHub Actions once in Settings. After that, run the workflow manually. The workflow is intentionally manual until Pages is enabled so it does not create failing deployments on every code push.

## API connection

GitHub Pages only serves static assets. It does not run Python, FastAPI, or provider API calls.

Before the deployed site can import URLs/files or generate narration:

1. Deploy the API to a supported backend host.
2. Configure provider keys as server-side secrets.
3. Set `APP_ACCESS_TOKEN` as a strong private secret on the API host. Enter the same token in the website's API access field for each browser session. Do not put it in `frontend/config.js`.
4. Configure API CORS to allow the GitHub Pages origin.
5. Set `window.AI_STORY_READER_API_BASE` in `frontend/config.js` to the API origin (for example, `https://api.example.com`).
6. Verify `GET /api/health`, URL import, file import, comic OCR, and narration against the deployed API.

Never place AI provider keys in `frontend/config.js`. The API base URL is public; provider credentials are not.

The Render Blueprint defaults to the Free web-service plan to avoid a required monthly compute charge. Free services can spin down after 15 minutes without traffic and may take about a minute to wake up; their filesystem is ephemeral and the service can restart. The story library therefore stays in browser IndexedDB, not on the API container. Free compute is suitable for a low-traffic trial, not a latency-sensitive production service. See [Render's free-service limits](https://render.com/docs/free).

## Cloudflare Workers note

Cloudflare Workers does not run the current Python FastAPI application unchanged. If Workers is selected, implement and test an equivalent Worker API before pointing the GitHub Pages frontend at it. The current FastAPI backend can remain the local/reference implementation until endpoint parity is achieved.

## Release checklist

- [ ] Pages setting uses GitHub Actions.
- [ ] Pages deployment workflow succeeds.
- [ ] API is deployed and health check succeeds.
- [ ] API CORS permits only the required website origins.
- [ ] Public API base URL is configured.
- [ ] Provider secrets exist only in backend secret storage.
- [ ] Import, narration, OCR, and accessibility flows are manually checked.
