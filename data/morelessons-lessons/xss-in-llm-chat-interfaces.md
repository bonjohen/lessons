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

## Implementation Guide

### Step 1: Add an escapeHtml helper

Create a function that converts HTML-special characters to their entity equivalents. The safest approach uses the DOM itself — create an element, set its `textContent` (which escapes automatically), then read back `innerHTML`:

```js
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
```

This handles `<`, `>`, `&`, `"`, and `'` without maintaining a manual replacement map. Use this for every string interpolated into HTML, whether it comes from the user or from an API response.

### Step 2: Add a URL allowlist validator

Block dangerous URL schemes (`javascript:`, `data:`, etc.) by only allowing known-safe prefixes. An allowlist is safer than a blocklist because new URI schemes get added to browsers over time:

```js
function isSafeUrl(url) {
  if (typeof url !== "string") return false;
  return url.startsWith("/") || url.startsWith("https://") || url.startsWith("http://");
}
```

Apply this before rendering any URL from an API response as an `href`. Also apply `encodeURI()` to the URL value to handle special characters.

### Step 3: Apply sanitization to all dynamic content insertion

Audit every place your code inserts dynamic content into the DOM. Search for these patterns:

```bash
grep -rn "innerHTML\|\.html(\|document\.write\|insertAdjacentHTML" src/
```

For each match, apply the appropriate fix:

- **Plain text display** (messages, titles): use `escapeHtml()` or `element.textContent = value`
- **Rich text display** (markdown rendering): use a sanitization library like DOMPurify or sanitize-html
- **Link hrefs**: validate with `isSafeUrl()` and encode with `encodeURI()`

```js
// Chat message rendering — sanitize both user and LLM text
messages.innerHTML += `<p><strong>You:</strong> ${escapeHtml(query)}</p>`;
messages.innerHTML += `<p><strong>Assistant:</strong> ${escapeHtml(data.answer)}</p>`;

// Citation links — validate URL and escape title
const safeLinks = data.citations
  .filter(c => isSafeUrl(c.url))
  .map(c => `<a href="${encodeURI(c.url)}">${escapeHtml(c.title)}</a>`)
  .join(", ");
```

### Step 4: Add a grep-based audit to your CI or preflight checks

Prevent regressions by flagging raw `innerHTML` usage in CI. Add a check that fails if `innerHTML` is used without a sanitizer in the same file:

```bash
# Flag files that use innerHTML but don't import/define a sanitizer
for file in $(grep -rl "innerHTML" src/); do
  if ! grep -q "escapeHtml\|sanitize\|DOMPurify\|textContent" "$file"; then
    echo "WARNING: $file uses innerHTML without sanitization"
  fi
done
```

This won't catch every case, but it catches the most common one — adding `innerHTML` during a quick feature build without thinking about sanitization.

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
