import unittest
from io import BytesIO
import zipfile

from fastapi import HTTPException

from app.importers import _parse_html, _validate_public_url, _validate_archive_limits, extract_document


class HTMLExtractionTests(unittest.TestCase):
    def test_prefers_story_content_and_removes_navigation_noise(self):
        source = b"""<!doctype html><html><head><title>Fallback title</title></head>
        <body><nav>Menu link</nav><h1>Chapter 12</h1>
        <article><p>Paragraf pertama cerita.</p><p>Paragraf kedua cerita.</p>
        <div class='advertisement'>Iklan tidak boleh ikut.</div></article>
        <aside class='related'>Cerita rekomendasi.</aside></body></html>"""
        title, text, paragraphs, container = _parse_html(source)
        self.assertEqual(title, "Chapter 12")
        self.assertIn("Paragraf pertama cerita.", text)
        self.assertIn("Paragraf kedua cerita.", text)
        self.assertNotIn("Menu link", text)
        self.assertNotIn("Iklan tidak boleh ikut", text)
        self.assertNotIn("Cerita rekomendasi", text)
        self.assertEqual(paragraphs, 2)
        self.assertEqual(container, "article")

    def test_generic_adapter_is_selected_as_fallback(self):
        from app.source_adapters import resolve_source_adapter

        adapter = resolve_source_adapter("https://unregistered.example/chapter")
        self.assertEqual(adapter.adapter_id, "generic-html")
        self.assertTrue(adapter.supports("https://unregistered.example/chapter"))

    def test_url_validator_rejects_private_ip(self):
        with self.assertRaises(HTTPException) as error:
            _validate_public_url("http://127.0.0.1/chapter")
        self.assertEqual(error.exception.status_code, 400)

    def test_url_validator_rejects_non_http_scheme(self):
        with self.assertRaises(HTTPException) as error:
            _validate_public_url("file:///etc/passwd")
        self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()


class URLStreamingImportTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_oversized_content_length_before_reading_body(self):
        import httpx
        from unittest.mock import patch
        from app.importers import MAX_URL_BYTES, extract_webpage_report

        async def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8", "content-length": str(MAX_URL_BYTES + 1)},
                content=b"",
                request=request,
            )

        original_client = httpx.AsyncClient

        def client_factory(**kwargs):
            return original_client(transport=httpx.MockTransport(handler), **kwargs)

        with patch("app.importers._validate_public_url", return_value="https://example.com/story.txt"), patch(
            "app.importers.httpx.AsyncClient", side_effect=client_factory
        ):
            with self.assertRaises(HTTPException) as error:
                await extract_webpage_report("https://example.com/story.txt")
        self.assertEqual(error.exception.status_code, 413)

    async def test_streams_and_decodes_plain_text_response(self):
        import httpx
        from unittest.mock import patch
        from app.importers import extract_webpage_report

        async def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                content="Bab pertama\\n\\nCerita berlanjut.".encode(),
                request=request,
            )

        original_client = httpx.AsyncClient

        def client_factory(**kwargs):
            return original_client(transport=httpx.MockTransport(handler), **kwargs)

        with patch("app.importers._validate_public_url", return_value="https://example.com/chapter.txt"), patch(
            "app.importers.httpx.AsyncClient", side_effect=client_factory
        ):
            result = await extract_webpage_report("https://example.com/chapter.txt")
        self.assertIn("Cerita berlanjut.", result["text"])
        self.assertEqual(result["verification"]["page_count"], 1)


class ArchiveSafetyTests(unittest.TestCase):
    def test_rejects_archive_path_traversal(self):
        archive_bytes = BytesIO()
        with zipfile.ZipFile(archive_bytes, "w") as archive:
            archive.writestr("../outside.txt", "not safe")
        with zipfile.ZipFile(BytesIO(archive_bytes.getvalue())) as archive:
            with self.assertRaises(HTTPException) as error:
                _validate_archive_limits(archive)
        self.assertEqual(error.exception.status_code, 400)

    def test_rejects_oversized_uncompressed_archive_member(self):
        archive_bytes = BytesIO()
        info = zipfile.ZipInfo("large.txt")
        info.file_size = 25 * 1024 * 1024 + 1
        with zipfile.ZipFile(archive_bytes, "w") as archive:
            archive.writestr(info, b"x")
        with zipfile.ZipFile(BytesIO(archive_bytes.getvalue())) as archive:
            with self.assertRaises(HTTPException) as error:
                _validate_archive_limits(archive)
        self.assertEqual(error.exception.status_code, 413)
