---
date: 2026-05-11
phase: implementation
---

# Counter Wheel as Asymmetric Balance

## The Lesson

A circular advantage mechanic (A beats B beats C beats D beats A) creates asymmetric matchups from symmetric starting positions. The modifier can be small (+1/-1) and still be load-bearing if it touches enough systems — attacks, defenses, public effects, SWOT traits, and upgrade synergies.

## Context

Corporate Battle Cards has four resource pools: Economy, Technology, Reputation, and Influence. All players start with 5 tokens in each pool — perfectly symmetric. The counter wheel defines a circular advantage: Economy counters Technology, Technology counters Reputation, Reputation counters Influence, Influence counters Economy. When attacking the pool you counter, you get +1 to the effect. When attacking the pool that counters yours, you get -1. This is a +/-1 modifier on a base of 2-5 tokens — small in absolute terms but significant relative to pool sizes.

## What Happened

1. Phase 3 implemented `engine/counter_wheel.py` as a simple dict lookup: `COUNTERS = {Economy: Technology, Technology: Reputation, Reputation: Influence, Influence: Economy}`. The `counter_modifier` function returns +1 (advantage), -1 (disadvantage), or 0 (neutral) based on attacker pool vs. target pool.
2. Phase 4 wired the modifier into the 11-step attack resolution pipeline at step 4. The same modifier is applied to offense effects, SWOT weakness calculations, and public market interactions.
3. The AI scorer in Phase 6 added "counter-wheel advantage: +10" as a scoring weight, making the AI prefer attacks that exploit the wheel. This emerged naturally from the weights table — no special counter-wheel logic in the AI.
4. Phase 7 simulation showed economy pool starving 963 times vs. reputation at only 2. This asymmetry isn't caused by the counter wheel directly (it's symmetric by design) but by the card distribution — more companies produce economy tokens, creating more economy-targeted attacks via the counter wheel.
5. The 16 pool pairings were tested exhaustively in `test_counter_wheel.py`: 4 advantages, 4 disadvantages, 4 self-matchups (0), and 4 cross-neutral matchups (0). The test is a complete truth table.

## Key Insights

- **Circular advantage creates depth from a simple rule.** With 4 pools, there are 16 possible attack/target combinations. The counter wheel makes 8 of them mechanically different (+1 or -1), turning "attack any pool" into a strategic choice with consequences.
- **Small modifiers matter when base values are small.** +1 on a 3-token attack is a 33% increase. On a 2-token effect, it's 50%. The modifier is small in absolute terms but large relative to the game's economy. This is more impactful than it appears on paper.
- **The wheel should touch more than one system.** If the counter wheel only affected direct attacks, players could ignore it by not attacking. Applying it to public effects, SWOT weaknesses, and upgrade synergies means the wheel is always relevant, even in defensive play.
- **Symmetric mechanics produce asymmetric outcomes through card distribution.** The counter wheel itself is perfectly symmetric (every pool counters one and is countered by one). The asymmetric starvation rates (economy 963, reputation 2) come from the card set having more economy-producing companies, not from the wheel being biased.
- **A complete truth table test is worth writing.** 16 test cases for 16 pairings is exhaustive and cheap. It prevents the most likely bug — getting one direction wrong in the COUNTERS dict.

## Examples

Counter wheel diagram:

```
Economy  ──counters──>  Technology
   ^                         |
   |                    counters
counters                     |
   |                         v
Influence  <──counters──  Reputation
```

Attack resolution with counter-wheel modifier:

```
Attacker plays "Compliance Audit" (Influence pool, base effect: -3 Reputation)
Target pool: Reputation
Counter check: Influence → counters → Economy (not Reputation)
              Reputation → counters → Influence (Reputation counters Influence)
Result: attacker is DISADVANTAGED (-1)
Final effect: -3 + (-1) = -2 Reputation
```

Same card targeting Economy:

```
Counter check: Influence → counters → Economy (match!)
Result: attacker has ADVANTAGE (+1)
Final effect: -3 + 1 = -4 Economy
```

## Applicability

This pattern applies to any game or system with multiple resource types where you want to create strategic trade-offs: RPGs with elemental types, RTS games with unit counters, trading card games with color/faction advantages. It does NOT apply when resources are fungible (all interchangeable) or when the number of resource types is too large for a clean cycle (beyond ~6 types, the wheel becomes hard to reason about).

## Related Lessons

- [AI Scoring Weights as a Balance Lever](ai-scoring-weights-as-balance-lever.md) — The AI scores counter-wheel advantage at +10, making it prefer attacks that exploit the wheel.
- [Simulation as Acceptance Test](simulation-as-acceptance-test.md) — The pool starvation asymmetry (economy 963 vs. reputation 2) was only visible through batch simulation, not from inspecting the wheel mechanic in isolation.
