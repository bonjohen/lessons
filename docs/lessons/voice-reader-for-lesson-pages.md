---
title: Adding a Voice Reader to Lesson Pages
summary: Integrating browser-native text-to-speech into a static site requires handling platform quirks, script timing, and progressive enhancement — the Web Speech API is powerful but fragile across browsers.
date: 2026-05-10
phase: implementation
lesson_type: frontend
status: active
tags: [web-speech-api, text-to-speech, accessibility, astro, progressive-enhancement, browser-quirks]
---

# Adding a Voice Reader to Lesson Pages

## The Lesson

The Web Speech API provides free, zero-dependency text-to-speech in every modern browser, but shipping a reliable voice reader requires handling Chrome's 15-second utterance cutoff, Android's broken pause/resume, script execution timing in static site generators, and graceful degradation when the API is unavailable.

## Context

A lessons-learned hub built with Astro (static output) needed a "read aloud" feature for lesson pages. A reference implementation existed in a standalone markdown reader app — a simple tool for rendering and reading markdown files aloud — using vanilla JS and the Web Speech API. The goal was to port the concept into an Astro component, improve on it with paragraph highlighting and section navigation, and integrate it with the site's existing design system.

## What Happened

1. **Built a self-contained `VoiceReader.astro` component** using the Web Speech API (`window.speechSynthesis` and `SpeechSynthesisUtterance`). No external dependencies — no CDN loads, no npm packages. The component reads text from a target content element specified by a CSS selector prop.

2. **The component rendered but was invisible.** The voice reader div had `style="display: none;"` applied at runtime. The script used an IIFE that ran immediately when parsed, but the component was placed *above* the lesson content in the DOM. At execution time, `document.querySelector('.lesson-content')` returned `null` because that element hadn't been parsed yet. The fallback logic hid the reader: `if (!contentEl) { root.style.display = 'none'; }`. Fix: wrap the initialization in `document.addEventListener('DOMContentLoaded', ...)`.

3. **Chrome stops speaking after ~15 seconds.** Desktop Chrome silently kills any `SpeechSynthesisUtterance` that runs longer than roughly 15 seconds. The workaround is twofold: chunk text into segments under 200 characters at sentence boundaries, and run a keep-alive timer that calls `speechSynthesis.pause(); speechSynthesis.resume();` every 10 seconds to reset Chrome's internal timer.

4. **Android Chrome's pause/resume is broken.** Calling `speechSynthesis.pause()` on Android permanently halts speech — `resume()` does nothing. The workaround: on Android, "pause" actually calls `speechSynthesis.cancel()` and sets a flag so the `onend` handler doesn't advance to the next chunk. "Resume" re-speaks the current chunk from the start. Users lose their position within a chunk, but it's better than a dead pause button.

5. **Text chunking needs sentence-aware splitting.** Naive splitting by character count produces chunks that break mid-word or mid-sentence, causing unnatural speech. The chunker splits on sentence-ending punctuation first (`/(?<=[.!?])\s+/`), then accumulates sentences into chunks up to the size limit. Oversized sentences get further split on commas. Android uses larger chunks (500 chars vs 200) because shorter chunks cause more inter-chunk gaps where Android can drop speech.

6. **Voice selection UX matters.** `speechSynthesis.getVoices()` returns a flat list mixing low-quality and high-quality voices. Categorizing voices by quality (matching `/Natural|Neural|Online|Premium|Enhanced/i`) and sorting English voices first makes the dropdown usable. Persisting the selection to `localStorage` prevents users from re-picking every page load.

7. **Screen wake lock prevents device sleep during long reads.** The Screen Wake Lock API (`navigator.wakeLock.request('screen')`) keeps the screen on during playback. It must be re-acquired on `visibilitychange` because the browser releases it when the tab goes to background.

## Key Insights

- **Script execution order in static sites is a class of bug.** Astro renders components in document order. An inline script in a component that appears before its target content will fail silently. `DOMContentLoaded` is the reliable fix, not script placement. This applies to any framework that renders components sequentially into static HTML.

- **The Web Speech API is a "works on my machine" trap.** It works perfectly in desktop Chrome during development. Android, Safari, Firefox, and even Chrome on different OS versions all have different failure modes. The reference implementation had already solved most of these — porting without understanding *why* each workaround existed would have dropped them.

- **Progressive enhancement is the only safe approach.** The component checks for `window.speechSynthesis` and hides itself if unavailable. No error, no broken UI, no placeholder. Users on unsupported browsers never know the feature exists. This is better than showing a disabled button that implies something is broken.

- **Paragraph highlighting transforms the reading experience.** The reference implementation had no visual feedback beyond a progress bar. Adding a CSS highlight (`.vr-reading`) to the current block element and scrolling it into view turns passive listening into active reading — users can follow along and jump back to re-read sections.

- **Port allocation for concurrent development needs a scheme, not defaults.** When running multiple repos' dev servers simultaneously, default ports (4321, 8000) collide immediately. Assigning each project a unique port pair (e.g., 4331/8011 for this project) in config files prevents the "which project stole my port" problem. The scheme should leave gaps for future projects.

## Recommendations

1. **Always wrap component scripts in `DOMContentLoaded`** when the script references DOM elements outside its own component tree. Astro's `is:inline` scripts execute as the parser encounters them — they cannot assume the full page exists yet.

2. **Test speech features on Android early.** Desktop Chrome's Web Speech API is forgiving. Android's is not. The pause/resume, chunk timing, and voice availability all differ. Test on a real Android device, not just Chrome DevTools' device emulation (which uses desktop speech synthesis).

3. **Persist user preferences for voice and rate.** Users who change the voice or speed once will want the same setting on every page. Two `localStorage` keys (`vr-voice`, `vr-rate`) cost nothing and eliminate a repeated friction point.

4. **Chunk at sentence boundaries, not character counts.** Speech that stops mid-sentence sounds broken. The chunking algorithm should prioritize natural pause points (periods, question marks, exclamation marks) over hitting an exact size target.

5. **Use CSS variables from the host site's design system.** A component that brings its own colors will clash with dark mode, custom themes, or any visual refresh. The voice reader uses `var(--color-border)`, `var(--color-accent)`, etc. — it automatically matches whatever theme is active.
