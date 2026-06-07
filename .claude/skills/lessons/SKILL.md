---
name: lessons
description: Discover, write, list, audit, or repair lessons-learned documents extracted from project work. Mines git history, design docs, plans, and code reviews to identify reusable patterns and mistakes. Each lesson is a standalone document useful independent of the codebase.
argument-hint: "[write <topic> | list | audit | repair [<file-or-pattern>]]"
---

You are producing **lessons learned** documents — standalone learning resources extracted from real project work. Each lesson captures a pattern, mistake, or decision and is written so a developer on a completely different project can understand and apply it.

## Inputs

The argument `$ARGUMENTS` determines the mode:

| Argument | Mode | Writes files? |
|----------|------|---------------|
| *(empty)* | **Discover** — scan for new lesson candidates | No |
| `write <topic>` | **Author** — write or complete a lesson on `<topic>` | Yes |
| `list` | **Index** — print the current lesson index | No |
| `audit` | **Completeness check** — evaluate all lessons | No |
| `repair [target]` | **Repair** — fill missing sections in existing lessons | Yes |

## Lesson Location

Lessons live at `docs/lessons/` in the current project. This is the default and correct location for project-specific lessons.

- Lesson files: `docs/lessons/slug-title.md`
- Index: `docs/lessons/README.md`
- Template: `docs/lessons/TEMPLATE.md`

If `docs/lessons/` does not exist, create it along with `README.md` and `TEMPLATE.md` before writing any lessons.

For a **cross-project lessons library** shared across all projects, the user may designate a central archive (e.g., `D:/Archive/lessons/`). When a lesson is general enough to be useful beyond its source project, suggest copying it to the archive. Never move — always copy, so the project retains its own record.

## Mode: Discover (no argument)

1. Read `docs/lessons/README.md` to know what lessons already exist.
2. Scan for new lesson candidates:
   - `git log --oneline` — look for bug fixes, migrations, refactors, scaling events, remediation phases, audit+fix cycles, security fixes, design system work, test infrastructure, schema work
   - `docs/` — design docs, PDRs, plans, review results, audit reports
   - Multi-commit sequences that tell a story (phased work, iterative improvement)
3. For each candidate, check whether an existing lesson already covers it.
4. Present new candidates as a numbered list with proposed titles and one-line descriptions.
5. **Do not write any files.** Wait for the user to select which lessons to write.

### Discovery Heuristics

| Signal | Example commit pattern | Likely lesson topic |
|--------|----------------------|---------------------|
| Bug fix after a pattern was missed | "Fix XML escape characters..." | Encoding pitfalls, validation gaps |
| Format migration | "Rewire app.js to load JSON..." | Migration strategy, equivalence testing |
| Multi-commit enrichment | "Enrich hints for GCP..." (6x) | Content quality at scale, batch tooling |
| Code review + remediation | "Code review remediation Phase N" | Review-driven improvement |
| Scaling event | "Add CompTIA, ISC2, GitHub..." | Plugin architecture, scaling |
| Design system work | "Port landing page to Atlas..." | Design system migration |
| Audit + fix cycle | "Fix H1 answer giveaways..." | Automated quality gates |
| Schema consolidation | "Convert 4 variant-schema..." | Schema drift, data pipelines |
| Security fix | "Add Content Security Policy..." | Security in context |
| Test infrastructure | "Add full-corpus equivalence test" | Testing strategies |

## Mode: Author (`write <topic>`)

1. Read `docs/lessons/TEMPLATE.md` for the section structure.
2. Research the topic thoroughly:
   - Read relevant commits (`git log --stat`, `git show`)
   - Read related docs, plans, review results
   - Read actual code changes when the lesson is about a code decision
3. Choose a descriptive slug for the filename: `slug-title.md` (no numeric prefix).
4. Write the lesson following the template structure below.
5. Add the lesson to `docs/lessons/README.md` under the appropriate category.
6. If the lesson references other existing lessons, add cross-references in both directions.

### Template Structure

Every lesson has these **required** sections:

#### `# [Title]`
Short, descriptive. Not a sentence — a topic label.

#### `## The Lesson`
1-3 sentences stating a general principle. Frame as reusable insight, not project fact.

