---
title: "XSS via innerHTML in LLM Chat Interfaces"
summary: "Any UI that displays LLM-generated text has two untrusted input sources: the user's query and the model's response. Both must be sanitized before DOM insertion. The model's output is especially dangerous because developers intuitively trust \"their own backend\" — but the LLM's response is no more tru..."
date: 2026-05-13
lesson_type: security
tags: [security, deployment, frontend, python, javascript]
---
# XSS via innerHTML in LLM Chat Interfaces

## The Lesson

Any UI that displays LLM-generated text has two untrusted input sources: the user's query and the model's response. Both must be sanitized before DOM insertion. The model's output is especially dangerous because developers intuitively trust "their own backend" — but the LLM's response is no more trusted than user input.

## Context

A static knowledge library site included a chat panel that sent user questions to a FastAPI backend running RAG (retrieval-augmented generation) over a local Ollama model. The chat UI was a simple `<form>` + `<div>` where messages were appended to a container using `innerHTML`. The backend returned a JSON response with an `answer` string and a list of `relevant_lessons` (each with `title` and `url`). The site was deployed publicly on GitHub Pages.

## What Happened

1. The chat panel was built quickly during Phase 5 of a 7-phase plan. It used `innerHTML +=` to append both user messages and assistant responses to the chat container.
2. User input was interpolated directly into a template literal: `` `<p><strong>You:</strong> ${query}</p>` ``. A user typing `<img onerror=alert(1) src=x>` would execute arbitrary JavaScript.
3. The LLM response was also injected raw: `` `<p><strong>Assistant:</strong> ${data.answer}</p>` ``. If the model returned HTML (which language models frequently do when discussing code), it would be rendered as live markup.
4. Citation links used `l.url` and `l.title` from the backend response without validation. A `javascript:` URL or a title containing HTML would both execute.
5. A structured code review (7 categories, systematic grep for `innerHTML`) caught all three vectors in a single pass. The fix added an `escapeHtml()` helper using `textContent`/`innerHTML` round-trip, a `isSafeUrl()` validator (only `/` or `https://` prefixes), and `encodeURI()` on link hrefs.
6. The existing `sanitize-html` library was already in the project (used for lesson markdown rendering) but was not applied to the chat panel — a case of having the right tool but not using it everywhere.

## Key Insights

- **LLM responses are untrusted input.** Developers naturally think of "user input" as the threat vector. But in a RAG system, the model's response passes through retrieval, prompt assembly, and generation — any of those stages could inject HTML. Treat model output with the same suspicion as a query parameter.
- **innerHTML is almost never the right choice for dynamic content.** Using `textContent` for plain text and a sanitizer for rich text eliminates the entire class of DOM XSS. The performance difference is negligible. The only legitimate use of `innerHTML` is for static, developer-authored markup.
- **URL validation requires an allowlist, not a blocklist.** Checking `isSafeUrl()` with a prefix allowlist (`/` or `https://`) is more robust than trying to block `javascript:`, `data:`, `vbscript:`, and every other dangerous scheme. New schemes are added to browsers; your blocklist won't keep up.
- **Structured reviews catch what tests miss.** The XSS was not caught during Phase 5 implementation, Phase 6 E2E tests, or Phase 7 acceptance criteria verification. A systematic grep for `innerHTML` across the entire codebase found it immediately. Pattern-based audits complement test suites — they find classes of bugs, not individual cases.

## Examples

**Before (vulnerable):**
```js
messages.innerHTML += `<p><strong>You:</strong> ${query}</p>`;
messages.innerHTML += `<p><strong>Assistant:</strong> ${data.answer}</p>`;
answer += data.relevant_lessons.map(l => `<a href="${l.url}">${l.title}</a>`).join(', ');
```

**After (safe):**
```js
messages.innerHTML += `<p><strong>You:</strong> ${escapeHtml(query)}</p>`;
messages.innerHTML += `<p><strong>Assistant:</strong> ${escapeHtml(data.answer)}</p>`;
answer += data.relevant_lessons
  .filter(l => isSafeUrl(l.url))
  .map(l => `<a href="${encodeURI(l.url)}">${escapeHtml(l.title)}</a>`)
  .join(', ');
```

## Applicability

This applies to any web UI that displays LLM output — chatbots, code assistants, summarizers, search result snippets. It does NOT apply to server-side rendering where the output is HTML-encoded by the template engine (e.g., Jinja2 auto-escaping, React JSX). The risk is specific to client-side DOM manipulation with `innerHTML`, `document.write`, or jQuery's `.html()`.

## Related Lessons

- [Base URL Misconfiguration Breaks Subdirectory Deploys](base-url-subdirectory-deploys.md) — discovered in the same review-and-fix cycle
- [Structured Code Review as a Phase Gate](structured-review-as-phase-gate.md) — the review process that caught this vulnerability
