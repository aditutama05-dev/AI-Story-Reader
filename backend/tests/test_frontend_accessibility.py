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
        self.assertIn("indexedDB.open(readingDatabaseName,2)", HTML)
        self.assertIn("restoreSavedChapter();", HTML)
        self.assertIn("scrollToParagraph(index)", HTML)
        self.assertIn("renderNarration(data.narration)", HTML)

    def test_tts_controls_are_labelled_and_configurable(self):
        for control_id in ("play", "pause", "resume", "stop", "speechRate", "voiceSelect"):
            self.assertIn(f'id="{control_id}"', HTML)
        self.assertIn('utterance.lang="id-ID"', HTML)
        self.assertIn('utterance.rate=Number($("speechRate").value)||1', HTML)

    def test_library_builds_prior_chapter_continuity_context(self):
        library = (FRONTEND.parent / "library.js").read_text(encoding="utf-8")
        self.assertIn("function buildContinuityContext(chapterId)", library)
        self.assertIn("parts.slice(0,index)", library)
        self.assertIn("getContinuityContext:buildContinuityContext", library)
        self.assertIn("getContinuityContext?.(window.currentLibraryChapterId)", HTML)
        self.assertIn("body.continuity_context=continuity", HTML)

    def test_automatic_continuity_extraction_requires_user_review_before_save(self):
        self.assertIn('id="extractFacts"', HTML)
        self.assertIn('/api/continuity/extract', HTML)
        self.assertIn('if(!confirm("Periksa usulan fakta berikut.', HTML)
        library = (FRONTEND.parent / "library.js").read_text(encoding="utf-8")
        self.assertIn("async function storeExtractedFacts", library)
        self.assertIn("storeExtractedFacts};", library)

    def test_library_supports_structured_source_grounded_continuity_facts(self):
        library = (FRONTEND.parent / "library.js").read_text(encoding="utf-8")
        self.assertIn("async function editContinuityFacts", library)
        self.assertIn('"character","relationship","location","term","event","conflict"', library)
        self.assertIn("sourceExcerpt", library)
        self.assertIn('textContent="Fakta terstruktur"', library)
        self.assertIn("FAKTA KONTINUITAS TERIKAT KE SUMBER", library)
        self.assertIn('"; kutipan: "+fact.sourceExcerpt+")"', library)

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
        self.assertIn("partType", library)
        self.assertIn("Interlude, Ending, Epilogue", library)
        self.assertIn("function editNotes", library)
        self.assertIn("notesUpdatedAt", library)

    def test_full_chapter_mp3_and_multi_page_import_controls_exist(self):
        for control_id in ("generateMp3", "chapterAudio", "downloadMp3", "seekBack", "seekForward", "audioVoice", "continuationUrls"):
            self.assertIn('id="' + control_id + '"', HTML)
        self.assertIn('apiFetch("/api/audio"', HTML)
        self.assertIn('apiFetch(endpoint', HTML)
        self.assertIn(".cbz,.zip", HTML)

    def test_mp3_playback_position_is_persisted_and_restored(self):
        self.assertIn('progress.audioPosition=audio.currentTime', HTML)
        self.assertIn('addEventListener("timeupdate"', HTML)
        self.assertIn('addEventListener("loadedmetadata"', HTML)
        self.assertIn('progress.audioPosition<$("chapterAudio").duration', HTML)
        self.assertIn('audioPosition:previous?.audioPosition??0', HTML)


    def test_library_chapters_have_independent_reading_progress_and_audio_positions(self):
        self.assertIn('let activeReadingId="current"', HTML)
        self.assertIn('indexedDB.open(readingDatabaseName,2)', HTML)
        self.assertIn('readReadingStore(storeName,recordId=activeReadingId)', HTML)
        self.assertIn('activeReadingId=libraryChapterId?"chapter:"+libraryChapterId:"current"', HTML)
        self.assertIn('libraryChapterId=libraryChapterId||window.currentLibraryChapterId||null', HTML)
        self.assertIn('progress.id=activeReadingId', HTML)
        self.assertIn('window.restoreStoryNarration=async(title,text,libraryChapterId=null)', HTML)
        library = (FRONTEND.parent / "library.js").read_text(encoding="utf-8")
        self.assertIn('window.currentLibraryChapterId=chapter.id;await window.restoreStoryNarration?.(chapter.title,chapter.narration,chapter.id)', library)
        self.assertIn('activeReadingId', HTML)

    def test_browser_tts_highlights_current_word_when_boundary_events_exist(self):
        self.assertIn("data-word-start", HTML)
        self.assertIn('utterance.onboundary=event=>', HTML)
        self.assertIn('classList.add("speech-current-word")', HTML)
        self.assertIn('aria-current","true"', HTML)


if __name__ == "__main__":
    unittest.main()
