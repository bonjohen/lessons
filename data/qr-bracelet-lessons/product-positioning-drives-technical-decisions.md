---
title: "Product Positioning Drives Technical Decisions"
summary: "How you describe your product to users determines which features you build, which fields you show, and which language your code uses. A positioning document written before implementation saves more engineering time than any technical design doc because it eliminates features before they're built."
date: 2026-06-06
lesson_type: implementation
tags: [database, security, data-modeling]
---
# Product Positioning Drives Technical Decisions

## The Lesson

How you describe your product to users determines which features you build, which fields you show, and which language your code uses. A positioning document written before implementation saves more engineering time than any technical design doc because it eliminates features before they're built.

## Context

MyReachBand started as a "QR Safety Bracelet" — an emergency contact system with safety notes, medical alerts, and revocation workflows. A positioning document (`docs/myreachband.md`) reframed it as a "simple QR bracelet for reaching a trusted contact" — a temporary contact bracelet, not an emergency identity system. This single document changed almost every screen in the app.

## What Happened

1. Initial implementation had emergency-language UI: red "SAFETY INFORMATION" heading, "Emergency Contact" labels, medical note fields, safety note fields.
2. Owner wrote a positioning doc defining the product as warm, non-medical, non-alarming. Key term: "trusted contact" instead of "emergency contact."
3. Rethemed the entire UI based on the doc: red → teal, "SAFETY INFORMATION" → "Reach Trusted Contact," "Emergency Contact" → "Trusted Contact," alarm emoji removed.
4. Hid medical_note and safety_note fields from the v1 form — the positioning doc said to avoid inviting sensitive data in the first version. The database columns remain for future use.
5. Removed contact name from the form and scan page — the positioning doc said "no personal information visible." The scan page shows just "Call Trusted Contact" without revealing a name.
6. Changed the admin language: "Revoke" → "Disable," "Admin" → "Dashboard," "Manage" → "My Bracelets."
7. Added message presets based on use cases from the positioning doc: field trips, elder care, lost-and-found, temporary care.

## Key Insights

- **Write the positioning doc first.** Before wireframes, before schemas, before code. "Is this an emergency system or a convenience tool?" changes everything downstream. Answering it in code is 10x more expensive than answering it in a document.
- **Language choices propagate everywhere.** "Trusted contact" vs "emergency contact" isn't just UI copy — it affects form labels, error messages, email templates, documentation, support language, and how users explain the product to others.
- **Hiding features is a design decision.** The database has `medical_note` and `safety_note` columns. The UI doesn't expose them in v1. This is cheaper than deleting them (no migration needed) and preserves the option to add them later.
- **Tone affects color palette.** "Emergency" suggests red, bold, urgent. "Trusted contact" suggests teal, calm, approachable. The positioning doc's tone section (`"Clean, calm, readable, non-medical, non-alarming"`) directly determined the CSS color variables.
- **Use cases from positioning become presets.** The doc listed 10 use cases (field trips, elder care, travel, etc.). These became the scan message dropdown presets and the carousel slides. The positioning doc was literally a feature spec.
- **"Temporary" unlocks simplicity.** Framing the product as "temporary contact bracelet" means you don't need: permanent medical records, regulatory compliance, audit trails, or HIPAA considerations. One word in the positioning doc eliminated months of potential scope.

## Examples

### Before positioning doc
```
Header: ⚠️ SAFETY INFORMATION
Button: 📞 Call Jane Doe (Emergency Contact)
Field: Medical Note, Safety Note
Color: #d32f2f (red)
```

### After positioning doc
```
Header: Reach Trusted Contact
Button: Call Trusted Contact
Field: (hidden in v1)
Color: #138A9E (teal)
```

## Applicability

This applies to any product where the framing is ambiguous. "Is this a security tool or a convenience tool?" "Is this for developers or business users?" "Is this for daily use or emergencies?" The positioning decision cascades into UI, data model, feature scope, and pricing. Getting it wrong means building the right features with the wrong framing — which users reject even though the technology works.

## Related Lessons

- [Phone Numbers as Data Not Identity](phone-numbers-as-data-not-identity.md) — a data model decision driven by product positioning
