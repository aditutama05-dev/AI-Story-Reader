# Project Context — AI Story Reader

## Product identity

AI Story Reader is a personal **website** for turning novels, light novels, web novels, digital books, manga, manhwa, manhua, and comics into detailed Indonesian narration that can be read and listened to in a browser.

The target deliverable is a website. A native Android application, desktop application, Android Accessibility Service, floating overlay, and background screen-capture service are not part of this product's target architecture.

## Product principles

1. Preserve the source's events, order, dialogue meaning, emotions, atmosphere, actions, and conflict development.
2. Do not replace detailed narration with a summary.
3. Do not invent events, dialogue, character identities, motivations, or missing source material.
4. Treat source text/images as the authority. Continuity notes are auxiliary context only.
5. Keep Series, Arc, Volume, and Chapter/part as distinct data concepts.
6. One submitted chapter URL represents one chapter or one standalone story part, not an entire volume.
7. A chapter may consist of multiple source pages; join only pages that are demonstrably part of that same chapter and preserve their order.
8. Deliver chapter-level audio as one complete file when audio export is implemented.
9. Prioritize accessible browser interaction, including TalkBack and other screen readers.
10. Prefer free/open-source components and services already available to the project owner. Keep secrets out of frontend code and Git.

## Visual direction

- Dark mode.
- Navy-blue surfaces and background.
- Bright blue accents.
- Minimal, professional visual language.
- No purple palette.
- Avoid generic AI-product visual tropes.

## Context carried forward from earlier project discussion

The earlier Android project/repository named `Livechat-Reading` was discussed as a reference point for concepts such as OCR, TTS, accessibility, screen capture, and floating reading. Those Android-specific mechanisms are **not** copied into AI Story Reader as native Android capabilities. AI Story Reader implements the relevant user-facing reading and accessibility behavior within normal browser capabilities.

## Source of truth

The repository is the durable project reference. Update the relevant documents whenever a decision changes or a feature is implemented. Keep desired features separate from implemented features and tested capabilities.

- Product requirements: `../FEATURES.md`
- Feature sequence: `FEATURE_ROADMAP.md`
- Browser accessibility and screen-access boundaries: `SCREEN_ACCESS_LIMITS.md`
- URL and file extraction: `SOURCE_INGESTION.md`
- Story hierarchy: `STORY_DATA_MODEL.md`
- Architecture: `TECHNICAL_ARCHITECTURE.md`
- Known gaps: `KNOWN_LIMITATIONS.md`
- Change history: `CHANGELOG.md`
