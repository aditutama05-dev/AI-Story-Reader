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

Adapters are independent modules selected by hostname and source characteristics. A future adapter contract should provide:

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

The current backend uses a basic BeautifulSoup extraction fallback. It does not yet execute JavaScript, render a browser DOM, or recognize multi-page chapter navigation. A page that requires JavaScript or an authenticated session may fail.

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

Current FastAPI implementation supports TXT, Markdown, HTML, text-based PDF, DOCX, and EPUB extraction. It supports image OCR for multiple JPG, PNG, and WEBP pages.

Planned but not yet implemented in the current code:

- ZIP/CBZ archive import;
- OCR for scanned PDF pages;
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

Suggested verification states: `complete`, `review_required`, `incomplete`, and `failed`. The state `complete` must require explicit evidence, not just a non-empty text result.
