# Feature Roadmap

This roadmap separates the desired product from what is currently implemented. Priorities may be reordered as technical findings emerge.

## Stage 0 — Foundation and documentation

- [x] Repository and initial web/backend scaffold exist.
- [x] Record product requirements in `FEATURES.md`.
- [x] Record project context, story model, source ingestion, architecture, accessibility boundaries, and known limitations.
- [x] Add a GitHub Pages deployment workflow for the static website; successful public deployment is verified.
- [ ] Provide a production API endpoint suitable for a static frontend (Vercel FastAPI deployment scaffold added; owner import and live verification remain).

## Stage 1 — Website foundation

- [x] Responsive browser interface.
- [x] Navy/blue visual theme.
- [x] Semantic landmarks, labels, keyboard focus, and accessibility preferences.
- [x] Add persistent configuration point for the public API base URL (never an API secret).
- [ ] Verify the site at mobile and desktop viewport sizes.
- [x] Publish the static website through GitHub Pages (Actions deployment succeeded for commit `45af27c5acf1a1e8f132988ce5ec37637d914ea8`; server-backed features remain unavailable until the API URL is configured).

## Stage 2 — Source import and URL recognition

- [x] Basic single-page HTML URL extraction in the current FastAPI backend.
- [x] TXT, Markdown, HTML, PDF text layer, DOCX, and EPUB import in the current FastAPI backend.
- [x] Multi-image OCR request for JPG/JPEG, PNG, and WEBP pages.
- [x] Source URL validation and structured source metadata (basic generic adapter report).
- [x] Generic HTML article extraction with extraction diagnostics.
- [x] Modular source adapter interface and registry (generic fallback is active; domain-specific adapters remain planned).
- [x] User-specified same-domain multi-page chapter assembly in explicit URL order with review warnings.
- [ ] Automatic same-chapter continuation detection without following next-chapter links.
- [x] Source completeness report with explicit uncertainty warnings for single-page and manually assembled imports.
- [x] CBZ/ZIP comic archive ingestion with natural page sorting and decompression limits.
- [x] Scanned PDF rendering and OCR through a vision model, with a 30-page limit and review warnings.

## Stage 3 — Story library and continuity

- [x] Local browser library for Series / Arc / Volume / Chapter hierarchy, with chapter creation, editing, deletion, and JSON backup/restore. (Local to one browser; cloud sync remains planned.)
- [x] Explicit story-part type field for Chapter, Interlude, Ending, Epilogue, Prologue, Side Story, and custom part labels.
- [ ] One source URL maps to one story part unless the source explicitly proves otherwise.
- [x] Store original source text separately from Indonesian narration in the local story library.
- [x] Manual continuity notes stored per chapter and kept separate from source text/narration.
- [x] Automatically include notes from preceding parts in the same series as secondary context for narration, with source text taking priority.
- [x] Manually curated structured continuity facts for characters, relationships, locations, terms, events, and conflicts, each paired with a source excerpt.
- [x] AI-assisted fact extraction with verbatim source-excerpt matching, user review, and explicit approval before saving.
- [x] AI-assisted detection of possible contradictions against prior structured facts, with exact current-source quote matching and review-only results; character-offset evidence linking, source-editor highlighting, imported page-to-source offset mapping for multi-page URLs, scanned PDFs, and comic/manga OCR are implemented. Stale imported mappings are cleared when source text changes or another saved chapter is opened.
- [ ] Continuity notes never replace or override source evidence.

## Stage 4 — Narration and verification

- [x] Initial context-aware chunked narration endpoint.
- [x] MASTER FORM V2 prompt strengthened for complete chronological narration, dialogue fidelity, detail preservation, and no invention, with regression tests.
- [x] Per-chunk output-length sanity report flags empty or unusually compressed narration and requires human review (not semantic proof).
- [x] Flag empty narration chunks and exact duplicate outputs across chunks in the verification report.
- [ ] Detection of missing, repeated, or reordered source sections.
- [ ] Explicit uncertainty reporting; never claim guaranteed completeness without evidence.
- [ ] Narration revision workflow that preserves the source.

## Stage 5 — Accessible reading and audiobook

- [x] Browser text narration region usable by screen readers.
- [x] Basic browser speech synthesis controls.
- [x] Adjustable browser speech rate and selectable device voice where available.
- [x] High contrast, text sizing, spacing, and reduced-motion preferences.
- [x] Persist the current narration and reading position in browser IndexedDB; restore it after reload.
- [x] Accessible bookmark, resume, and clear-progress controls.
- [x] Browser TTS highlights the active word when speech-boundary events are supported, with paragraph-level fallback and assistive-technology state.
- [x] HTML5 MP3 audio player with native playback controls and ±15-second seek.
- [x] Server-generated MP3 export as one complete file per story part (Edge TTS; server network access required).
- [ ] Word-level synchronization for generated MP3 audio.
- [ ] Verify audio completeness against the full narration text.
- [x] Persist and restore generated MP3 playback position independently for each library chapter when its audio is regenerated.
- [x] Keep reading position and bookmarks independently for each library chapter.

