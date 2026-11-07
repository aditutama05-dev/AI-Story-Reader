import os
import unittest
from io import BytesIO
from unittest.mock import patch
import zipfile

from fastapi.testclient import TestClient

from app.main import app, _rate_buckets\nimport app.main as main_module


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


if __name__ == "__main__":
    unittest.main()
