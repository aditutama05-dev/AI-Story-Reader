# Known Limitations

This document describes the current repository state. It must be updated when a limitation is fixed or a new one is discovered.

## Frontend and deployment

- The frontend supports a configurable absolute API base URL for separate static hosting. The API service still needs to be deployed and connected before AI features work from GitHub Pages.
- GitHub Pages deployment has not yet been configured or verified.
- Automated checks cover the navy/bright-blue palette; manual mobile/desktop visual testing is still outstanding.
- The website has not yet undergone manual cross-device testing.

## URL extraction

- Current extraction is a single-page HTTP fetch with a generic BeautifulSoup adapter; it reports basic metadata and defaults to `review_required`.
- JavaScript-rendered pages are not executed.
- Authenticated pages and pages protected by access controls are not supported.
- Redirects are rejected rather than followed through a validated redirect chain.
- A source adapter registry exists with a generic fallback; domain-specific adapters remain to be added.
- Explicit same-domain multi-page imports can be assembled in user-supplied order and are flagged for review. Automatic continuation detection is not implemented.
- Generic HTML cleanup may still include unrelated text or omit content in unusual layouts.
- Domain-specific adapters and automatic verified continuation-page assembly are not implemented.
- DNS validation resolves hostnames before fetching, but the current implementation does not pin the resolved address to the HTTP connection; additional hardening against DNS rebinding is still required before broad public deployment.

## File and comic import

- EPUB extraction follows the package spine order. Complex fixed-layout EPUBs and unusual navigation structures may still need review.
- PDF extraction reads the text layer only; scanned PDFs require OCR, which is not implemented.
- CBZ/ZIP comic archives are supported for image pages, up to 30 pages per request.
- Comic OCR is vision-model transcription, not geometric panel segmentation or dedicated character tracking.
- Image upload currently accepts up to 30 pages per request, each limited to 15 MB.

## Narration and continuity

- Narration uses context-aware chunks but does not yet run automated source-to-narration coverage verification.
- A local IndexedDB Series/Arc/Volume/Chapter library exists with JSON backup/restore. It is not cloud-synced, and part types are represented by user-entered chapter titles.
- Manual continuity notes can be saved per chapter. Structured character/relationship/location/event tracking with source references remains unimplemented.
- AI output can still omit or distort source details; human review remains important.

## Audio

- Current playback uses browser Web Speech API.
- There is no server-generated MP3 download.
- There is no synchronized word highlighting.
- There is no ±15-second audio seek because current browser TTS is not exposed as a stable seekable audio file.
- Reading progress and a single bookmark are stored locally in the current browser using IndexedDB. They do not sync between devices or browsers. Audio playback position is not yet persisted because generated audio is not implemented.

## Accessibility

- Semantic structure, accessible labels, keyboard focus, display preferences, and basic browser TTS are present.
- Real Android TalkBack testing has not been completed.
- Speech voices and behavior depend on the user's browser and installed speech engine.
- The site does not provide Android Accessibility Service, floating overlay, or background screen capture; these are outside the website product boundary.
