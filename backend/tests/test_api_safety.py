import os
import unittest
from io import BytesIO
from unittest.mock import patch
import zipfile
from pathlib import Path

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



    def test_comic_archive_rejects_unsafe_paths_before_ocr(self):
        archive = BytesIO()
        with zipfile.ZipFile(archive, "w") as book:
            book.writestr("../outside.png", b"not-an-image")
        response = self.client.post(
            "/api/import/comic",
            files={"files": ("chapter.cbz", archive.getvalue(), "application/zip")},
            data={"direction": "vertical"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("jalur file yang tidak aman", response.json()["detail"])

    def test_multi_page_import_combines_explicit_urls_in_order(self):
        async def fake_extract(url):
            return {"title": "Chapter", "text": url.rsplit("/", 1)[-1], "characters": 2, "source_url": url, "source_domain": "example.com"}
        with patch.object(main_module, "extract_webpage_report", side_effect=fake_extract):
            response = self.client.post("/api/import/urls", json={"urls": ["https://example.com/chapter/page-1", "https://example.com/chapter/page-2"]})
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.json()["text"].index("page-1"), response.json()["text"].index("page-2"))
        self.assertEqual(response.json()["verification"]["page_count"], 2)


    def test_comic_ocr_page_offsets_match_combined_text(self):
        pages = [{"page": 1, "filename": "1.png", "text": "Panel pertama."}, {"page": 2, "filename": "2.png", "text": "Panel kedua."}]
        cursor = 0
        for index, page in enumerate(pages):
            if index:
                cursor += 2
            cursor += len(f"[Halaman {page['page']}]\\n")
            page["source_start"] = cursor
            cursor += len(page["text"])
            page["source_end"] = cursor
        combined = "\\n\\n".join(f"[Halaman {page['page']}]\\n{page['text']}" for page in pages)
        for page in pages:
            self.assertEqual(combined[page["source_start"]:page["source_end"]], page["text"])

    def test_multi_page_import_returns_exact_source_offsets_for_each_page(self):
        async def fake_extract(url):
            page = url.rsplit("/", 1)[-1]
            return {"title": "Chapter", "text": "isi " + page, "characters": len("isi " + page), "source_url": url, "source_domain": "example.com"}
        with patch.object(main_module, "extract_webpage_report", side_effect=fake_extract):
            response = self.client.post("/api/import/urls", json={"urls": ["https://example.com/chapter/1", "https://example.com/chapter/2"]})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for segment in data["segments"]:
            self.assertEqual(data["text"][segment["source_start"]:segment["source_end"]], "isi " + str(segment["index"]))

    def test_scanned_pdf_page_offsets_match_combined_text(self):
        pages = [{"page": 1, "text": "Halaman satu."}, {"page": 2, "text": "Halaman dua."}]
        cursor = 0
        for index, item in enumerate(pages):
            if index:
                cursor += 2
            item["source_start"] = cursor
            cursor += len(item["text"])
            item["source_end"] = cursor
        combined = "\\n\\n".join(item["text"] for item in pages)
        for item in pages:
            self.assertEqual(combined[item["source_start"]:item["source_end"]], item["text"])

    def test_multi_page_import_rejects_combined_text_over_limit(self):
        async def fake_extract(url):
            return {"title": "Chapter", "text": "123456", "characters": 6, "source_url": url, "source_domain": "example.com"}
        with patch.object(main_module, "MAX_BATCH_IMPORT_CHARS", 10), patch.object(
            main_module, "extract_webpage_report", side_effect=fake_extract
        ):
            response = self.client.post(
                "/api/import/urls",
                json={"urls": ["https://example.com/chapter/1", "https://example.com/chapter/2"]},
            )
        self.assertEqual(response.status_code, 413)

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


    def test_audio_endpoint_rejects_unsupported_voice(self):
        response = self.client.post(
            "/api/audio",
            json={"text": "Narasi lengkap", "voice": "unsupported-voice"},
        )
        self.assertEqual(response.status_code, 422)

    def test_private_api_token_is_required_when_configured(self):
        with patch.dict(os.environ, {"APP_ACCESS_TOKEN": "private-test-token"}):
            denied = self.client.post("/api/import/url", json={"url": ""})
            allowed = self.client.post("/api/import/url", json={"url": ""}, headers={"Authorization": "Bearer private-test-token"})
            health = self.client.get("/api/health")
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(allowed.status_code, 400)
        self.assertEqual(health.status_code, 200)

    def test_master_form_prompt_prioritizes_complete_chronological_storytelling(self):
        source = Path(main_module.__file__).read_text(encoding="utf-8")
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


    def test_scanned_pdf_rejects_excessive_page_dimensions_before_render(self):
        import fitz
        pdf = fitz.open()
        pdf.new_page(width=10000, height=10000)
        payload = pdf.tobytes()
        pdf.close()
        response = self.client.post(
            "/api/import/pdf-ocr",
            files={"file": ("oversized.pdf", payload, "application/pdf")},
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("Resolusi atau total area", response.json()["detail"])

    def test_find_source_span_returns_original_offsets_across_whitespace(self):
        source = "Awal\n\nRaka  memasuki   kastil tua. Akhir."
        span = main_module.find_source_span(source, "Raka memasuki kastil tua.")
        self.assertIsNotNone(span)
        self.assertEqual(source[span[0]:span[1]], "Raka  memasuki   kastil tua.")

    def test_find_source_span_is_case_insensitive_and_rejects_missing_quote(self):
        source = "Sang Naga menjaga gerbang."
        span = main_module.find_source_span(source, "sang naga MENJAGA gerbang.")
        self.assertEqual(source[span[0]:span[1]], source)
        self.assertIsNone(main_module.find_source_span(source, "Naga membakar gerbang."))

    def test_continuity_extraction_rejects_quotes_not_present_in_source(self):
        source = "Mira memasuki aula dan memperkenalkan dirinya sebagai kapten penjaga."
        async def fake_generate(*args, **kwargs):
            return ('{"facts":['
                '{"category":"character","fact":"Mira adalah kapten penjaga","sourceExcerpt":"memperkenalkan dirinya sebagai kapten penjaga"},'
                '{"category":"location","fact":"Aula berada di ibu kota","sourceExcerpt":"aula megah di ibu kota"}]}')
        with patch.object(main_module, "provider_config", return_value=("openrouter", "test-model", "test-key", "https://example.com/v1")), patch.object(
            main_module, "generate_text", side_effect=fake_generate
        ):
            response = self.client.post("/api/continuity/extract", json={"text": source, "title": "Chapter 1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["accepted"], 1)
        self.assertEqual(data["rejected"], 1)
        self.assertEqual(data["facts"][0]["category"], "character")
        span = data["facts"][0]["sourceStart"], data["facts"][0]["sourceEnd"]
        self.assertEqual(source[span[0]:span[1]], data["facts"][0]["sourceExcerpt"])
        self.assertEqual(data["verification"]["method"], "verbatim_source_excerpt_match")


    def test_continuity_check_accepts_only_valid_prior_index_and_current_source_quote(self):
        source = "Raka membuka pintu dengan tangan kirinya. Ia lalu memasuki ruangan."
        async def fake_generate(*args, **kwargs):
            return ('{"contradictions":['
                '{"fact_index":0,"current_excerpt":"membuka pintu dengan tangan kirinya","explanation":"Fakta lama menyebut Raka selalu kehilangan tangan kiri.","severity":"high"},'
                '{"fact_index":9,"current_excerpt":"memasuki ruangan","explanation":"Indeks fakta tidak ada.","severity":"low"},'
                '{"fact_index":0,"current_excerpt":"Raka membuka pintu dengan tangan kanannya","explanation":"Kutipan tidak ada di sumber.","severity":"medium"}]}')
        facts = [{"category":"character","fact":"Raka tidak memiliki tangan kiri","chapterTitle":"Chapter 1"}]
        with patch.object(main_module, "provider_config", return_value=("openrouter", "test-model", "test-key", "https://example.com/v1")), patch.object(
            main_module, "generate_text", side_effect=fake_generate
        ):
            response = self.client.post("/api/continuity/check", json={"text":source,"title":"Chapter 2","prior_facts":facts})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["accepted"], 1)
        self.assertEqual(data["rejected"], 2)
        self.assertEqual(data["contradictions"][0]["prior_fact"], facts[0]["fact"])
        self.assertEqual(data["verification"]["method"], "prior_fact_index_and_verbatim_current_excerpt_match")
        item = data["contradictions"][0]
        self.assertEqual(source[item["current_start"]:item["current_end"]], item["current_excerpt"])

    def test_continuity_check_requires_prior_facts(self):
        response = self.client.post("/api/continuity/check", json={"text":"Teks baru","prior_facts":[]})
        self.assertEqual(response.status_code, 422)

    def test_narration_accepts_continuity_context_as_secondary_reference(self):
        prompts = []
        async def fake_generate(client, provider, model, api_key, base_url, system_prompt, user_prompt):
            prompts.append((system_prompt, user_prompt))
            return "Narasi lengkap berdasarkan teks sumber saat ini. " * 8
        with patch.object(main_module, "provider_config", return_value=("openrouter", "test-model", "test-key", "https://example.com/v1")), patch.object(
            main_module, "generate_text", side_effect=fake_generate
        ):
            response = self.client.post("/api/narrate", json={
                "text": "Tokoh utama memasuki ruangan dan menyapa penjaga.",
                "title": "Chapter 5",
                "continuity_context": "Seri: Contoh\\n- Chapter 4: Penjaga mengenal tokoh utama.",
            })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Penjaga mengenal tokoh utama", prompts[0][1])
        self.assertIn("referensi tambahan", prompts[0][0])
        self.assertIn("referensi sekunder", prompts[0][1])
        self.assertIn("utamakan teks sumber", prompts[0][0])

    def test_narration_verification_flags_empty_compressed_and_duplicate_chunks(self):
        from app.main import build_narration_verification

        chunks = ["A" * 3000, "B" * 3000, "C" * 3000, "D" * 3000]
        repeated = "Narasi yang sama dan cukup panjang untuk diuji. " * 8
        outputs = [repeated, repeated, "", "pendek"]
        report = build_narration_verification(chunks, outputs)
        self.assertEqual(report["method"], "chunk_length_and_duplicate_output_checks")
        self.assertEqual(report["empty_chunks"], [3])
        self.assertEqual(report["duplicate_output_chunks"], [{"chunk": 2, "duplicate_of": 1}])
        self.assertEqual(report["compressed_chunks"], [1, 2, 3, 4])
        self.assertEqual(report["status"], "review_required")

    def test_narration_returns_review_required_chunk_sanity_report(self):
        source = open(main_module.__file__, encoding="utf-8").read()
        self.assertIn("chunk_length_and_duplicate_output_checks", source)
        self.assertIn("source_characters", source)
        self.assertIn("narration_characters", source)
        self.assertIn("belum membuktikan kesetiaan semantik", source)

if __name__ == "__main__":
    unittest.main()
