from pathlib import Path
import re
import unittest


FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
HTML = FRONTEND.read_text(encoding="utf-8")


class FrontendAccessibilityTests(unittest.TestCase):
    def test_document_language_and_skip_navigation(self):
        self.assertIn('<html lang="id">', HTML)
        self.assertIn('href="#main-content"', HTML)
        self.assertIn('<main id="main-content"', HTML)
        self.assertIn('<nav class="card" aria-label="Navigasi cepat">', HTML)

    def test_primary_sections_have_accessible_names(self):
        for section_id in ("accessibility-heading", "import-heading", "comic-heading", "editor-heading", "result-heading"):
            self.assertIn(f'aria-labelledby="{section_id}"', HTML)
            self.assertIn(f'id="{section_id}"', HTML)

    def test_long_narration_is_readable_without_forced_live_announcement(self):
        self.assertIn('role="region" aria-label="Teks lengkap hasil narasi"', HTML)
        self.assertNotIn('aria-label="Teks lengkap hasil narasi" aria-live=', HTML)
        self.assertIn('role="status" aria-live="polite" aria-atomic="true"', HTML)

    def test_accessibility_controls_and_preferences_exist(self):
        for control_id in ("textSize", "contrastToggle", "spacingToggle", "motionToggle"):
            self.assertIn(f'id="{control_id}"', HTML)
        self.assertIn("localStorage.setItem(preferenceKey", HTML)
        self.assertIn("localStorage.getItem(preferenceKey", HTML)
        self.assertIn("prefers-reduced-motion:reduce", HTML)

    def test_tts_controls_are_labelled_and_configurable(self):
        for control_id in ("play", "pause", "resume", "stop", "speechRate", "voiceSelect"):
            self.assertIn(f'id="{control_id}"', HTML)
        self.assertIn('utterance.lang="id-ID"', HTML)
        self.assertIn('utterance.rate=Number($("speechRate").value)||1', HTML)


if __name__ == "__main__":
    unittest.main()
