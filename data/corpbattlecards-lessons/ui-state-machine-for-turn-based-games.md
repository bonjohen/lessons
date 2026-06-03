---
phase: implementation
---

# UI State Machine for Turn-Based Games

## The Lesson

Model every distinct "what is the UI waiting for?" moment as an explicit state in an enum. The state machine eliminates the most common game UI bugs — wrong input handled at the wrong time, dialogs that don't dismiss, and turn phases that skip or repeat — by making the set of valid transitions explicit and the current state inspectable.

## Context

Corporate Battle Cards has a 6-phase turn structure (forced effects, upkeep decisions, production, public reveal, actions, end of turn) with multiple decision points: playing cards, picking targets, confirming actions, reacting to attacks, choosing upkeep payments, selecting public decks, and handling game over. The Pygame UI needed to route mouse clicks and key presses to the right handler depending on what the game is currently asking the player. Phase 8 built a render-only UI; Phase 9 added full interaction.

## What Happened

1. Phase 8 built the UI with a simple event loop: quit, resize, mouse motion (hover), scroll, and escape. No game state management — just rendering a static board.
2. Phase 9 introduced a `UIState` enum with 11 values: `IDLE`, `PICK_ACTION`, `PICK_TARGET`, `CONFIRM_PLAY`, `PICK_REACTION`, `UPKEEP_DECISIONS`, `PICK_PUBLIC_DECK`, `PICK_EFFECT_OPTION`, `GAME_OVER`, `AI_TURN`, `DISCARD_SELECT`.
3. Each state determines: what clicks do (card selection, dialog option, target pick), what keys do (P=pass, D=discard, Esc=cancel), what the status bar shows ("Click card to play | D=discard-draw | P=pass"), and whether a dialog is rendered.
4. The `_handle_click` method checks `self.ui_state` first, then dispatches to state-specific handlers. A click during `PICK_ACTION` selects a card; the same click during `AI_TURN` does nothing.
5. State transitions are explicit method calls: `_enter_action_pick()` sets state to `PICK_ACTION` and computes playable cards; `_show_reaction_dialog()` sets state to `PICK_REACTION` and builds the defense card list. Invalid transitions can't happen because there's no code path from `AI_TURN` to `PICK_TARGET`.
6. The AI turn uses the `AI_TURN` state with a timer-based event drain. Events from `run_ai_turn` are queued and displayed in small batches every 200ms, giving the human player time to follow. The state only transitions when the event queue is empty.

## Key Insights

- **The state enum is the single source of truth for "what are we doing right now."** Every rendering decision, every input routing, and every status message reads `self.ui_state`. There's no ambiguity about what phase the UI is in.
- **Dialogs are state, not overlays.** When a dialog is active, the UI state changes (e.g., to `CONFIRM_PLAY`). The dialog isn't a floating widget that might be dismissed by accident — it's the current mode of interaction. Clicks outside the dialog are ignored because the state handler only checks dialog options.
- **Cancel is a state transition, not an undo.** Pressing Escape during `PICK_TARGET` transitions to `PICK_ACTION` (clearing the selected card), not to some "previous state" stack. The set of valid cancel destinations is hardcoded per state, making it predictable.
- **AI turns need their own state.** Without `AI_TURN`, clicks during AI processing could queue human actions that arrive out of order. The state blocks all human input during the AI's turn while still allowing quit and scroll.
- **The state count reflects the game's decision complexity, not the code's complexity.** 11 states for a game with 6 turn phases and 5 card types is proportional. If the count grows past ~15, the game probably needs a hierarchical state machine.

## Examples

State transition for playing an offense card:

```
PICK_ACTION  →  (click offense card)
PICK_TARGET  →  (click target in dialog)  
CONFIRM_PLAY →  (click Confirm)
  → submit_action → resolve_ai_reaction
PICK_ACTION  (back to action selection, actions_remaining -= 1)
```

State transition for AI turn with pending reaction:

```
AI_TURN      →  (events drain over 200ms intervals)
  → AI attacks human → pending reaction detected
PICK_REACTION → (human picks defense or passes)
  → submit_reaction
PICK_ACTION   (human's turn continues)
```

## Applicability

This pattern applies to any interactive application with modal input: turn-based games, wizard/stepper UIs, form builders with conditional pages, command-line REPLs with modes. It does NOT apply to continuous-input systems (real-time games, drawing tools) where the input interpretation doesn't change based on a discrete mode.

## Related Lessons

- [Data-Driven Game Design with a Verb Grammar](data-driven-game-design-with-verb-grammar.md) — The state machine dispatches actions to the same verb resolvers; the UI layer and the engine layer are cleanly separated.
