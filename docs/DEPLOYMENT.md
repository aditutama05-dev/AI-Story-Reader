# Website Deployment

## Target

- Static website: GitHub Pages, published from the `frontend/` directory by GitHub Actions.
- API: a separate service. The current Python FastAPI backend is not executed by GitHub Pages.
- Public frontend API configuration: `frontend/config.js`.

## GitHub Pages setup

1. Open the repository Settings.
2. Open Pages.
3. Under Build and deployment, select **GitHub Actions** as the source.
4. Push a change to `frontend/` on `main`, or run the **Deploy website to GitHub Pages** workflow manually from Actions.
5. After a successful deployment, GitHub displays the website URL. For this repository, the expected default URL is `https://aditutama05-dev.github.io/AI-Story-Reader/`.

The workflow is committed, but GitHub Pages must be enabled in repository settings by an account owner with the required permission. A repository code commit cannot itself guarantee that the account-level Pages setting is enabled.

## API connection

GitHub Pages only serves static assets. It does not run Python, FastAPI, or provider API calls.

Before the deployed site can import URLs/files or generate narration:

1. Deploy the API to a supported backend host.
2. Configure provider keys as server-side secrets.
3. Configure API CORS to allow the GitHub Pages origin.
4. Set `window.AI_STORY_READER_API_BASE` in `frontend/config.js` to the API origin (for example, `https://api.example.com`).
5. Verify `GET /api/health`, URL import, file import, comic OCR, and narration against the deployed API.

Never place AI provider keys in `frontend/config.js`. The API base URL is public; provider credentials are not.

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
