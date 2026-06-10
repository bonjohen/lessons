---
title: Structured Commits as Lesson Inputs
summary: Commit messages with What/Why/Learned sections capture reusable insights at the moment of discovery, feeding downstream lesson extraction pipelines
date: 2026-06-06
phase: execution
lesson_type: process
status: active
tags: [git, process, knowledge-management, automation, lessons]
---

# Structured Commits as Lesson Inputs

## The Lesson

Commit messages are the cheapest place to capture engineering lessons because they happen at the exact moment of discovery — when the problem, root cause, and fix are all in working memory. Adding a structured "What we learned" section to commit messages creates a pipeline of lesson candidates that can be harvested, ranked, and refined into standalone lessons with minimal effort.

## Context

A lessons-learned knowledge base harvests markdown lesson files from multiple GitHub repositories. Lessons are written manually after the fact, which introduces two problems: (1) the insight has decayed — you remember *what* you did but not *why* that approach won over alternatives, and (2) writing a lesson is a separate task that competes with feature work for attention. Meanwhile, every commit already requires a message, and the developer (or AI assistant) who writes the message has full context on what went wrong and what was learned.

## What Happened

1. A date inference bug surfaced where all harvested lessons showed today's date. The root cause was that `infer_date_from_file()` used filesystem mtime, which is set to clone time for cloned repos.
2. The fix was straightforward — use `git log` instead of `stat()` — but the original commit message was a single line: `fix: use git commit date instead of filesystem mtime for lesson date inference`. The *what* was clear; the *why* and the reusable insight (filesystem metadata is unreliable in clone-based workflows) were lost.
3. This pattern repeated across the project's history. Good engineering decisions were buried in diffs with minimal commit messages, making lesson extraction harder.
4. A structured commit template was introduced with three sections: **What changed** (factual), **Why** (motivation), and **What we learned** (reusable insight). The third section maps directly to the "Key Insights" section of a lesson document.
5. Three implementation options were evaluated:
   - `.gitmessage` (git's `commit.template` config) — only works when git opens an editor, not with `git commit -m`
   - `commit-msg` hook — could validate structure, but the message author is the one who needs guidance, not enforcement
   - Feedback memory + versioned template doc — *assumed* to govern the AI assistant's behavior directly, since that is where the messages originate (this assumption proved wrong — see step 6)
6. The feedback memory approach was chosen first — the template rules were written into a persistent auto-memory file the assistant loads every session. **This failed to install the behavior.** Auto-memory is surfaced to the assistant as *background context* ("here is something that may be relevant"), not as an authoritative directive. The format was followed inconsistently, and plain one-line commits still slipped through — the very problem the template was meant to solve. The rule was "written down" but not "installed."
7. The corrected installation used two layers. (a) The rule was promoted into the **global instruction file** (`~/.claude/CLAUDE.md`), which every session in every project loads as an authoritative, override-level instruction — so the behavior applies everywhere, not just one project, and is treated as a directive rather than a hint. (b) A **`PostToolUse(Bash)` validation hook** was added as a safety net: it inspects each commit after the fact and prompts the assistant to amend when required sections are missing.
8. The hook had to be `PostToolUse`, not `PreToolUse`. The commit message does not exist until `git commit` runs, and with `git commit -F -` (heredoc) the message is not even present in the command string for a pre-hook to read. The robust check ignores the command entirely and reads the resulting `HEAD` message via `git log -1 --pretty=%B` *after* the commit — which works identically for `-m`, `-F -`, and `-F <file>`.

## Key Insights

- **Capture lessons at the point of discovery, not after.** The moment you understand a root cause is the moment to write down the reusable principle. Deferring to a separate "write lessons" task loses the nuance of *why* one approach won over alternatives. Commit messages are a natural capture point because they're already mandatory.

- **Structure enables automation; prose does not.** A commit message with labeled sections (What changed / Why / What we learned) is parseable by a harvester. A freeform paragraph with the same information is not. The structure costs the author almost nothing but makes downstream extraction dramatically easier.

- **The right enforcement mechanism depends on who writes the message.** `.gitmessage` and `commit-msg` hooks are designed for human developers using git interactively. When an AI assistant generates commit messages programmatically via `git commit -m`, the effective enforcement mechanism is the assistant's instruction set (memory/prompts), not git's hook system.

- **Auto-memory is the wrong layer for must-follow behavior.** Persistent memory/notes files are surfaced to an assistant as *background context* — they answer "what might be relevant here?" not "what must you do?" A rule that must be obeyed every time belongs in the authoritative instruction file (for Claude Code, a `CLAUDE.md`), not in memory. We learned this the expensive way: the format lived only in memory and was therefore "installed" in name but not in effect. The first sign that a rule is in the wrong layer is that it's followed *sometimes*.

- **Global behavior belongs in the global instruction file, not duplicated per project.** When a rule should hold everywhere, put it once in the global instruction file (`~/.claude/CLAUDE.md`, loaded in every project) and reduce per-project copies to a one-line pointer. Two divergent copies drift; one global source with pointers does not.

- **A commit-message validator must run *after* the commit and read the result, not parse the command.** The message isn't known until `git commit` executes, and heredoc/`-F -` input never appears in the command string — so a pre-commit/pre-tool hook can't see it. Reading `HEAD` (`git log -1 --pretty=%B`) post-commit handles `-m`, `-F -`, and `-F <file>` uniformly. Because the commit has already happened, post-hoc validation can only *warn* and prompt an amend — not block. Design it to warn-and-amend, fail safe on any error, and guard against stale `HEAD` (a failed "nothing to commit" leaves the previous commit at `HEAD`).

- **Not every commit has a lesson.** Formatting fixes, renames, and dependency bumps don't produce reusable insights. The template explicitly allows minimal messages for mechanical changes. Forcing structure on trivial commits creates noise that degrades the signal in the lesson pipeline.

## Examples

**Before (typical commit message):**
```
fix: use git commit date for lesson date inference
```

**After (structured commit message):**
```
fix: use git commit date instead of filesystem mtime for lesson date inference

What changed: infer_date_from_file() now runs git log to get the last
commit date before falling back to filesystem mtime. Corrected hardcoded
dates for gtmleads and data-readiness virtual lesson files.

Why: The harvester stamped all cloned-repo lessons with today's date
because git clone sets every file's mtime to the clone time.

What we learned: Filesystem metadata is unreliable for provenance in any
workflow that involves cloning or regenerating files. Git log is the
authoritative source for "when was this file last meaningfully changed."
```

## Implementation Guide

### Step 1: Define the commit message template

The template needs three things: the structure, guidelines for each section, and rules for when to skip sections. Here is the full template:

```
<type>: <short summary>

What changed: <factual description — name the files, functions, and
behavior changes. Describe what's different, not line-level diffs.>

Why: <the problem, constraint, or request that motivated the change.
If a bug: symptom and root cause. If a feature: the gap it fills.>

What we learned: <reusable principle, framed for someone facing a
similar situation in a different project. Not a restatement of the
diff — the insight that would save someone else time.>
```

**Type prefixes:** `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:` (conventional commits).

**Section guidelines:**

- **What changed** — factual, concise. Name the files and functions affected. Describe behavior changes, not line-level diffs (the diff itself does that).
- **Why** — state the problem, constraint, or user request that motivated the change. If a bug, describe the symptom and root cause. If a feature, describe the gap it fills.
- **What we learned** — frame as a reusable principle, not a project-specific fact. Good: "Filesystem mtime is unreliable for date inference in cloned repos because git clone sets all mtimes to the clone time." Bad: "Fixed the date bug." If the change is purely mechanical (formatting, renames), this section can be omitted.

**When to omit sections:**

- **Style/format commits**: type + summary line is sufficient. Omit all sections.
- **Trivial fixes**: type + summary + one-line Why. Omit What we learned if there's nothing reusable.
- **Feature/fix/refactor commits**: all three sections expected.

### Step 2: Choose an enforcement mechanism

The right mechanism depends on who writes the commit messages. **The distinction that matters most is authoritative *instruction* vs. passive *context*.** A rule that must be followed every time has to live where the author treats it as a directive — for an AI assistant, that is its instruction file, not a memory/notes file.

| Scenario | Mechanism | How it works |
|----------|-----------|--------------|
| Human developers using `git commit` (editor) | `.gitmessage` template | `git config commit.template .gitmessage` pre-fills the editor. Passive — easy to ignore, and does nothing for `git commit -m`. |
| Human developers using `git commit -m` | `commit-msg` git hook | A script in `.git/hooks/commit-msg` validates structure and rejects non-conforming commits. Active, but per-repo and aimed at humans. |
| **AI assistant generating messages via `-m`/`-F`** | **Authoritative instruction file + post-commit validator** | Put the rule in the assistant's instruction file (`CLAUDE.md`) so it is a directive on every turn; add a `PostToolUse` hook that checks each commit and prompts an amend when sections are missing. |
| Team with mixed workflows | Combination | `.gitmessage` for editor users + `commit-msg` git hook for validation + the assistant rule above for AI-authored commits. |

> **Failure mode this step exists to prevent.** The first attempt put the rule only in the assistant's *auto-memory*. It did not stick: memory is surfaced as background context, not a directive, so the format was applied inconsistently. The fix was to (1) move the rule into the **global instruction file** and (2) add a **post-commit validation hook**. "Wrote it down somewhere the assistant can see" is not the same as "installed as required behavior." The instructions below are deliberately precise because vagueness here is what caused the miss.

**Setting up `.gitmessage` (for human developers):**

```bash
# Create the template file at the repo root
cat > .gitmessage << 'EOF'
# <type>: <short summary>
#
# What changed:
#
# Why:
#
# What we learned:
#
# Types: feat, fix, docs, style, refactor, test, chore
# Omit "What we learned" for mechanical changes (format, rename, deps)
EOF

# Configure git to use it
git config commit.template .gitmessage
```

**Setting up a `commit-msg` hook (for enforcement):**

```bash
cat > .git/hooks/commit-msg << 'HOOK'
#!/bin/bash
# Reject non-trivial commits that lack the "Why:" section
msg=$(cat "$1")
type=$(echo "$msg" | head -1 | grep -oP '^(feat|fix|refactor|test|docs):')

# Style/chore commits are exempt
if echo "$msg" | head -1 | grep -qP '^(style|chore):'; then
  exit 0
fi

# Feature, fix, and refactor commits must have a Why section
if [ -n "$type" ] && ! echo "$msg" | grep -q "^Why:"; then
  echo "ERROR: $type commits require a 'Why:' section."
  echo "Add 'Why: <motivation>' to your commit message."
  exit 1
fi
HOOK
chmod +x .git/hooks/commit-msg
```

**Setting up a persistent AI instruction (for Claude Code):**

Claude Code (Anthropic's AI coding assistant) uses two files to govern behavior: a **CLAUDE.md** project instruction file and an optional **memory file**. CLAUDE.md is a markdown file checked into the repo root that the assistant reads at the start of every session — it contains project-specific rules, conventions, and instructions that shape how the assistant works. Memory files are per-project persistent notes stored outside the repo that carry preferences and feedback across sessions. Either can carry commit template rules. CLAUDE.md is better for team-wide enforcement (it's in version control); memory is better for personal workflow preferences.

**Option A: Add to a CLAUDE.md instruction file (the load-bearing install).** Put the full template and rules inline in a `CLAUDE.md`. Because `CLAUDE.md` is loaded automatically at the start of every session as an *authoritative instruction*, the assistant follows it without any extra setup. **Scope matters:** use the *project* `CLAUDE.md` for one repo, or the *global* `~/.claude/CLAUDE.md` to apply the rule to every existing and new project. For a behavior that should hold everywhere, install it globally and reduce per-project copies to a one-line pointer (this avoids divergent duplicates that drift apart):

```markdown
## Commit Message Format

All non-trivial commits must use this structure:

\`\`\`
<type>: <short summary>

What changed: <factual — name files, functions, behavior changes>

Why: <the problem, constraint, or request that motivated this>

What we learned: <reusable principle framed for someone in a different
project — not a restatement of the diff>
\`\`\`

Type prefixes: feat, fix, docs, style, refactor, test, chore.

Rules:
- Style/chore commits: summary line only. Omit all sections.
- Trivial fixes: summary + one-line Why. Omit What we learned.
- Feature/fix/refactor: all three sections required.
- "What we learned" must be a reusable insight, not a project fact.
  Good: "Filesystem mtime is unreliable in clone-based workflows
  because git clone sets all mtimes to the clone time."
  Bad: "Fixed the date bug."
- Always end with the co-author trailer.
```

**Option B: Feedback memory file — supplementary only, NOT for must-follow rules.** ⚠️ This is the option that failed for us. Claude Code's auto-memory (`~/.claude/projects/<project>/memory/`) is surfaced to the assistant as *background context*, not as an authoritative instruction — so a rule placed only here is applied inconsistently. Use memory to *reinforce* a rule that already lives in an instruction file (Option A), never as the sole home of a must-follow behavior. If you do use it as reinforcement, make the entry self-contained:

```markdown
---
name: Structured commit messages for lesson extraction
description: Every non-trivial commit uses What changed / Why / What
  we learned sections to feed the lesson extraction pipeline
type: feedback
---

All non-trivial commits must use this three-section format:

  <type>: <short summary>

  What changed: <factual — name files, functions, behavior changes>

  Why: <the problem, constraint, or request that motivated this>

  What we learned: <reusable principle framed for someone in a
  different project — not a restatement of the diff>

Type prefixes: feat, fix, docs, style, refactor, test, chore.

Rules:
- Style/chore commits: summary line only. Omit all sections.
- Trivial fixes: summary + one-line Why. Omit What we learned.
- Feature/fix/refactor: all three sections required.
- "What we learned" must be a reusable insight, not a project fact.
  Good: "Filesystem mtime is unreliable in clone-based workflows
  because git clone sets all mtimes to the clone time."
  Bad: "Fixed the date bug."

**Why this rule exists:** Richer commit messages serve as raw material
for lesson extraction. The "What we learned" section maps directly to
lesson content and captures insight in the moment, which is hard to
reconstruct later.
```

Then add a one-line pointer in `MEMORY.md` (the memory index that loads every session):

```markdown
- [Structured commit messages](feedback_commit_template.md) — What changed / Why / What we learned on every non-trivial commit
```

The key is that the memory file is **self-contained** — it includes the full format, rules, and examples so the assistant never needs to look up an external reference to follow it.

**Option C: Add a Claude Code validation hook (the safety net).** Claude Code hooks are commands that run automatically around tool calls, configured in a JSON settings file. This is the catch-net for when the assistant forgets the instruction. The instructions below are the exact, working setup — the earlier version of this lesson described this option vaguely (it named a script that was never provided), which is part of why the format wasn't reliably enforced.

**Why `PostToolUse`, not `PreToolUse`.** The commit message does not exist until `git commit` runs, and with `git commit -F -` (heredoc) the message never appears in the command string a pre-hook would inspect. So the hook fires *after* the Bash tool call and reads the resulting commit. Because the commit has already happened, the hook can only *warn* (exit code 2 surfaces the message back to the assistant so it can amend) — it cannot block. That is the honest scope of post-hoc validation.

**Step C1 — write the hook script** at `~/.claude/hooks/check-commit-msg.py`. It reads `HEAD` rather than parsing the command, so it handles `-m`, `-F -`, and `-F <file>` identically; guards against stale `HEAD` (a failed "nothing to commit" leaves the prior commit in place); and fails safe (any error exits 0, never blocking work):

```python
#!/usr/bin/env python3
"""PostToolUse(Bash) hook — structured-commit-message validator.
Warns (does not block) when a non-trivial `git commit` produces a HEAD
message missing the required sections. Reads HEAD so it works for -m,
-F -, and -F <file> uniformly. Fails safe: any error exits 0."""
import json, re, subprocess, sys, time

# type -> (needs_why, needs_learned)
ENFORCE = {"feat": (True, True), "refactor": (True, True),
           "perf": (True, True), "fix": (True, False)}
STALE_SECONDS = 180

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, timeout=5).stdout

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not re.search(r"\bgit\b[^|;&]*\bcommit\b", cmd):
        return 0
    if re.search(r"--dry-run|--amend|--no-edit", cmd):
        return 0
    # Resolve repo dir: honor `git -C <dir>`, else the hook's cwd.
    repo = data.get("cwd") or "."
    m = re.search(r"-C\s+(\"[^\"]+\"|'[^']+'|\S+)", cmd)
    if m:
        repo = m.group(1).strip("\"'")
    try:
        msg = git(repo, "log", "-1", "--pretty=%B")
        ts = git(repo, "log", "-1", "--pretty=%ct").strip()
    except Exception:
        return 0
    if not msg.strip() or not ts.isdigit():
        return 0
    if time.time() - int(ts) > STALE_SECONDS:   # HEAD wasn't just created
        return 0
    first = msg.strip().splitlines()[0]
    tm = re.match(r"^([a-z]+)(\([^)]*\))?!?:", first)
    if not tm or tm.group(1) not in ENFORCE:     # style/chore/docs/etc. exempt
        return 0
    needs_why, needs_learned = ENFORCE[tm.group(1)]
    missing = []
    if needs_why and not re.search(r"(?im)^\s*Why:", msg):
        missing.append("Why:")
    if needs_learned and not re.search(r"(?im)^\s*What we learned:", msg):
        missing.append("What we learned:")
    if not missing:
        return 0
    sys.stderr.write(
        f"Structured-commit reminder: the last commit ({tm.group(1)}:) is "
        f"missing section(s): {', '.join(missing)}. If this was a genuinely "
        f"trivial change, ignore; otherwise amend the commit message.\n"
        f"Subject was: {first}\n")
    return 2

if __name__ == "__main__":
    sys.exit(main())
```

**Step C2 — register it** in the settings file (global: `~/.claude/settings.json`; per-project: `.claude/settings.json`). Merge into any existing `hooks` object; don't overwrite it:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command",
            "command": "python \"C:/Users/<you>/.claude/hooks/check-commit-msg.py\"" }
        ]
      }
    ]
  }
}
```

`settings.json` changes are read at session start — a new session (or resume) is needed before the hook is active.

**Step C3 — test it before trusting it.** Feed the hook a synthetic payload on stdin and check the exit code. A non-compliant `feat` must exit 2; a compliant one and a `chore` must exit 0:

```bash
T="C:/Users/<you>/AppData/Local/Temp/hooktest"; rm -rf "$T"; mkdir -p "$T"
git -C "$T" init -q && git -C "$T" -c user.email=t@t -c user.name=t commit -q --allow-empty -m "feat: x"
printf '{"tool_name":"Bash","cwd":"%s","tool_input":{"command":"git commit -m x"}}' "$T" \
  | python "C:/Users/<you>/.claude/hooks/check-commit-msg.py"; echo "exit=$?"   # expect exit=2
