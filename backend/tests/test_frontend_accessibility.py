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

    def test_navy_blue_theme_and_no_purple_palette(self):
        self.assertIn("#081522", HTML)
        self.assertIn("#2f8cff", HTML)
        self.assertNotIn("#a987ef", HTML)
        self.assertNotIn("#c6a7ff", HTML)
        self.assertIn("AI_STORY_READER_API_BASE", HTML)

    def test_url_import_surfaces_verification_warnings(self):
        self.assertIn("data.verification.warnings", HTML)
        self.assertIn("status: perlu diperiksa", HTML)

    def test_reading_progress_and_bookmarks_are_persisted(self):
        for control_id in ("saveBookmark", "resumeReading", "clearProgress"):
            self.assertIn(f'id="{control_id}"', HTML)
        self.assertIn("indexedDB.open(readingDatabaseName,1)", HTML)
        self.assertIn("restoreSavedChapter();", HTML)
        self.assertIn("scrollToParagraph(index)", HTML)
        self.assertIn("renderNarration(data.narration)", HTML)

    def test_tts_controls_are_labelled_and_configurable(self):
        for control_id in ("play", "pause", "resume", "stop", "speechRate", "voiceSelect"):
            self.assertIn(f'id="{control_id}"', HTML)
        self.assertIn('utterance.lang="id-ID"', HTML)
        self.assertIn('utterance.rate=Number($("speechRate").value)||1', HTML)

    def test_story_library_uses_indexeddb_and_keeps_source_separate(self):
        library = (FRONTEND.parent / "library.js").read_text(encoding="utf-8")
        for control_id in ("library-heading", "addSeries", "exportLibrary", "importLibrary", "libraryTree"):
            self.assertIn('id="' + control_id + '"', HTML)
        self.assertIn("indexedDB.open(DB_NAME,1)", library)
        self.assertIn("originalSource", library)
        self.assertIn("narration", library)
        self.assertIn("function addArcTo", library)
        self.assertIn("function addVolume", library)
        self.assertIn("function addChapter", library)

    def test_full_chapter_mp3_and_multi_page_import_controls_exist(self):
        for control_id in ("generateMp3", "chapterAudio", "downloadMp3", "seekBack", "seekForward", "audioVoice", "continuationUrls"):
            self.assertIn('id="' + control_id + '"', HTML)
        self.assertIn('fetch(apiUrl("/api/audio")', HTML)
        self.assertIn('fetch(apiUrl(endpoint)', HTML)
        self.assertIn(".cbz,.zip", HTML)

if __name__ == "__main__":
    unittest.main()