- Good: "When migrating a data format, the key risk is proving equivalence — not the conversion itself."
- Bad: "We migrated XML to JSON in the certification project."

#### `## Context`
One paragraph. Set the stage for an outsider: what kind of system, what scale, what constraints, why this situation arose. Use concrete numbers but avoid unexplained internal paths or class names.

#### `## What Happened`
4-8 numbered steps. What was tried, in what order, what the outcome was. Include successes and failures. Focus on decisions and consequences, not implementation minutiae.

#### `## Key Insights`
4-6 bulleted observations. Each bullet:
1. Starts with **bold statement** (the insight)
2. Follows with 1-2 sentences of explanation or evidence

Every insight must be actionable — a reader should be able to change their behavior based on it.

And these **optional** sections (include when they add value, omit when they don't):

#### `## Implementation Guide`
Step-by-step instructions for applying this pattern to a new project. Include when the lesson describes a concrete, replicable technique (adapter patterns, search integration, security sanitization, build pipelines). Omit for observational lessons, one-time decisions, or lessons where the insight IS the implementation.

Structure as numbered steps (`### Step 1: ...`), each with:
- What to do and why
- Code snippets, configuration examples, or shell commands
- Key decisions and their trade-offs

**Self-contained rule:** Every concept must be explained inline. Do not reference repo files (e.g. "see `scripts/foo.py`") without explaining what that file does and showing the relevant pattern. Readers cannot access the source repository.

#### `## Examples`
Before/after, good/bad, or worked/failed comparisons. Use simplified/generic versions, not verbatim codebase copies.

#### `## Applicability`
Where else this lesson applies. Boundary conditions — when the advice does NOT apply.

#### `## Related Lessons`
Cross-references: `- [Title](filename.md) — one sentence on the relationship`

## Mode: Index (`list`)

Read and print `docs/lessons/README.md` to the conversation. If the file doesn't exist, say so.

## Mode: Audit (`audit`)

1. Read every `*.md` file in `docs/lessons/` (excluding README.md and TEMPLATE.md).
2. For each file, evaluate against the completeness levels:

| Level | Criteria |
|-------|----------|
| **Draft** | Has The Lesson and Context. Other sections are placeholders or thin. |
| **Partial** | Has all four required sections, but insights lack evidence or examples would help. |
| **Complete** | All required sections are substantive. Optional sections present where they add value. No placeholders remain. |

3. Report a table: `| Filename | Status | Gaps |`
4. **Do not modify any files.** Report only.

## Mode: Repair (`repair [target]`)

Repair fills missing or thin sections in existing lessons. It preserves all existing content and only adds what's missing. This is the write-mode complement to `audit`.

### Target selection

The `target` argument controls scope:

| Target | Scope |
|--------|-------|
| *(empty)* | All lessons with gaps (runs audit internally, then repairs each) |
| `<filename>` | Single file, e.g. `repair bayesian-beta-binomial-smoothing.md` |
| `<glob>` | Pattern, e.g. `repair block2/*` |
| `<section>` | Fix one section type across all lessons, e.g. `repair what-happened` or `repair related-lessons` |

### Workflow

1. **Assess.** Read each target lesson file. Identify which required sections are missing or thin, and which optional sections would add value.
2. **Research.** For each gap, gather the information needed to fill it:
   - **"What Happened" gaps:** Search `git log --all --oneline`, design docs, plan files, and code for the chronological story. Look for the commit(s) that introduced the pattern, any false starts or reverted approaches, and the final resolution. If the project history doesn't contain enough detail to reconstruct the narrative, write a plausible "What Happened" based on the lesson's own Context and Key Insights sections — mark it with a `<!-- reconstructed from context, not git history -->` comment so the author knows to verify.
   - **"Related Lessons" gaps:** Read all other lesson files in the collection. Identify lessons that share a technique, were discovered in the same phase, or represent the same principle applied differently. Write cross-references in both directions (update the related lesson too).
   - **Thin "Key Insights":** Look for concrete evidence (benchmarks, data, error messages) in git history or code that can strengthen vague insights.
3. **Edit.** Insert the missing sections into the lesson file at the correct position in the template order: Title → The Lesson → Context → What Happened → Key Insights → Examples → Applicability → Related Lessons. Never rewrite existing sections — only add new ones or append to thin ones.
4. **Report.** After repairing, print a summary table: `| Filename | Sections Added | Status Before → After |`

### Section ordering rule

When inserting a missing section, place it in template order relative to existing sections: Title → The Lesson → Context → What Happened → Key Insights → Implementation Guide → Examples → Applicability → Related Lessons. If "What Happened" is missing and the file goes `The Lesson → Context → Key Insights`, insert "What Happened" between Context and Key Insights.

### Repair constraints

- **Never rewrite existing content.** Repair only adds. If an existing section is wrong, that's the author's call — flag it in the report but don't change it.
- **Never remove sections.** Even non-standard sections (e.g., "Design Decisions" used in place of "Key Insights") are kept as-is.
- **Reconstructed narratives are marked.** If "What Happened" is reconstructed from context rather than git history, include `<!-- reconstructed -->` so the author can verify or rewrite.
- **Cross-references are bidirectional.** When adding "Related Lessons" to file A pointing to file B, also add the reverse reference to file B.
- **Batch size limit.** When repairing all lessons (no target), process at most 5 files per invocation. Report remaining files as "queued" so the user can run `repair` again. This prevents context exhaustion on large collections.

### Example repair of "What Happened"

If a lesson about Bayesian smoothing has Context explaining the sparse-data problem and Key Insights about Beta(2,8) prior, but no "What Happened," the repair would search git for commits related to batch scoring, find the progression (raw rates → Wilson → Beta-Binomial), and write:

```markdown
## What Happened

1. Initial implementation used raw selection rates (selected / shown). Images shown once and selected once scored 1.0 — higher than genuinely popular images shown 50 times.
2. Added Wilson lower-bound confidence intervals. This penalized low-exposure images but produced a frequentist point estimate, not a full posterior.
3. Switched to Beta-Binomial conjugate model with Beta(2,8) prior. The prior encodes "assume an image is below-average until data says otherwise."
4. Verified that images with 10+ exposures had posteriors dominated by data, while images with 1-2 exposures stayed near the prior mean of 0.20.
5. Kept Wilson lower bound as a secondary metric for comparison, but used posterior mean as the backbone of the composite score.
```

## Quality Standards

### Independence
Each lesson must be readable without codebase access. No unexplained file paths, no bare class/function names. Concrete numbers are good — they ground the lesson in reality.

### Generality
**The Lesson** and **Key Insights** are general principles. **Context** and **What Happened** are where project-specific details live. A reader should get value from just The Lesson + Key Insights.

### Categorization
Group lessons in the README index by domain:
- **Data & Content Quality** — schema, validation, auditing, format migration
- **Architecture & Design** — system design, plugin patterns, design systems, persistence
- **Process & Methodology** — planning, review, workflow, scaling
- **Testing** — test strategies, equivalence, integration, coverage
- **Data Engineering** — encoding, schema management, bulk transformation

Add new categories when 3+ lessons don't fit existing ones.

### Naming
Use descriptive slug filenames without numeric prefixes: `xss-in-llm-chat-interfaces.md`, not `01-xss-in-llm-chat-interfaces.md`. Slugs should be lowercase, hyphenated, and descriptive enough to identify the lesson without opening the file.

## Hard Rules

- **Discover mode never writes files.** It proposes; the user decides.
- **Audit mode never modifies files.** It evaluates and reports.
- **Drafts are acceptable.** A large list of drafts is more valuable than a small list of polished documents. Drafts capture the lesson's existence; details can be filled in later.
- **Lessons are standalone.** If a lesson can't be understood without reading the codebase, it's not done.
- **Never delete lessons.** Mark as superseded or merge into another, but don't remove.

## Relationship to Other Skills and Artifacts

- `/phase` executes plan rows. Lessons are extracted *after* phases complete — reflection on what was learned.
- Design docs and PDRs are forward-looking (what to build). Lessons are backward-looking (what was learned).
- `docs/todo.md` "Resolved Decisions" captures *what* was decided. Lessons capture *why it mattered*.