```

> **Windows gotcha (cost us a debugging cycle).** The repo path passed to the hook must be a form the Windows `python`/`git` can resolve (forward-slash `C:/...` is fine). An MSYS-style path like `/tmp/...` from `mktemp -d` will make `git -C` fail, the hook will fail safe to exit 0, and the test will look like a false pass. If a test "passes" silently when you expected a warning, suspect the path before the logic.

**Which option to pick:**

- AI-authored commits, any project → **Option A in the *global* instruction file** (`~/.claude/CLAUDE.md`), so the rule applies everywhere. This is the load-bearing install; without it nothing else reliably fires.
- Want a safety net against the assistant forgetting → **add Option C** (post-commit validator). **A + C is the recommended pairing** for "this must happen every time."
- Reinforcement only → Option B, *in addition to* A — never as the sole mechanism. (Putting the rule only here is the mistake that caused the original miss.)
- Not using Claude Code (human authors) → `.gitmessage` + `commit-msg` git hook from the top of this step.

### Step 3: Wire commits into your knowledge pipeline

Structured commit messages are only valuable if something downstream consumes them. Options, from simplest to most sophisticated:

**Manual review (no tooling required):** Periodically run `git log --format='%B---' | grep -B5 "What we learned"` to scan recent insights. Copy promising ones into lesson documents.

**Automated candidate extraction:** Write a script that parses commit messages, extracts "What we learned" sections, and writes them to a candidates file:

```python
import subprocess, re

