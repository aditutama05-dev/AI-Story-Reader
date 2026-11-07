# AI Story Reader

AI Story Reader is a web application for turning novels, light novels, web novels, manga, manhwa, and manhua into detailed Indonesian narration.

## Product goals

- Import a chapter from a URL, pasted text, or uploaded EPUB/TXT/PDF/DOCX file.
- Keep volume, chapter, interlude, ending, and epilogue as distinct content units.
- Narrate chronologically in natural Indonesian using the **MASTER FORM V2** approach: preserve events, actions, important dialogue (paraphrased), expressions, emotions, atmosphere, battles, and conflict development.
- Process long chapters in context-aware chunks without exposing artificial chunk boundaries in the final narration.
- Maintain story context such as characters, relationships, locations, terminology, current conditions, and unresolved conflicts.
- Provide playback controls, reading progress, text highlighting, adjustable speed, and downloadable chapter audio.
- Support configurable AI providers (OpenAI, OpenRouter, Gemini, and compatible custom endpoints) without exposing API keys in browser code or Git.

## Architecture

- **Backend:** Python + FastAPI.
- **Frontend:** lightweight responsive web application.
- **Storage:** SQLite for the initial single-instance deployment.
- **AI:** provider adapter layer; credentials are supplied at runtime through environment variables or the app's protected settings flow.
- **Deployment:** container-friendly; can be deployed to a managed application host.

## Security

Never commit API keys, passwords, tokens, uploaded books, or generated private media. Use environment variables/secrets for production credentials. The browser must never receive server-side provider secrets.

## Project status

Initial repository scaffold. Features will be implemented incrementally, with source extraction, narration, and provider configuration forming the first milestones.

## Development

The backend application will live in `backend/`. See `backend/requirements.txt` and `backend/app/main.py` as the implementation is added.
