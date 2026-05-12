# AI Scoring Weights as a Balance Lever

## The Lesson

When building an AI opponent for a strategy game, express its decision-making as a single weights table that scores every legal action. This table simultaneously defines AI behavior and serves as a balance tuning surface — changing one number shifts both how the AI plays and how the game feels.

## Context

Corporate Battle Cards needed an AI that could play a complete game autonomously for both single-player gameplay and batch simulation. The AI must choose actions (deploy companies, play offenses, pass), reactions (play defense or take the hit), upkeep decisions (pay or drop effects), and public deck reveals. The design doc specified a weights table with specific scoring values. The same AI is used for human-vs-AI games and for 100-game batch simulation runs that detect balance issues.

## What Happened

1. Phase 6 implemented `ai/scorer.py` with a `score_action` function that evaluates every legal action against a weights table: prevent loss (+100), trigger win (+100), keep company active (+40), deactivate enemy company (+35), attack weak sustain (+25), deploy to weakest pool (+20), upgrade stable company (+15), counter-wheel advantage (+10), illegal card near exposure thresholds (-30/-50/-80), discard defense card (-15).
2. `AIAgent.choose_action` scores all legal actions, collects ties at the max score, and breaks ties with the game's seeded RNG. This makes AI behavior deterministic for a given seed.
3. The same scorer is used for reactions (`choose_reaction`), upkeep decisions (`choose_upkeep`), and public deck selection (`choose_public_deck`). Every AI decision point flows through the same weights.
4. Phase 7 ran 100 AI-vs-AI simulations. The metrics — 11.9 average turns, 57% strategic dominance / 43% total dominance, 41% first-player win rate — are direct consequences of the weights table.
5. Phase 6.5 changed the public market significantly (single-effect to multi-effect cards). The AI's `choose_public_deck` scoring needed no change because it already scored by effect impact, not by card structure.
6. Phase 10 re-ran the 100-game batch and got identical metrics, confirming the weights table was stable across the engine changes.

## Key Insights

- **A flat weights table is readable by non-engineers.** A game designer can look at "deactivate enemy: +35, deploy weakest pool: +20" and immediately understand the AI's priorities. A neural network or complex heuristic tree wouldn't offer this.
- **Negative weights for risky behavior create natural AI caution.** The exposure penalties (-30/-50/-80 at escalating thresholds) make the AI avoid illegal cards as exposure accumulates. This emerged from the weights, not from explicit "if exposure > 5, don't play illegal" logic.
- **Tie-breaking with seeded RNG preserves determinism.** When multiple actions score equally (common for "pass" vs. "play a marginal card"), using the game's existing RNG means the AI's choice is deterministic for replay purposes.
- **The weights table is also a test oracle.** Testing the AI doesn't require mocking game states — you test that `score_action` returns the right score for known inputs, then trust that `max()` picks the right one.
- **Batch simulation is the real balance test.** Unit tests verify the scorer works. 100-game batches verify the scorer produces fun games. A 41% first-player win rate and a mix of win conditions wouldn't be visible in unit tests.

## Examples

Scoring a company deployment when the player's weakest pool is Economy:

```
Base: +0 (company play has no inherent score)
+ deploy to weakest pool: +20 (company outputs Economy)
+ keep company active: +40 (company will produce tokens)
= Total: +60
```

Scoring an illegal offense card when exposure is at 4 (threshold is 5):

```
Base: +0
+ deactivate enemy: +35
+ counter-wheel advantage: +10
- illegal near threshold 5: -30
= Total: +15 (marginal — AI might still play it)
```

Same card when exposure is at 9 (threshold 10):

```
Base: +0
+ deactivate enemy: +35
+ counter-wheel advantage: +10
- illegal near threshold 10: -80
= Total: -35 (AI avoids it)
```

## Applicability

This pattern applies to any game AI where decisions are discrete and enumerable (card games, turn-based strategy, board games). It does NOT apply to continuous-action spaces (real-time games, physics-based games) where scoring every possible action is intractable. It also becomes insufficient when the AI needs to plan multiple turns ahead — a weights table is greedy by nature.

## Related Lessons

- [Simulation as Acceptance Test](simulation-as-acceptance-test.md) — The weights table's quality is measured by batch simulation metrics, not by unit tests alone.
- [Data-Driven Game Design with a Verb Grammar](data-driven-game-design-with-verb-grammar.md) — The scorer evaluates actions produced by the verb grammar; both are data-driven systems that compose cleanly.
