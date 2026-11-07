# Changelog

Notable repository changes are recorded here. For exact commit history, use GitHub commits.

## 2026-11-07

- Added AI-assisted continuity contradiction checks against structured facts from preceding parts. Candidate findings require a valid prior-fact index and a verbatim current-source excerpt; results are review-only and never modify saved facts.

- Added AI-assisted extraction of structured continuity facts from a selected chapter, with source-excerpt matching, duplicate-aware merge, and mandatory user review before saving.

- Added manually curated structured continuity facts by category (character, relationship, location, term, event, conflict), paired with source excerpts and included in later narration as secondary context.

- Added prior-chapter continuity context: manually maintained notes from earlier parts in the same series are sent with narration requests as secondary reference, capped at 12,000 characters. Current source text remains authoritative.

- Narration verification now flags empty chunks, unusually compressed outputs, and exact duplicate narration between source chunks. The report remains review-required and does not claim semantic completeness.

- Separated reading position, bookmarks, and generated MP3 playback position by library chapter so opening another chapter no longer overwrites the previous chapter's progress.

- Added `FEATURES.md` with the product feature specification gathered from prior brainstorming.
- Added project context, roadmap, accessibility/screen-access boundaries, source ingestion, story data model, architecture, known limitations, and changelog documentation.
- Refined product boundary: AI Story Reader is a website; Android-native screen capture/accessibility services are not part of the deliverable.
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
