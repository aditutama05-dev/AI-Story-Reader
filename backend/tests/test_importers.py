import unittest

from fastapi import HTTPException

from app.importers import _parse_html, _validate_public_url


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
