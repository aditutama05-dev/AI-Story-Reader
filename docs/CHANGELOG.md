# Changelog

## 2026-11-08 — Novelith AI

- Clarified that GitHub Pages can publish the static frontend independently from the API; server-backed features require a separately deployed API and configured public API origin.
- Simplified the Render Free blueprint for the default bring-your-own-provider-key model by removing the optional shared application access-token prompt. No shared provider key is required; public visitors provide their own key.
- Added explicit one-time owner steps for enabling GitHub Pages and creating the Render Blueprint, without asking the owner to share passwords, tokens, or API keys in chat.

- Renamed the website-facing brand to **Novelith AI**; `AI` is rendered as a smaller suffix in the header wordmark. The repository slug remains unchanged to preserve existing GitHub Pages links.
- Added optional per-user provider API keys. The browser stores a key in session storage for the current session and sends it to the backend in `X-Provider-API-Key`; the backend uses request-scoped context and does not persist the key.
- Documented the hybrid model: GitHub Pages for the free static website, backend service for import/OCR/AI, and IndexedDB for each visitor's local library/progress.

Notable repository changes are recorded here. For exact commit history, use GitHub commits.

## 2026-11-08

- Structured comic OCR as ordered panels and text blocks (dialogue, thought, caption, SFX, other), with per-panel balloon numbering and page/panel/text-block source offsets. Invalid provider JSON falls back to editable plain text and remains review-required.
- Added accessible source-map controls to select a whole comic page, panel, or individual text block, plus a collapsible OCR warning list.
- Verify actual uploaded image format with Pillow rather than trusting the client Content-Type; accept JPG/JPEG, PNG, WEBP, and generic binary headers only when the decoded image signature is supported. Retained upload, page-count, pixel-count, and archive limits.
- Updated MASTER FORM V2 to treat comic page/panel/dialogue/caption/SFX labels as structural metadata, not spoken story content.
- Added regression tests for panel and balloon ordering, OCR fallback, source offsets, endpoint integration, image MIME mismatches, supported image formats, and narration marker handling.

## 2026-11-07

- Added source-evidence character offsets for AI-extracted continuity facts and contradiction findings, plus accessible controls to select the exact quoted excerpt in the source editor.

- Added AI-assisted continuity contradiction checks against structured facts from preceding parts. Candidate findings require a valid prior-fact index and a verbatim current-source excerpt; results are review-only and never modify saved facts.

- Added AI-assisted extraction of structured continuity facts from a selected chapter, with source-excerpt matching, duplicate-aware merge, and mandatory user review before saving.

- Added manually curated structured continuity facts by category (character, relationship, location, term, event, conflict), paired with source excerpts and included in later narration as secondary context.

- Added prior-chapter continuity context: manually maintained notes from earlier parts in the same series are sent with narration requests as secondary reference, capped at 12,000 characters. Current source text remains authoritative.

- Narration verification now flags empty chunks, unusually compressed outputs, and exact duplicate narration between source chunks. The report remains review-required and does not claim semantic completeness.

- Separated reading position, bookmarks, and generated MP3 playback position by library chapter so opening another chapter no longer overwrites the previous chapter's progress.

- Added `FEATURES.md` with the product feature specification gathered from prior brainstorming.
- Added project context, roadmap, accessibility/screen-access boundaries, source ingestion, story data model, architecture, known limitations, and changelog documentation.
- Refined product boundary: Novelith AI is a website; Android-native screen capture/accessibility services are not part of the deliverable.
- Aligned the website visual direction to dark navy and bright blue, with no purple palette.

- Added a GitHub Pages deployment workflow and deployment guide; Pages must be enabled in repository settings.
- Added a public API base URL configuration file for static hosting; no provider credentials are stored in it.
- Updated the frontend to the navy/bright-blue palette and documented the website's screen-access boundaries.
- Added the MASTER FORM V2 narration standard.

- Improved generic HTML extraction to prefer semantic story containers, remove common navigation/ad elements, and return adapter, segment, paragraph, and verification metadata. URL imports default to review-required rather than claiming completeness.
- Added unit tests for article extraction, noise removal, and private/non-HTTP URL rejection.

- Added local reading-state persistence with IndexedDB: restore the latest narration after reload, auto-save reading position, set a bookmark, resume, and clear saved progress.

- The frontend now surfaces URL extraction warnings and review-required status instead of implying that a fetched page is a complete chapter.

- Added a modular source-adapter protocol and registry with a generic HTML fallback, allowing future domain-specific adapters to be added independently.
