# Source Ingestion: URL, Website Recognition, and Files

## Goal

Allow a user to provide one chapter/part URL or upload a supported file, then extract the content while preserving source order and reporting uncertainty.

## URL processing pipeline

1. **Input validation** — accept only HTTP or HTTPS URLs; reject credentials and private/local network destinations.
2. **Domain recognition** — normalize hostname and record the canonical URL.
3. **Adapter selection** — use a domain-specific adapter when one is implemented; otherwise try the generic HTML adapter.
4. **Fetch** — retrieve only the submitted URL and explicitly verified continuation pages.
5. **Content extraction** — identify title, main content, paragraph boundaries, and page metadata.
6. **Noise filtering** — remove menus, advertisements, scripts, comments, recommendations, and unrelated navigation without dropping story paragraphs.
7. **Continuation analysis** — follow only links or page markers that can be confidently identified as another segment of the same chapter.
8. **Ordering** — retain source page order and paragraph order.
9. **Verification** — report what was extracted, page count, character/paragraph counts where available, and uncertainty.
10. **Review** — allow the user to inspect/edit extracted source before narration.

## Source adapters

Adapters are independent modules selected by hostname and source characteristics. The current code now includes a `SourceAdapter` protocol, registry, and generic HTML fallback in `backend/app/source_adapters.py`. Domain-specific adapters can be registered without rewriting the fetch pipeline. A future domain adapter should provide:

- adapter identifier and version;
- supported hostnames;
- source-type classification;
- chapter title extraction;
- story-content extraction;
- canonical chapter identity;
- continuation-page detection;
- ordering metadata;
- extraction diagnostics.

A domain adapter must not assume every link on a page belongs to the chapter. Previous/next chapter links, related stories, comments, advertisements, and recommendations are not chapter continuation.

## Generic HTML fallback

The generic adapter should prefer semantic content containers such as `article`, `main`, and known reading-content containers. It should compare candidate content blocks and avoid blindly taking all text from the body.

The current backend uses a registered generic BeautifulSoup adapter that prefers semantic article/main containers, removes common navigation and advertisement elements, extracts title and paragraph text, and returns basic source metadata (domain, adapter ID/version, segment count, paragraph count, and warnings). It does not yet execute JavaScript, render a browser DOM, or recognize multi-page chapter navigation. A page that requires JavaScript or an authenticated session may fail. The current URL verification state is deliberately `review_required`; a single successful HTTP response is not proof that the full chapter was captured.

## Multi-page chapter rules

- A multi-page chapter remains one story part.
- Append pages in verified reading order.
- Keep page boundaries in source metadata for traceability.
- Do not include unrelated navigation or the next chapter as part of the current chapter.
- If continuation is ambiguous, stop and report that manual review is needed rather than guessing.
- A submitted URL remains one chapter/part URL; it does not imply fetching an entire volume or series.

## Access and security boundaries

- Respect website terms, copyright, access controls, authentication, paywalls, CAPTCHAs, and anti-bot restrictions.
- Do not bypass access restrictions or scrape content the user is not authorized to access.
- URL fetching must defend against SSRF, private IPs, redirects to private networks, oversized responses, and unsupported content types.
- The backend should enforce timeouts and request size limits.
- Never put provider API keys in frontend JavaScript or public repository files.

## Supported user-provided files

Current FastAPI implementation supports TXT, Markdown, HTML, text-based PDF, DOCX, and EPUB extraction. It supports single- or multi-page JPG, JPEG, PNG, and WEBP image OCR, plus CBZ/ZIP comic archives with natural filename ordering. Scanned PDFs can also be rendered and transcribed through a configured vision provider.

Planned but not yet implemented in the current code:

- reliable EPUB spine/reading-order parsing;
- robust chapter-level extraction from all website layouts;
- JavaScript-rendered source pages;
- domain-specific adapter catalogue;
- continuation-page discovery and verification.

## Extraction result contract (target)

A future structured import result should include:

- source URL and canonical URL (when applicable);
- source domain and adapter ID/version;
- title and detected story-part label;
- source type;
- ordered page/segment list;
- ordered paragraphs or panel transcriptions;
- extraction warnings;
- counts and verification state;
- a clear indication when completeness cannot be established.

Suggested verification states: `complete`, `review_required`, `incomplete`, and `failed`. The current generic HTML URL importer returns `review_required` with warnings because it cannot establish chapter completeness. Explicit multi-page URL imports include zero-based character ranges for each ordered page segment in the combined source text. Scanned-PDF OCR likewise includes page-level character ranges for each transcription; these map to extracted text, not pixel coordinates on the original PDF page. The state `complete` must require explicit evidence, not just a non-empty text result.

## Comic and manga OCR structure

The comic OCR endpoint asks the configured vision model for a JSON sequence of panels and text blocks. Each block is classified as dialogue, thought, caption, SFX, or other; dialogue/thought blocks may carry a per-panel balloon number. The backend preserves the model's panel and item order, converts the structure into readable source text for the MASTER FORM V2 narration endpoint, and returns page, panel, and text-block character offsets for source review. The browser exposes these offsets as accessible selection buttons.

The image-upload interface now provides a page queue with thumbnails, accessible **Naikkan**, **Turunkan**, and **Hapus** controls, and preflight checks for page count and upload size. The order shown in the queue is the order sent to the OCR endpoint. A CBZ/ZIP upload is treated as one archive and its image entries are naturally sorted by filename; an archive cannot be mixed with individually uploaded images in one request. Archive contents do not have browser thumbnails in this queue, so filenames inside the archive remain important.

Each structured OCR text block receives conservative normalization before source offsets are calculated: Unicode is normalized to NFC, non-breaking spaces are converted to ordinary spaces, and repeated line/whitespace runs inside a single text block are collapsed. Words, names, punctuation, and onomatopoeia are not rewritten by this normalization. The narration endpoint then applies MASTER FORM V2: for Indonesian output it uses natural spoken Indonesian and faithfully conveys non-Indonesian dialogue/OCR without guessing, while preserving names, titles, distinctive terms, numbers, and meaningful SFX. Panel and balloon markers remain structural metadata, not spoken content.

This is model-proposed segmentation and ordering, not independent computer-vision validation. Invalid or non-JSON provider output is retained as plain text with a warning and without panel-level offsets. All comic OCR results remain in review-required state; users must compare the transcription and ordering against the original images before narration. Provider API keys remain server-side.
