---
phase: implementation
---

# Permission Union vs. Role Switching

## The Lesson

When a user has multiple roles, merging all permissions into a single set (union) is simpler to implement and understand than requiring users to switch between active roles — but it means users see all their capabilities simultaneously, which can cause confusion in healthcare contexts where acting under the wrong role has consequences.

## Context

A medical portal needed to support users with multiple roles: a doctor could be both a `provider` and a `patient`. The system needed to decide whether multi-role users actively switch between roles (seeing only one role's permissions at a time) or see the union of all their permissions at once. This was one of 10 design concerns raised by the user requirements document.

## What Happened

1. The user requirements (FR-13) specified "multi-role support" but left the interaction model open.
2. The PDR evaluated two options: role switching (active role selector in UI) vs. permission union (all permissions always active).
3. Permission union was chosen. Rationale: simpler frontend (no role picker component, no role state management), simpler backend (no "active role" in session), and the navigation system already filtered items by permission — showing only what the user can access.
4. The consequence: a user with both `patient` and `provider` roles sees both the Patient Dashboard and Provider Dashboard in their sidebar simultaneously.
5. The PDR added a risk note (Risk 3: context confusion) acknowledging that proxy/caregiver mode still needs clear context indicators, even though role switching was eliminated.

## Key Insights

- **Union is the right default for most RBAC systems.** Role switching adds UI complexity (which role am I in?), state management complexity (what happens if my role expires mid-session?), and support complexity (users calling in confused about which role they selected). Union avoids all of this.
- **The risk shifts from "wrong role" to "wrong context."** With union, the role question disappears. But the organization/patient context question remains: "Am I looking at my own patient record or my proxy patient's?" Context indicators matter more than role indicators.
- **Navigation filtering makes union palatable.** If the sidebar showed every possible page regardless of permissions, union would be overwhelming. But because navigation is permission-filtered, users only see pages they can actually access — the union is invisible except through the nav items that appear.
- **Document the trade-off, not just the decision.** The PDR's Concern #4 resolution explicitly stated "no role switching, permissions union" with reasoning. When a future sprint reconsiders (e.g., regulatory requirement to audit which role a clinician acted under), the decision record explains why union was chosen and what would need to change.

## Applicability

Union works well for: internal tools, portals with few roles, and systems where roles grant access to different areas (not different views of the same data). Union works poorly for: systems where the same action has different meaning per role (e.g., a doctor ordering a test for themselves vs. for a patient), audit environments requiring per-action role attribution, and systems with 10+ roles where the combined nav would be overwhelming.
