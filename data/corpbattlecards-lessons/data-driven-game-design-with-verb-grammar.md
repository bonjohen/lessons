---
phase: implementation
---

# Data-Driven Game Design with a Verb Grammar

## The Lesson

Define a small, fixed grammar of mechanical verbs and make every game effect a data declaration using those verbs. This keeps the engine small and testable while allowing card variety to scale independently of code complexity.

## Context

Corporate Battle Cards is a multiplayer card game with 84 cards spanning 5 types (company, upgrade, offense, defense, public). Each card has effects that modify token pools, attach to companies, cancel other effects, or trigger conditional outcomes. The design doc specified 16 verbs (gain, lose, transfer, convert, disable, deactivate, attach, cancel, reduce, increase, lock, unlock, copy, expose, reveal, merge) as the complete effect vocabulary. The risk was that each new card would require custom resolver code, turning the engine into a sprawl of special cases.

## What Happened

1. Phase 1 defined `EffectDef` as a frozen dataclass with fields for verb, target, pool, amount, duration, timing, choices, and target filter. Every effect is a data record, not a behavior.
2. Phase 4 implemented 11 verb resolvers as pure functions (`resolve_gain`, `resolve_lose`, `resolve_transfer`, etc.) registered in a `VERB_RESOLVERS` dispatch dict. Adding a verb means writing one function and one dict entry.
3. The 11-step attack resolution pipeline in `combat.py` calls verb resolvers by name from the card's effect data. It never inspects card IDs or names — it only reads the verb and parameters.
4. Phase 3.5 generated 92 cards from a spreadsheet. The generator mapped 28 human-readable "EffectProfile" strings (like "pool-attack", "choice-pressure", "sustain-pressure") to combinations of the 16 verbs. All 92 cards loaded through the existing resolver pipeline with zero engine changes.
5. Phase 6.5 overhauled the public market from 20 single-effect cards to 12 multi-effect cards (two `increase` + one `reduce` per card). The engine handled this without modification because multi-effect cards were already just lists of `EffectDef` records.
6. By Phase 10, the engine had 11 resolvers handling all 84 cards across 28 effect profiles, with 252 passing tests. No card-specific logic existed anywhere in the engine.

## Key Insights

- **Verbs are the API contract between content and engine.** When a game designer adds a new card, they compose from existing verbs. When an engineer adds a new verb, they write one resolver. Neither side touches the other's code.
- **Frozen dataclasses enforce the data-not-behavior boundary.** Making `EffectDef` frozen means effects can't accumulate runtime state or grow custom methods. The resolver is always external to the data.
- **A dispatch dict beats a match/case chain.** `VERB_RESOLVERS[effect.verb](state, effect, player_idx)` is one line. A 16-branch match statement would be 50+ lines and grow with every verb.
- **Multi-effect cards are free.** Because effects are a list on the card definition, cards with 1 effect and cards with 3 effects use the same resolution loop. The Phase 6.5 public market overhaul (single-effect to triple-effect) required zero engine changes.
- **The grammar should be smaller than you think.** 16 verbs was the design doc spec. Only 11 were needed for v1. Starting small forces card designers to compose rather than invent, which keeps the system predictable.

## Examples

A "choice-pressure" offense card that forces the opponent to lose from one of two pools:

```python
EffectDef(
    verb=Verb.LOSE,
    target=TargetType.OPPONENT,
    choices=[
        ChoiceOption(pool=Pool.ECONOMY, amount=3),
        ChoiceOption(pool=Pool.TECHNOLOGY, amount=2),
    ],
    timing=Timing.IMMEDIATE,
    duration=Duration.INSTANT,
    reaction_window=True,
)
```

A multi-effect public market card (two boosts, one penalty):

```python
[
    EffectDef(verb=Verb.INCREASE, pool=Pool.TECHNOLOGY, amount=2, ...),
    EffectDef(verb=Verb.INCREASE, pool=Pool.ECONOMY, amount=2, ...),
    EffectDef(verb=Verb.REDUCE, pool=Pool.REPUTATION, amount=3, ...),
]
```

Both resolve through the same `VERB_RESOLVERS` dispatch — no special cases.

## Applicability

This pattern applies to any system where content variety outpaces engineering capacity: card games, RPG skill systems, workflow automation engines, form builders, rule engines. It does NOT apply when effects have genuinely unique mechanics that can't be decomposed into a grammar (e.g., physics simulations, free-form AI behaviors).

## Related Lessons

- [Spreadsheet-to-Code Pipeline for Game Content](spreadsheet-to-code-pipeline-for-game-content.md) — The verb grammar is what makes the pipeline possible; without it, each spreadsheet row would need custom code.
- [Simulation as Acceptance Test](simulation-as-acceptance-test.md) — The grammar's correctness is validated by running 100 AI-vs-AI games through the full resolver pipeline.
