# Story Data Model

## Hierarchy

The logical library hierarchy is:

```text
Series
└── Arc (optional)
    └── Volume (optional)
        └── Story Part
            ├── Prologue
            ├── Chapter
            ├── Interlude
            ├── Ending
            └── Epilogue
```

Arc and Volume are separate entities. A story may have an Arc without known Volume metadata, a Volume without explicit Arc metadata, or incomplete source metadata. Do not fabricate missing hierarchy.

## Core entities

### Series
Represents the overall work/franchise title.

### Arc
A named narrative arc within a Series. It is not a Volume or Chapter.

### Volume
A published or source-defined volume. It may contain multiple story parts.

### Story Part
A single processable unit of source content. Examples include Prologue, Chapter 1, Interlude, Ending, and Epilogue. A Story Part is the unit used for source extraction, narration, and audio export.

### Source Segment
A page or segment that belongs to one Story Part. A chapter split across several website pages has several ordered Source Segments but remains one Story Part.

### Original Content
The extracted original text or ordered image/OCR transcription. Keep it separate from translated/narrated output.

### Indonesian Narration
The generated detailed Indonesian retelling. It must remain linked to its original source and extraction version.

### Audio Asset
A generated audio file associated with exactly one Story Part. Target export format: MP3, one complete file per part.

### Continuity Note
Internal structured context about characters, relationships, locations, prior events, terms, and active conflicts. Each note should retain provenance when possible. It is auxiliary and cannot override original content.

## Identity and mapping rules

- One submitted URL maps to one Story Part candidate.
- The system may detect that the URL is one segment of a multi-page Story Part, but it must not silently expand the import into an entire Volume.
- A Story Part can have one or more Source Segments.
- Source segment order must be explicit and stable.
- Original content, narration, and audio must not overwrite one another.
- Interlude, Ending, and Epilogue each have their own text, narration, reading progress, bookmarks, and audio asset.

## Metadata uncertainty

Store unknown fields as unknown/null rather than inventing values. Distinguish user-confirmed metadata from automatically detected metadata and retain the source evidence used for detection.

## Continuity context implementation

The browser can assemble manually entered notes from up to the 12 most recent preceding story parts in the same series, plus notes on the active part. The combined context is capped at 12,000 characters and sent as secondary reference. It is not an automatically extracted fact database and does not replace source content.

## Structured continuity facts

Each chapter may store up to 100 user-curated facts with category (`character`, `relationship`, `location`, `term`, `event`, `conflict`), a concise fact statement, and a supporting source excerpt. Each statement and excerpt is limited to 500 characters. Facts from preceding parts in the same series are assembled with part titles and sent as secondary narration context, capped at 12,000 characters. This is not automatic extraction or evidence verification; the active chapter source remains authoritative.

### AI-proposed continuity facts

AI suggestions use the same per-chapter `continuityFacts` structure as manually entered facts. The extraction endpoint returns only suggestions with a verbatim source excerpt match (whitespace-normalized); rejected suggestions are counted. The browser displays all accepted suggestions and asks for user approval before merging them into the chapter. Existing facts are preserved and exact category/fact/excerpt duplicates are not re-added. The AI output is still a proposal, not verified canon.

### Source evidence offsets

AI-proposed continuity facts now retain zero-based `sourceStart` and exclusive `sourceEnd` character offsets into the exact source text submitted for extraction, alongside the excerpt. The backend locates a whitespace-tolerant, case-insensitive token sequence and returns offsets in the original unmodified text. Contradiction candidates carry the same offsets for their current-chapter excerpt. The browser can select and highlight the exact excerpt in the source editor. Multi-page URL imports and scanned-PDF OCR also return per-page source character ranges, allowing the browser to select the corresponding page transcription. These ranges identify extracted text, not original visual coordinates. Offsets are tied to that specific source-text version; editing or replacing the source can make previously stored offsets stale and requires re-extraction/review.