## Stage 6 — Comic understanding

- [x] Multi-page image transcription via vision model.
- [x] Reading direction options: RTL, LTR, and vertical.
- [x] CBZ/ZIP page extraction with natural filename ordering and archive size limits.
- [x] Structured model-proposed panel and text-block extraction (dialogue, thought, caption, SFX) with per-panel balloon sequence, page/panel/item source offsets, and a plain-text fallback when provider JSON is invalid; all results require human review.
- [ ] Independent panel segmentation and reading-order validation against original image geometry.
- [ ] Character identity tracking grounded in visual evidence.
- [x] Model-proposed association of dialogue, thought, caption, and SFX text blocks with their ordered panels and optional balloon sequence; speaker identity is not guessed.
- [ ] Visual event narration without unsupported assumptions.
- [x] Comic OCR source text can be sent through MASTER FORM V2; page/panel/dialogue/caption/SFX markers are treated as structural metadata, not spoken story text.
- [ ] Full-chapter comic narration with persistent page/panel traceability in the generated narration.

## Stage 7 — Release readiness

- [x] Deploy frontend to GitHub Pages (Actions run `42470842578` completed successfully on 2026-11-08).
- [ ] Deploy API to Vercel Hobby (FastAPI entrypoint and configuration added; live deployment and health check remain).
- [ ] Configure runtime secrets outside the repository.
- [x] Add per-client in-memory rate limits to expensive/import API routes.
- [ ] Add distributed rate limiting, authentication, request quotas, and production abuse protection.
- [ ] Add privacy/data-retention controls for imported source content and generated audio.
- [ ] Run automated tests and manual TalkBack testing on real Android devices.
- [ ] Document deployment, backup, and recovery procedures.

## Current manga/manhwa OCR increment — 2026-11-08

- Implemented an accessible browser-side image queue with per-page thumbnails, manual move-up/move-down ordering, removal, and upload-size/page-count preflight checks.
- Individually uploaded images are submitted in the visible queue order. A CBZ/ZIP archive is handled as a single upload and its entries retain natural filename sorting; mixed archive-plus-image batches are rejected explicitly.
- Structured OCR text blocks now receive conservative NFC and whitespace normalization before source offsets are calculated. This does not translate or rewrite words, names, punctuation, or SFX.
- MASTER FORM V2 now explicitly requests natural Indonesian narration and faithful Indonesian rendering of non-Indonesian dialogue/OCR while preserving names, titles, special terms, numbers, and meaningful SFX.
- Regression tests were added for normalization, selected image order, page offsets, and mixed archive rejection. Run `pip install -r backend/requirements.txt` followed by `cd backend && python -m unittest discover -s tests` in a repository checkout; the current connector runtime could not clone GitHub because DNS resolution was unavailable.
- [ ] Verify the upload queue and reordering with keyboard navigation, Android TalkBack, and real mobile browsers; inspect actual OCR order against representative RTL manga, LTR manhua, and vertical manhwa pages.

## Recent API credential hardening — 2026-11-08

- Moved Gemini API keys from URL query parameters into the `x-goog-api-key` request header for text generation, scanned-PDF OCR, and comic OCR, reducing exposure in URL logs and diagnostics.
- Updated missing-key errors to explain both visitor-owned API keys and optional server-side configuration.
- Added a regression test asserting that Gemini credentials are sent in headers and never appear in the request URL.

## Hosting and copyright update — 2026-11-09\n\n- Added a Vercel Python/FastAPI deployment entrypoint and root dependency manifest as an alternative to Render, whose signup requested a payment card. This is a deployment scaffold only; a repository owner must import the project and confirm that the account can use the free Hobby plan without entering payment details.\n- Tightened the backend's default CORS allowlist to the project's GitHub Pages origin rather than `*`. Additional trusted origins can be explicitly configured with `CORS_ORIGINS`.\n- Added a repository-level `LICENSE` notice reserving all rights to `aditutama05-dev`; this is a proprietary all-rights-reserved notice, not an OSI-approved open-source license. Third-party component licenses remain separate.\n\n## Completion rule

A checkbox is marked complete only after the feature exists in the repository and its behavior has been tested. A design note or planned implementation is not evidence that a feature is complete.


## Recent frontend usability work

- [x] Live source and narration character/word counters, including a visible warning when source text exceeds the backend's 1,000,000-character narration input limit.
