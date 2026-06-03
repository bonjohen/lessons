---
phase: implementation
---

# Spreadsheet-to-Code Pipeline for Game Content

## The Lesson

When game content is authored by designers in spreadsheets, build a one-way generator script that converts the spreadsheet into schema-validated data files. The spreadsheet stays authoritative; the generated files are artifacts. This separates content authoring from code and catches errors at generation time, not runtime.

## Context

Corporate Battle Cards has 84 cards defined across two spreadsheet tabs ("Private Faces" for 72 cards, "Public Faces" for 12 cards). Each row has human-readable columns: Cost ("2E 1T"), MinRequirement ("5I"), SustainRequirement ("3T"), EffectSummary ("lose 3 from Economy or 2 from Technology"), and EffectProfile (a canonical string like "choice-pressure" or "pool-attack"). The engine consumes JSON with structured fields (token_cost as `{Pool: int}` dicts, effects as `EffectDef` arrays). The gap between these two representations is where bugs hide.

## What Happened

1. Phase 2 built a JSON loader and schema validator (16 rules) that consumed hand-authored `samplecards.json`. This established the target format and validation expectations.
2. Phase 3.5 introduced `scripts/generate_cards.py`. The script reads the xlsx with openpyxl, parses each text column into structured fields (e.g., "2E 1T" becomes `{"Economy": 2, "Technology": 1}`), and dispatches on the EffectProfile string via match/case to build the effects array.
3. The generator handled 28 distinct EffectProfile types. Each profile maps to a specific combination of verbs, targets, pools, and amounts. The profile string is the contract between designer and generator.
4. On first run, the generator produced 92 cards across 6 JSON files. The existing schema validator caught 0 errors and 20 balance warnings (all expected — 3-pool companies inherently produce less than cost+1).
5. Phase 6.5 overhauled the public market: the spreadsheet's "Public Faces" tab was rewritten from 20 rows to 12. The generator got one new profile (`public-dual-boost`) and five old profiles were removed. Re-running the generator produced correct output without touching the engine.
6. The GTM flavor pass (renaming all 72 private cards' titles and narratives) was a spreadsheet-only edit. Re-running the generator propagated the changes to JSON with zero code modifications.

## Key Insights

- **The EffectProfile string is the key abstraction.** It sits between the designer's intent ("this card attacks a pool") and the engine's data format (a list of EffectDef objects). Without this intermediate label, you'd need the designer to author JSON directly or the generator to guess intent from free-text descriptions.
- **Schema validation at generation time catches errors early.** Running the validator against generated output means the designer sees "card X has invalid pool name" when the generator runs, not when a player draws the card at runtime.
- **One-way generation avoids merge conflicts.** The JSON files are never hand-edited — they're regenerated from the spreadsheet. This eliminates the risk of a hand-edit in JSON diverging from the spreadsheet.
- **Balance warnings are separate from schema errors.** The validator distinguishes hard errors (invalid data) from soft warnings (balance concerns). This prevents balance tuning from blocking content updates.
- **Removing generated artifacts requires test updates.** When `samplecards.json` was deleted in favor of generated files, tests that loaded from that file broke. Tests should use inline fixtures or factory functions, not file paths that may change.

## Examples

Spreadsheet row (simplified):

| FaceID | Cost | Category | EffectProfile | EffectSummary |
|--------|------|----------|---------------|---------------|
| off_lawsuit_01 | 2I | Influence | choice-pressure | lose 3E or 2T |

Generator output:

```json
{
  "id": "off_lawsuit_01",
  "type": "offense",
  "token_cost": {"Influence": 2},
  "category": ["Influence"],
  "effects": [
    {
      "verb": "lose",
      "target": "opponent",
      "choices": [
        {"pool": "Economy", "amount": 3},
        {"pool": "Technology", "amount": 2}
      ]
    }
  ]
}
```

The generator's match/case for `choice-pressure` produces the choices array from the EffectSummary column.

## Applicability

This pattern applies wherever non-engineers author structured data: game card sets, quiz/exam question banks, product catalogs with computed fields, configuration spreadsheets for infrastructure. It does NOT apply when the data is purely machine-generated (no human authoring step) or when the schema changes so rapidly that a generator can't keep up.

## Related Lessons

- [Data-Driven Game Design with a Verb Grammar](data-driven-game-design-with-verb-grammar.md) — The verb grammar defines the target format that the generator must produce.
- [Simulation as Acceptance Test](simulation-as-acceptance-test.md) — Generated card data is validated not just by schema checks but by running full games through the engine.
