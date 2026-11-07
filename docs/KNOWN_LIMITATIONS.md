# Known Limitations

This document describes the current repository state. It must be updated when a limitation is fixed or a new one is discovered.

## Frontend and deployment

- The frontend supports a configurable absolute API base URL for separate static hosting. The API service still needs to be deployed and connected before AI features work from GitHub Pages.
- GitHub Pages deployment has not yet been configured or verified.
- Automated checks cover the navy/bright-blue palette; manual mobile/desktop visual testing is still outstanding.
- The website has not yet undergone manual cross-device testing.
- The API supports a single shared `APP_ACCESS_TOKEN` and per-process in-memory rate limits. Production deployment must set a strong token; distributed quotas, per-user accounts, and persistent abuse monitoring are not implemented.

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
- Text-based PDF extraction reads the text layer; scanned PDF OCR is available through the separate vision-model action, limited to 30 pages per request.
- CBZ/ZIP comic archives are supported for image pages, up to 30 pages per request.
- Comic OCR is vision-model transcription, not geometric panel segmentation or dedicated character tracking.
- Image upload currently accepts up to 30 pages per request, each limited to 15 MB.

## Narration and continuity

- Narration uses context-aware chunks but does not yet run automated source-to-narration coverage verification.
- A local IndexedDB Series/Arc/Volume/Chapter library exists with JSON backup/restore. It is not cloud-synced; story parts have explicit type metadata for Chapter, Interlude, Ending, Epilogue, Prologue, Side Story, and custom labels.
- Manual continuity notes can be saved per chapter. Structured character/relationship/location/event tracking with source references remains unimplemented.
- AI output can still omit or distort source details; human review remains important.

## Audio

- Browser Web Speech API highlights the active word when the browser emits word-boundary events, with paragraph-level fallback.
- Full-chapter MP3 generation uses Edge TTS and requires outbound server connectivity to the TTS service.
- The HTML5 audio player supports native playback controls and ±15-second seek.
- Word-level synchronization for generated MP3 files and audio playback-position persistence remain unimplemented.
- Reading progress and bookmarks are stored locally in IndexedDB; they do not sync between devices or browsers.

## Accessibility

- Semantic structure, accessible labels, keyboard focus, display preferences, and basic browser TTS are present.
- Real Android TalkBack testing has not been completed.
- Speech voices and behavior depend on the user's browser and installed speech engine.
- The site does not provide Android Accessibility Service, floating overlay, or background screen capture; these are outside the website product boundary.
