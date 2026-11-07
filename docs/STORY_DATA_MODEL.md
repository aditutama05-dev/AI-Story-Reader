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
