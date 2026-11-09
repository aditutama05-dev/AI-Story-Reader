# Known Limitations

This document describes the current repository state. It must be updated when a limitation is fixed or a new one is discovered.

## Frontend and deployment

- The frontend supports a configurable absolute API base URL for separate static hosting. Vercel FastAPI deployment files are prepared, but the API service still needs owner-side import, a successful build/health check, and connection before server-backed features work from GitHub Pages.
- GitHub Pages deployment has not yet been configured or verified.
- The editor now displays live source/narration character and word counts and warns when source text exceeds the narration API limit. Automated checks cover the navy/bright-blue palette; manual mobile/desktop visual testing is still outstanding.
- The website has not yet undergone manual cross-device testing. The latest GitHub Pages deployment workflow is verified successful; this does not replace real-device UI testing.
- The API's default CORS allowlist is the GitHub Pages origin (additional origins require explicit `CORS_ORIGINS` configuration). The API supports an optional shared `APP_ACCESS_TOKEN` and per-process in-memory rate limits. Public BYOK mode leaves the token unset; private deployments may configure a strong token. Distributed quotas, per-user accounts, and persistent abuse monitoring are not implemented.

## URL extraction

- Current extraction is a single-page HTTP fetch with a generic BeautifulSoup adapter; it reports basic metadata and defaults to `review_required`.
- JavaScript-rendered pages are not executed.
- Authenticated pages and pages protected by access controls are not supported.
- Redirects are rejected rather than followed through a validated redirect chain.
- A source adapter registry exists with a generic fallback; domain-specific adapters remain to be added.
- Explicit same-domain multi-page imports can be assembled in user-supplied order and are flagged for review; combined extracted text is capped at 20 million characters. Automatic continuation detection is not implemented.
- Generic HTML cleanup may still include unrelated text or omit content in unusual layouts.
- Domain-specific adapters and automatic verified continuation-page assembly are not implemented.
- DNS validation resolves hostnames before fetching, but the current implementation does not pin the resolved address to the HTTP connection; additional hardening against DNS rebinding is still required before broad public deployment.

## File and comic import

- EPUB extraction follows the package spine order. Complex fixed-layout EPUBs and unusual navigation structures may still need review. ZIP-based EPUB/DOCX inputs are guarded by entry-count, per-member, and total uncompressed-size limits.
- URL response bodies are streamed and capped at 8 MB before parsing. Text PDFs are limited to 500 pages and 20 million extracted characters; scanned-PDF OCR remains capped at 30 pages.
- Text-based PDF extraction reads the text layer; scanned PDF OCR is available through the separate vision-model action, limited to 30 pages per request.
- CBZ/ZIP comic archives are supported for image pages, up to 30 pages per request.
- Comic OCR now requests structured model-proposed panel order and dialogue/thought/caption/SFX blocks, with balloon sequence and page/panel/item text offsets. The order is not independently checked against image geometry; dedicated character tracking and visual-event narration remain unimplemented.
- Image upload currently accepts up to 30 pages per request, each limited to 15 MB, with a 100 MB aggregate limit and a 40-megapixel per-image decode limit.
- Scanned PDF OCR rejects excessive page dimensions and caps total rendered pixel workload before rasterization.

## Narration and continuity

- Narration uses context-aware chunks and flags empty, unusually compressed, or exactly duplicated chunk outputs. These structural checks cannot detect paraphrased omissions, altered event order, or semantic inaccuracies; full source-to-narration coverage verification is not implemented.
- A local IndexedDB Series/Arc/Volume/Chapter library exists with JSON backup/restore. It is not cloud-synced; story parts have explicit type metadata for Chapter, Interlude, Ending, Epilogue, Prologue, Side Story, and custom labels.
- Manual notes and structured facts (character, relationship, location, term, event, conflict) can be stored per chapter with source excerpts. AI-assisted extraction checks that proposed excerpts match the current source and requires user approval before saving; this validates quote matching, not the model's interpretation or completeness. AI-assisted contradiction checks are review-only and validate the quoted current-source excerpt and prior-fact index, but do not prove semantic contradiction. AI-proposed facts store character offsets; manually curated legacy facts may not. Page/panel/item evidence mapping exists for multi-page URL, scanned-PDF, and comic OCR imports, but not ordinary text imports. The frontend clears imported page/panel mappings and visible continuity evidence when the source editor changes or a different saved chapter is opened. Re-import unchanged source to restore page-level selection; saved facts still require review after source edits.
- AI output can still omit or distort source details; human review remains important. Gemini credentials are sent in the `x-goog-api-key` header rather than URL query strings; the visitor key remains transient request-scoped data and is not persisted by the API.

## Audio

- Browser Web Speech API highlights the active word when the browser emits word-boundary events, with paragraph-level fallback.
- Full-chapter MP3 generation uses Edge TTS and requires outbound server connectivity to the TTS service.
- The HTML5 audio player supports native playback controls and ±15-second seek.
- Word-level synchronization for generated MP3 files remains unimplemented. Playback position, reading position, and bookmarks are stored independently per library chapter in the same browser. Non-library imports use a separate temporary current-reading record. Progress does not sync between devices or browsers.
- Reading progress and bookmarks are stored locally in IndexedDB; they do not sync between devices or browsers.

## Accessibility

- Semantic structure, accessible labels, keyboard focus, display preferences, and basic browser TTS are present.
- Real Android TalkBack testing has not been completed.
- Speech voices and behavior depend on the user's browser and installed speech engine.
- The site does not provide Android Accessibility Service, floating overlay, or background screen capture; these are outside the website product boundary.


## Continuity context

Manual notes from preceding parts in the same series can be supplied to the narration model as secondary continuity context (up to 12,000 characters). Notes are not extracted or verified automatically, and they must never override the current chapter source. Structured character/relationship/location/term/event/conflict records and source excerpts are supported; evidence offsets exist for AI-proposed facts, with limitations described above. Browser-local notes do not sync across devices.


Structured continuity facts are assembled from preceding story parts in the same series and sent as secondary context. They remain user-curated hints, not authoritative canon: the active chapter source always takes priority. The UI limits each fact and excerpt to 500 characters and each chapter to 100 facts; the combined continuity context is capped at 12,000 characters.


### AI-assisted continuity fact extraction

The user can request up to 30 AI-proposed facts from the active chapter. The backend rejects suggestions whose quoted excerpt cannot be matched against the source text (after whitespace normalization), and the UI requires explicit user confirmation before saving. This verifies the excerpt text only, not whether the model's fact interpretation is correct or whether it omitted relevant facts. The feature requires a configured AI provider and the active chapter must be opened from the local library.

### AI-assisted continuity contradiction checks

The user can compare the active chapter against up to 240 structured facts from preceding parts in the same series. The API accepts a candidate only when its prior-fact index is valid and its quoted current-chapter excerpt matches the source after whitespace normalization. Results are suggestions only: the model can misinterpret context, and the feature does not prove semantic contradiction, detect every inconsistency, or modify saved facts. It requires an active library chapter and a configured AI provider.

### Source evidence offsets

Offsets are zero-based character positions into the exact text submitted to the API, not stable identifiers across edits or re-imports. The current locator matches token sequences case-insensitively and tolerates whitespace differences; ambiguous repeated excerpts resolve to the first occurrence. Page-level mapping is available for explicit multi-page URL, scanned-PDF, and comic OCR imports, but not ordinary text imports; older/manual facts may lack offsets.
