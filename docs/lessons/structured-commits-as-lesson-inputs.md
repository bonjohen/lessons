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
   - Feedback memory + versioned template doc — governs the AI assistant's behavior directly, which is where the messages originate
6. The feedback memory approach was chosen because it matches the actual mechanism: the template rules live in a persistent memory file that the assistant loads every session, ensuring it follows the format on every commit without needing to look up an external reference.

## Key Insights

- **Capture lessons at the point of discovery, not after.** The moment you understand a root cause is the moment to write down the reusable principle. Deferring to a separate "write lessons" task loses the nuance of *why* one approach won over alternatives. Commit messages are a natural capture point because they're already mandatory.

- **Structure enables automation; prose does not.** A commit message with labeled sections (What changed / Why / What we learned) is parseable by a harvester. A freeform paragraph with the same information is not. The structure costs the author almost nothing but makes downstream extraction dramatically easier.

- **The right enforcement mechanism depends on who writes the message.** `.gitmessage` and `commit-msg` hooks are designed for human developers using git interactively. When an AI assistant generates commit messages programmatically via `git commit -m`, the effective enforcement mechanism is the assistant's instruction set (memory/prompts), not git's hook system.

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

The right mechanism depends on who writes the commit messages:

| Scenario | Mechanism | How it works |
|----------|-----------|--------------|
| Human developers using `git commit` (editor) | `.gitmessage` template | Set `git config commit.template .gitmessage`. Git pre-fills the editor with the template. Passive — easy to ignore. |
| Human developers using `git commit -m` | `commit-msg` hook | A script in `.git/hooks/commit-msg` validates the message structure and rejects commits that don't match. Active enforcement. |
| AI assistant generating messages via `-m` | Persistent instruction (memory/prompt) | The assistant's instruction set includes the template as a behavioral rule. The template doc is the reference; the instruction ensures it's followed. |
| Team with mixed workflows | Combination | `.gitmessage` for editor users + `commit-msg` hook for validation + CI check for messages that slip through. |

For AI-assisted workflows, the persistent instruction approach is simplest and most effective. The assistant reads the template doc and follows it — no hook infrastructure needed.

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

**Option A: Add to CLAUDE.md (recommended for teams).** Add a section to your project's CLAUDE.md with the full template and rules inline. Because CLAUDE.md is loaded automatically at the start of every session, the assistant will follow these rules without any additional setup:

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

**Option B: Use a feedback memory file.** If you use Claude Code's auto-memory system (`~/.claude/projects/<project>/memory/`), create a memory file with the full rules inline. The memory file must include enough detail that the assistant can follow the template without reading any other file:

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

**Option C: Use a Claude Code hook (for validation).** Claude Code supports hooks — shell commands that run automatically before or after specific tool calls (like running a bash command). Hooks are configured in a JSON settings file. To enforce commit message format, add a `PostToolUse` hook that fires after every bash command. The hook script checks if the command was a `git commit`, and if so, inspects the message for required sections:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/check-commit-msg.py"
          }
        ]
      }
    ]
  }
}
```

The hook script receives the tool call details on stdin as JSON, extracts the bash command, checks if it matches `git commit`, and warns (but doesn't block) if the message lacks `Why:` or `What we learned:` sections. This is heavier to set up but catches cases where the assistant forgets the template.

**Which option to pick:**

- Starting from scratch → Option A. One file, no infrastructure, works immediately.
- Already using Claude Code memory → Option B. Keeps CLAUDE.md clean; template lives in a dedicated doc.
- Team environment where enforcement matters → Options A + C. Instructions plus validation.
- Not using Claude Code → Skip all of these and use `.gitmessage` + `commit-msg` hook above.

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
