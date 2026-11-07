# Feature Roadmap

This roadmap separates the desired product from what is currently implemented. Priorities may be reordered as technical findings emerge.

## Stage 0 — Foundation and documentation

- [x] Repository and initial web/backend scaffold exist.
- [x] Record product requirements in `FEATURES.md`.
- [x] Record project context, story model, source ingestion, architecture, accessibility boundaries, and known limitations.
- [x] Add a GitHub Pages deployment workflow for the static website (repository Pages setting still needs enabling).
- [ ] Provide a production API endpoint suitable for a static frontend.

## Stage 1 — Website foundation

- [x] Responsive browser interface.
- [x] Navy/blue visual theme.
- [x] Semantic landmarks, labels, keyboard focus, and accessibility preferences.
- [x] Add persistent configuration point for the public API base URL (never an API secret).
- [ ] Verify the site at mobile and desktop viewport sizes.
- [ ] Publish through GitHub Pages after the API endpoint is ready.

## Stage 2 — Source import and URL recognition

- [x] Basic single-page HTML URL extraction in the current FastAPI backend.
- [x] TXT, Markdown, HTML, PDF text layer, DOCX, and EPUB import in the current FastAPI backend.
- [x] Multi-image OCR request for JPG, PNG, and WEBP pages.
- [x] Source URL validation and structured source metadata (basic generic adapter report).
- [x] Generic HTML article extraction with extraction diagnostics.
- [x] Modular source adapter interface and registry (generic fallback is active; domain-specific adapters remain planned).
- [ ] Detect same-chapter continuation pages without following unrelated links.
- [x] User-specified same-domain multi-page chapter assembly in explicit URL order with review warnings.\n- [ ] Automatic same-chapter continuation detection without following next-chapter links.
- [ ] Source completeness report with explicit uncertainty states.
- [x] CBZ/ZIP comic archive ingestion with natural page sorting and decompression limits.
- [ ] OCR for scanned PDF pages.

## Stage 3 — Story library and continuity

- [x] Local browser library for Series / Arc / Volume / Chapter hierarchy, with chapter creation, editing, deletion, and JSON backup/restore. (Local to one browser; cloud sync remains planned.)
- [ ] Explicit distinction between Arc, Volume, Chapter, Interlude, Ending, Epilogue, and other parts.
- [ ] One source URL maps to one story part unless the source explicitly proves otherwise.
- [x] Store original source text separately from Indonesian narration in the local story library.
- [ ] Continuity notes for characters, relationships, locations, events, terms, and active conflicts.
- [ ] Continuity notes never replace or override source evidence.

## Stage 4 — Narration and verification

- [x] Initial context-aware chunked narration endpoint.
- [ ] MASTER FORM V2 prompt and regression tests covering detailed chronological narration.
- [ ] Source-to-narration coverage checks.
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
- [x] Browser TTS highlights the active paragraph and exposes the active paragraph state to assistive technology. (Word-level synchronization remains planned.)
- [x] HTML5 MP3 audio player with native playback controls and ±15-second seek.
- [x] Server-generated MP3 export as one complete file per story part (Edge TTS; server network access required).
- [ ] Verify audio completeness against the full narration text.

## Stage 6 — Comic understanding

- [x] Multi-page image transcription via vision model.
- [x] Reading direction options: RTL, LTR, and vertical.
- [ ] CBZ/ZIP page extraction.
- [ ] Panel segmentation and reading-order validation.
- [ ] Character identity tracking grounded in visual evidence.
- [ ] Dialogue, caption, thought, and SFX association with panels.
- [ ] Visual event narration without unsupported assumptions.
- [ ] Full-chapter comic narration with page/panel traceability.

## Stage 7 — Release readiness

- [ ] Deploy frontend to GitHub Pages.
- [ ] Deploy API to the selected supported backend platform.
- [ ] Configure runtime secrets outside the repository.
- [x] Add per-client in-memory rate limits to expensive/import API routes.\n- [ ] Add distributed rate limiting, authentication, request quotas, and production abuse protection.
- [ ] Add privacy/data-retention controls for imported source content and generated audio.
- [ ] Run automated tests and manual TalkBack testing on real Android devices.
- [ ] Document deployment, backup, and recovery procedures.

## Completion rule

A checkbox is marked complete only after the feature exists in the repository and its behavior has been tested. A design note or planned implementation is not evidence that a feature is complete.
