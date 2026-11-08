# Story Narration Standard — MASTER FORM V2

## Purpose

Produce a detailed, natural Indonesian retelling of the supplied story content. The output should feel like continuous storytelling, not a short synopsis, review, analysis essay, or bullet-point summary.

## Required behavior

- Preserve the source's chronological order.
- Retain all meaningful events and actions.
- Preserve important dialogue by conveying its meaning naturally in Indonesian; dialogue may be paraphrased but must not change intent.
- Retain character reactions, expressions, emotions, hesitation, tone, and interpersonal dynamics when supported by the source.
- Preserve atmosphere, setting details, tension, battles, movement, and conflict progression.
- Keep names, titles, terminology, relationships, and point-of-view consistent.
- Preserve cause-and-effect links and transitions between events.
- Retell the complete supplied chapter/story part, not just its most important moments.
- For long input, internal chunking is allowed, but the final result must read as one continuous chapter.

## Prohibited behavior

- Do not invent scenes, actions, dialogue, motivations, thoughts, character identities, or outcomes.
- Do not omit meaningful events merely to shorten the output.
- Do not turn the main output into a summary.
- Do not reorder events for dramatic effect.
- Do not add analysis, review, speculation, or commentary as if it were part of the story.
- Do not create artificial headings such as “Bagian 1”, “Bagian 2”, or “Ringkasan” inside the narration.
- Do not use continuity notes as evidence when the source does not support the detail.

## Source fidelity and uncertainty

- The original source remains authoritative.
- If source text is missing, corrupted, unreadable, or ambiguous, do not silently fill the gap.
- For OCR, preserve the original readable text and mark unreadable portions for review.
- When a visual inference is uncertain, use cautious wording and do not present it as a confirmed event.
- Source extraction warnings must remain visible to the user before or alongside narration.

## Long-chapter processing

- Chunk boundaries are implementation details and must not appear as artificial story divisions.
- Pass a concise prior-narration context between chunks to reduce repetition and preserve continuity.
- Do not repeat the previous chunk's final event when continuing.
- Verify that every source chunk was processed and that output exists for each chunk.
- Preserve the original chunk sequence when assembling the final narration.

## Original text and Indonesian narration

Store original source content and generated Indonesian narration separately. Users should be able to review the source text and the generated retelling without one replacing the other.

## Acceptance criteria

A narration increment is acceptable only when tests and review demonstrate that it:
1. preserves source order;
2. does not invent events;
3. retains meaningful dialogue and reactions;
4. does not collapse the chapter into a summary;
5. joins internal chunks into continuous prose;
6. reports source gaps rather than pretending the input is complete.

## Comic OCR structural markers

When OCR source text contains markers such as [Halaman n], [Panel n], [Dialog n], [Pikiran n], [Caption n], or [SFX n], use them only to understand page/panel sequence and the kind of visible text. Do not read the labels aloud or narrate them as story events. Retell the visible dialogue, thoughts, captions, and sound effects naturally, while preserving their order. Do not invent speaker identities or visual actions that are not supported by the extracted source. The original page images remain necessary for reviewing OCR omissions and visual context.
