from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from PIL import Image

from app.vision_ocr import build_document_page_prompt, build_ocr_prompt, normalize_page_image


class VisionOCRTests(unittest.TestCase):
    def make_png(self) -> bytes:
        buffer = BytesIO()
        Image.new("RGB", (2400, 1200), "white").save(buffer, format="PNG")
        return buffer.getvalue()

    def test_normalizes_png_to_jpeg_and_resizes(self):
        result = normalize_page_image(self.make_png(), "image/png")
        with Image.open(BytesIO(result)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertLessEqual(max(image.size), 1800)


    def test_rejects_excessive_pixel_dimensions_before_image_conversion(self):
        class OversizedImage:
            width = 10000
            height = 10000
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        with patch("app.vision_ocr.Image.open", return_value=OversizedImage()):
            with self.assertRaises(HTTPException) as error:
                normalize_page_image(b"image-bytes", "image/png")
        self.assertEqual(error.exception.status_code, 413)

    def test_rejects_unsupported_media_type(self):
        with self.assertRaises(HTTPException) as error:
            normalize_page_image(self.make_png(), "image/gif")
        self.assertEqual(error.exception.status_code, 415)

    def test_rejects_empty_image(self):
        with self.assertRaises(HTTPException) as error:
            normalize_page_image(b"", "image/png")
        self.assertEqual(error.exception.status_code, 400)

    def test_prompt_preserves_japanese_reading_direction(self):
        prompt = build_ocr_prompt(1, 3, "rtl")
        self.assertIn("kanan ke kiri", prompt)
        self.assertIn("[Panel 1]", prompt)
        self.assertIn("[tidak terbaca]", prompt)

    def test_prompt_supports_vertical_webtoon(self):
        prompt = build_ocr_prompt(2, 4, "vertical")
        self.assertIn("atas ke bawah", prompt)
        self.assertIn("Halaman 2 dari 4", prompt)

    def test_document_ocr_prompt_preserves_layout_and_marks_unclear_text(self):
        prompt = build_document_page_prompt(2, 5)
        self.assertIn("Halaman 2 dari 5", prompt)
        self.assertIn("Pertahankan pemisahan paragraf", prompt)
        self.assertIn("[tidak terbaca]", prompt)
        self.assertIn("Jangan meringkas", prompt)


if __name__ == "__main__":
    unittest.main()
