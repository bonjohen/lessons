---
phase: execution
---

# Simulation as Acceptance Test

## The Lesson

For games and complex interactive systems, unit tests verify correctness but batch simulation verifies balance. Run N automated games, record metrics, and treat the first run's numbers as a baseline. Future changes must either match the baseline or explain the deviation.

## Context

Corporate Battle Cards has an AI opponent that can play complete games autonomously. The engine has 252 unit tests covering individual mechanics (token arithmetic, sustain checks, attack resolution, etc.). But unit tests can't answer "do games take a reasonable number of turns?" or "does the first player win too often?" — those are emergent properties of all mechanics interacting. The project needed a way to detect balance regressions when engine code or card data changed.

## What Happened

1. Phase 7 built `simulate/runner.py` (headless AI-vs-AI game runner), `simulate/metrics.py` (7 tracked metrics), and a CLI (`python -m corpbattlecards.simulate --games 100 --seed 42`).
2. The first 100-game run established the baseline: 11.9 average turns, 57% strategic dominance / 43% total dominance wins, 41% first-player win rate, economy pool starving 963 times, average company lifespan 2.0 turns, 76% runaway rate (60+ tokens by turn 10).
3. Phase 6.5 overhauled the public market (20 single-effect cards to 12 multi-effect cards with +2/+2/-3 patterns) and renamed all 72 private cards. This was a major content change.
4. After Phase 6.5, the simulation was re-run. Metrics matched the baseline exactly — the public market overhaul didn't affect game balance because the net token impact per public card was preserved (+2+2-3 = +1 per card, same as the old single-pool cards).
5. Phase 10 acceptance testing re-ran the simulation as a formal gate. Identical metrics confirmed no regressions across Phases 8-9 (UI implementation), which shouldn't affect engine behavior but could have introduced subtle state mutations.
6. Deterministic replay (same seed = same result) was verified both in unit tests and via the simulation CLI. This ensures that when a metric deviates, the exact game can be replayed for debugging.

## Key Insights

- **Simulation metrics are emergent, not derivable.** You can't calculate the first-player win rate from the rules alone — it emerges from the interaction of counter-wheel modifiers, AI scoring weights, card distribution, and production mechanics. Only simulation reveals it.
- **Identical metrics after a change is the strongest evidence of no regression.** When Phase 6.5 changed 84 cards and Phase 10 got identical numbers, that proved the engine was unaffected. A "tests pass" result wouldn't have given that confidence.
- **The baseline must be established before changes, not after.** Phase 7 ran the simulation before Phases 8-10. If the baseline had been set after all changes, there would be nothing to compare against.
- **Runaway detection surfaces balance problems that averages hide.** The 76% runaway rate (60+ tokens by turn 10) reveals that most games snowball quickly. The 11.9 average turn count looks reasonable, but the runaway rate says games are often decided early. Both numbers together tell a richer story.
- **Seeded determinism makes simulation debugging tractable.** When a specific game produces an anomaly (e.g., a 50-turn stalemate), the seed lets you replay that exact game with logging enabled. Without determinism, anomalies are unreproducible.

## Examples

Phase 7 baseline vs. Phase 10 verification:

| Metric | Phase 7 | Phase 10 | Status |
|--------|---------|----------|--------|
| Avg game length | 11.9 turns | 11.9 turns | Match |
| Strategic dominance | 57% | 57% | Match |
| Total dominance | 43% | 43% | Match |
| First-player win rate | 41% | 41% | Match |
| Economy starvation | 963 events | 963 events | Match |
| Avg company lifespan | 2.0 turns | 2.0 turns | Match |
| Runaway rate | 76% | 76% | Match |

## Applicability

This pattern applies to any system with complex emergent behavior: game balance, recommendation engines, scheduling algorithms, pricing models, load balancers. The key requirement is that you can run the system headlessly and measure meaningful outputs. It does NOT apply when the system requires human input that can't be automated (though an AI player, as in this project, solves that for games).

## Related Lessons

- [AI Scoring Weights as a Balance Lever](ai-scoring-weights-as-balance-lever.md) — The weights table's quality is measured by these simulation metrics.
- [Data-Driven Game Design with a Verb Grammar](data-driven-game-design-with-verb-grammar.md) — The verb grammar's correctness is validated by the simulation running all 84 cards through the full resolver pipeline without crashes.
- [Spreadsheet-to-Code Pipeline for Game Content](spreadsheet-to-code-pipeline-for-game-content.md) — Generated card data is validated not just by schema checks but by running full games.
