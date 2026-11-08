# Accessibility and Screen-Access Boundaries

## Product target

Novelith AI is a website used through a normal browser. It must support people who use Android TalkBack, desktop screen readers, keyboard navigation, browser zoom, and browser/device text-to-speech where available.

The project is not a native Android application. It does not install an Android Accessibility Service and does not run a floating window or a background screen-capture service.

## What the website can do

- Expose headings, landmarks, labels, buttons, form fields, and story text through semantic HTML.
- Let TalkBack and other screen readers read the website's text using their normal browser integration.
- Provide keyboard-accessible controls and visible focus.
- Offer high-contrast, larger-text, comfortable-spacing, and reduced-motion preferences.
- Use the browser Web Speech API for optional speech synthesis when supported by the browser and device.
- Read files explicitly selected by the user through a file input.
- Upload selected images for OCR/vision processing after the user chooses them.
- Fetch a public URL through the configured backend when the destination permits automated access and the backend can safely retrieve it.

## What the website cannot do or must not claim

- It cannot silently inspect the user's entire phone screen or other applications.
- It cannot read content from another app merely because TalkBack is enabled.
- It cannot install or behave like Android's Accessibility Service from an ordinary website.
- It cannot create an Android-style floating overlay above unrelated applications.
- It cannot capture the device screen in the background or continuously monitor other apps.
- It cannot control TalkBack's global gestures, system settings, or installed speech engines.
- It cannot guarantee a particular Indonesian voice exists on the user's device.
- It cannot bypass a website's login, paywall, CAPTCHA, access controls, or anti-bot protections.

These limitations are deliberate boundaries of the browser product, not bugs to work around by requesting excessive device permissions.

## TalkBack and screen-reader behavior

- Story text must remain real selectable HTML text, not be rendered only onto a canvas or embedded in an image.
- Use a logical heading hierarchy and semantic landmarks.
- Every input must have a visible and programmatic label.
- Controls must have meaningful names and state (for example, `aria-pressed` for toggles).
- Keep the complete long narration in a navigable region. Do not mark the entire chapter as a live region; doing so can cause a screen reader to announce a very long passage unexpectedly.
- Use a small polite live-status region for concise state changes such as import completion, OCR completion, and TTS start/stop.
- Do not intercept or replace TalkBack swipe gestures.
- Provide keyboard focus visibility and a skip-to-content link.
- Preserve browser zoom and avoid fixed text sizes that prevent enlargement.

## Browser TTS versus generated audiobook

Browser `speechSynthesis` is an optional device feature. Voice availability, quality, language, pause behavior, and background playback vary by browser and installed speech engine.

Browser TTS is not equivalent to a downloadable MP3 audiobook. Generated MP3, synchronized highlighting, reliable seeking, and persistent audio resume require a separate audio-generation/player implementation.

## Screen capture and OCR

The user must explicitly select image files or another supported source. The website processes only the files submitted through its interface. OCR/vision output must preserve page order and mark unreadable text instead of guessing.

## Verification required

Automated checks can validate HTML semantics and JavaScript syntax, but they cannot prove the experience works well with every assistive technology. Before release, perform manual testing with Android TalkBack on real devices, keyboard-only navigation, browser zoom, and at least one desktop screen reader if available.

Do not claim formal WCAG conformance or complete accessibility certification without a dedicated audit.
