from io import BytesIO
import unittest

from fastapi import HTTPException
from PIL import Image

from app.vision_ocr import build_ocr_prompt, normalize_page_image


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


if __name__ == "__main__":
    unittest.main()
