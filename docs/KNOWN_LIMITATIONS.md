# Known Limitations

This document describes the current repository state. It must be updated when a limitation is fixed or a new one is discovered.

## Frontend and deployment

- The frontend currently uses relative `/api/...` requests and is primarily suited to being served by the FastAPI app. A configurable absolute API base URL is needed for GitHub Pages hosting.
- GitHub Pages deployment has not yet been configured or verified.
- The current visual theme is being aligned to the required navy/bright-blue palette.
- The website has not yet undergone manual cross-device testing.

## URL extraction

- Current extraction is a single-page HTTP fetch with a generic BeautifulSoup adapter; it reports basic metadata and defaults to `review_required`.
- JavaScript-rendered pages are not executed.
- Authenticated pages and pages protected by access controls are not supported.
- Redirects are rejected rather than followed through a validated redirect chain.
- There is no domain-specific source adapter registry yet.
- There is no reliable multi-page chapter continuation detection or completeness report.
- Generic HTML cleanup may still include unrelated text or omit content in unusual layouts.
- Domain-specific adapters and verified continuation-page assembly are not implemented.
- DNS validation resolves hostnames before fetching, but the current implementation does not pin the resolved address to the HTTP connection; additional hardening against DNS rebinding is still required before broad public deployment.

## File and comic import

- EPUB extraction currently sorts HTML-like archive paths rather than following the EPUB package spine; reading order may be incorrect for some books.
- PDF extraction reads the text layer only; scanned PDFs require OCR, which is not implemented.
- ZIP/CBZ import is not implemented.
- Comic OCR is vision-model transcription, not geometric panel segmentation or dedicated character tracking.
- Image upload currently accepts up to 30 pages per request, each limited to 15 MB.

## Narration and continuity

- Narration uses context-aware chunks but does not yet run automated source-to-narration coverage verification.
- There is no persistent Series/Arc/Volume/Story Part library.
- Story Continuity Memory is specified but not yet stored as a structured persistent model.
- AI output can still omit or distort source details; human review remains important.

## Audio

- Current playback uses browser Web Speech API.
- There is no server-generated MP3 download.
- There is no synchronized word highlighting.
- There is no ±15-second audio seek because current browser TTS is not exposed as a stable seekable audio file.
- Reading/audio bookmark and resume persistence are not complete.

## Accessibility

- Semantic structure, accessible labels, keyboard focus, display preferences, and basic browser TTS are present.
- Real Android TalkBack testing has not been completed.
- Speech voices and behavior depend on the user's browser and installed speech engine.
- The site does not provide Android Accessibility Service, floating overlay, or background screen capture; these are outside the website product boundary.
