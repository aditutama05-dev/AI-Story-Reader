# Novelith AI — Human Test Checklist

This checklist contains only checks that require a person using a real browser, device, provider account, or visual judgment. Backend unit tests, JavaScript syntax checks, compilation, deployment workflows, and scheduled API health/config/CORS checks are handled automatically and do not need to be repeated manually.

Do not send API keys, access tokens, private book files, or account credentials in chat or screenshots. Use your own test material and a provider key you control. API usage may incur provider charges.

## 1. Live website and mobile layout
- [ ] In the library section, check the browser storage quota display. If offered, request persistent storage and confirm the status message. Remember this is browser quota, not the phone's entire free internal storage.
- [ ] Open https://aditutama05-dev.github.io/AI-Story-Reader/ on Android Chrome or Brave. Confirm the Novelith AI interface loads, not a README/Markdown page.
- [ ] Scroll through the full page. Confirm cards, text fields, buttons, and the library fit the phone width without horizontal scrolling or overlapping controls.
- [ ] Open the same site on a desktop browser and check the two-column areas and long text fields.
- [ ] Refresh the page and confirm it still loads.

## 2. Provider key and live API requests
- [ ] In the Provider AI section, choose a provider and paste your own key. Save it for the session. Never share the key or screenshot its value.
- [ ] Import a public chapter URL that you are allowed to access. Confirm the title and source text appear, and read the extraction warnings.
- [ ] Try a small TXT or Markdown file. Confirm the text appears in the source editor.
- [ ] Try a small text-based PDF, EPUB, and DOCX file if available. Confirm each import result is readable and in the expected order.
- [ ] Generate Indonesian narration from a chapter you know. Compare the beginning, middle, and ending against the source: check event order, character names, dialogue meaning, important actions, and whether the output invents or skips details.
- [ ] Clear the provider key after testing, or close the browser session. Confirm the site does not display the key.

## 3. Comic and scanned-PDF OCR
- [ ] Test a short sample of manga pages with right-to-left selected; check page order, panel order, speech balloons, names, and SFX against the images.
- [ ] Test a short manhwa/webtoon sample with vertical reading selected; check the order from top to bottom.
- [ ] Test LTR direction with a suitable sample if available.
- [ ] Move image pages up/down in the queue and confirm the displayed order matches the order sent for OCR.
- [ ] Try a small scanned PDF (30 pages or fewer). Compare OCR text with the original pages, especially names, numbers, punctuation, and unclear text.
- [ ] Confirm the OCR evidence links select the matching source text. Correct OCR errors before generating narration.

## 4. Audio
- [ ] Use browser TTS. Confirm play, pause, stop, voice selection, speech rate, and word/paragraph highlighting work in your browser.
- [ ] Generate an MP3 from a short chapter and play it to the end.
- [ ] Generate an MP3 from a longer chapter that requires multiple segments. Confirm all segments are present, the joined file downloads, playback reaches the end, and there is no missing/repeated section at segment boundaries.
- [ ] Pause, seek backward/forward, resume, and confirm the controls work.

## 5. Library, progress, and continuity
- [ ] Create a Series, Arc, Volume, and several story parts. Confirm Interlude, Chapter, Ending, and Epilogue remain separate story-part types, not volumes.
- [ ] Save a chapter with source text and narration. Refresh and reopen it; confirm both are restored separately.
- [ ] Add a bookmark, move the reading position, refresh, and confirm resume returns to the saved position.
- [ ] If MP3 is generated for a library chapter, refresh and confirm the audio position is restored independently.
- [ ] Export a JSON library backup, then test restoring it in a safe test library/profile. Confirm titles and story hierarchy survive.
- [ ] Add continuity notes/facts from earlier chapters. Confirm they are treated only as secondary hints and never replace the current chapter source.

## 6. Accessibility (Android)
- [ ] Enable TalkBack, navigate from the skip link through headings, labels, buttons, file inputs, and the story library. Confirm controls announce meaningful names and their state.
- [ ] Navigate and operate the comic queue and audio controls using TalkBack without relying on visual position alone.
- [ ] Try larger text, high contrast, comfortable reading spacing, and reduced motion.
- [ ] Confirm TTS and screen-reader navigation do not repeatedly announce the entire long narration after each small update.

## Known constraints while testing
- Server uploads are limited to a conservative 4 MB aggregate on this Vercel deployment. Large PDF/EPUB/CBZ/manga files are not supported through the current upload route.
- TXT/MD/HTML files can fall back to local browser import; that local import does not itself generate AI narration.
- OCR, narration, and continuity AI actions require a working provider key or an optional server-side provider configuration.
- Browser library, bookmarks, and progress are stored locally in that browser/device. They do not sync between devices.
- The AI output and OCR remain review-required; the original source/image is authoritative.