log = subprocess.run(
    ["git", "log", "--format=%H|%ai|%B|||"],
    capture_output=True, text=True
).stdout

for entry in log.split("|||"):
    match = re.search(r"What we learned:\s*(.+?)(?:\n\n|$)", entry, re.DOTALL)
    if match:
        lines = entry.strip().split("|")
        print(f"- [{lines[1][:10]}] {match.group(1).strip()[:200]}")
```

**Full pipeline integration:** If you have a lesson harvester (like this project's `harvest_lessons.py`), add a stage that reads commit history, extracts structured messages, scores them by novelty, and generates draft lesson files. The "What we learned" section becomes the lesson's core insight; the "Why" section becomes the Context; the "What changed" section maps to "What Happened."

### Step 4: Iterate on the template

After a few weeks of use, review the commit history:

- Are "What we learned" sections mostly restating the diff? → Add more good/bad examples to the template.
- Are too many trivial commits getting full treatment? → Tighten the "when to omit" rules.
- Are insights too project-specific? → Add guidance on framing for a general audience.
- Is the template being ignored? → Switch from passive (`.gitmessage`) to active enforcement (hook or CI check).

The template is a living document. Version it in the repo so changes are tracked and the team can discuss improvements via PR review.

## Applicability

This pattern applies to any project that extracts knowledge artifacts from development history — changelogs, postmortems, onboarding guides, architecture decision records. The key requirement is that someone (human or AI) is already writing commit messages and can add 2-3 sentences of structured context at negligible marginal cost.

It does NOT apply when commit messages are squash-merged away, when the team uses "fixup" commits extensively, or when the lesson extraction pipeline doesn't exist yet (build the pipeline first, then optimize its inputs).

## Related Lessons

- [Skill-Driven Workflow Automation](skill-driven-workflow-automation.md) — the `/push` skill that executes commits is the natural place to enforce the template
- [Code Review as Requirements Source](code-review-as-requirements-source.md) — another pattern for extracting knowledge from development artifacts
