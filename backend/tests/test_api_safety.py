import os
import unittest
from io import BytesIO
from unittest.mock import patch
import zipfile

from fastapi.testclient import TestClient

from app.main import app, _rate_buckets
import app.main as main_module


class APISafetyTests(unittest.TestCase):
    def setUp(self):
        _rate_buckets.clear()
        self.client = TestClient(app)

    def test_import_endpoint_is_rate_limited_per_client(self):
        with patch.dict(os.environ, {"IMPORT_REQUESTS_PER_MINUTE": "1"}):
            first = self.client.post("/api/import/url", json={"url": ""})
            second = self.client.post("/api/import/url", json={"url": ""})
        self.assertEqual(first.status_code, 400)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers.get("retry-after"), "60")

    def test_cbz_archive_is_parsed_before_ai_configuration_check(self):
        archive = BytesIO()
        with zipfile.ZipFile(archive, "w") as book:
            book.writestr("pages/10.png", b"not-an-image-but-valid-zip-entry")
            book.writestr("pages/2.png", b"not-an-image-but-valid-zip-entry")
        with patch.dict(os.environ, {"AI_API_KEY": ""}):
            response = self.client.post(
                "/api/import/comic",
                files={"files": ("chapter.cbz", archive.getvalue(), "application/zip")},
                data={"direction": "vertical"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn("AI belum dikonfigurasi", response.json()["detail"])


    def test_multi_page_import_combines_explicit_urls_in_order(self):
        async def fake_extract(url):
            return {"title": "Chapter", "text": url.rsplit("/", 1)[-1], "characters": 2, "source_url": url, "source_domain": "example.com"}
        with patch.object(main_module, "extract_webpage_report", side_effect=fake_extract):
            response = self.client.post("/api/import/urls", json={"urls": ["https://example.com/chapter/page-1", "https://example.com/chapter/page-2"]})
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.json()["text"].index("page-1"), response.json()["text"].index("page-2"))
        self.assertEqual(response.json()["verification"]["page_count"], 2)

    def test_multi_page_import_rejects_mixed_domains(self):
        response = self.client.post("/api/import/urls", json={"urls": ["https://example.com/chapter/1", "https://other.example/chapter/2"]})
        self.assertEqual(response.status_code, 400)

    def test_multi_page_import_validates_entire_batch_before_fetching(self):
        def validate(url):
            if "127.0.0.1" in url:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="URL menuju alamat jaringan privat tidak diizinkan.")
            return url
        with patch.object(main_module, "_validate_public_url", side_effect=validate), patch.object(main_module, "extract_webpage_report") as fetch:
            response = self.client.post("/api/import/urls", json={"urls": ["https://example.com/chapter/1", "http://127.0.0.1/private"]})
        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()
    def test_audio_endpoint_returns_one_complete_mp3_response(self):
        import edge_tts
        class FakeCommunicate:
            def __init__(self, text, voice, rate):
                self.text = text
            async def stream(self):
                yield {"type": "audio", "data": b"MP3-PART-1"}
                yield {"type": "audio", "data": b"MP3-PART-2"}
        with patch.object(edge_tts, "Communicate", FakeCommunicate):
            response = self.client.post("/api/audio", json={"text": "Narasi lengkap"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "audio/mpeg")
        self.assertEqual(response.content, b"MP3-PART-1MP3-PART-2")

    def test_private_api_token_is_required_when_configured(self):
        with patch.dict(os.environ, {"APP_ACCESS_TOKEN": "private-test-token"}):
            denied = self.client.post("/api/import/url", json={"url": ""})
            allowed = self.client.post("/api/import/url", json={"url": ""}, headers={"Authorization": "Bearer private-test-token"})
            health = self.client.get("/api/health")
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(allowed.status_code, 400)
        self.assertEqual(health.status_code, 200)

    def test_master_form_prompt_prioritizes_complete_chronological_storytelling(self):
        source = open(main_module.__file__, encoding="utf-8").read()
        self.assertIn("hasilnya bukan ringkasan", source)
        self.assertIn("dialog penting melalui parafrasa yang setia", source)
        self.assertIn("Jangan mengarang dialog", source)
        self.assertIn("jangan menghilangkan peristiwa baru", source)

    def test_scanned_pdf_is_rendered_before_provider_configuration_check(self):
        import fitz
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Sample scanned text")
        payload = pdf.tobytes()
        pdf.close()
        with patch.dict(os.environ, {"AI_API_KEY": ""}):
            response = self.client.post("/api/import/pdf-ocr", files={"file": ("scan.pdf", payload, "application/pdf")})
        self.assertEqual(response.status_code, 503)
        self.assertIn("AI belum dikonfigurasi", response.json()["detail"])

    def test_narration_returns_review_required_chunk_sanity_report(self):
        source = open(main_module.__file__, encoding="utf-8").read()
        self.assertIn("chunk_length_sanity_check", source)
        self.assertIn("source_characters", source)
        self.assertIn("narration_characters", source)
        self.assertIn("belum membuktikan kesetiaan semantik", source)

if __name__ == "__main__":
    unittest.main()
