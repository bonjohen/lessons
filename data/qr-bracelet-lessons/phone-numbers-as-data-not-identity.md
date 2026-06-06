---
title: "Phone Numbers as Data, Not Identity"
summary: "When a phone number appears in your product, decide early whether it's an identity (the account itself) or data (a field on a record). Conflating the two creates the wrong data model, the wrong auth flow, and forces users into a single-phone-per-account constraint that doesn't match reality."
date: 2026-06-06
lesson_type: implementation
tags: [authentication, sms, data-modeling]
---
# Phone Numbers as Data, Not Identity

## The Lesson

When a phone number appears in your product, decide early whether it's an identity (the account itself) or data (a field on a record). Conflating the two creates the wrong data model, the wrong auth flow, and forces users into a single-phone-per-account constraint that doesn't match reality.

## Context

MyReachBand lets users create QR bracelets that link to a trusted contact's phone number. Early designs assumed the user's phone number was both their account identity and the default contact on bracelets. This created confusion about what "verify your phone" meant — is it account verification or bracelet data validation?

## What Happened

1. Initial design proposed phone-number-only accounts: sign up with phone, log in with SMS code, phone is your identity.
2. Owner clarified: "Phone number is not an identity — it is a data element." Multiple bracelets can use the same phone number. The phone on the bracelet is contact data, not an account identifier.
3. Redesigned: accounts are email + password (with Google OAuth). Phone numbers are a separate data element verified via Twilio before use on bracelets.
4. Added a `verified_phones` table — tracks which phone numbers each user has proven they can receive texts at. A number verified by User A is not verified for User B.
5. The user's own phone (verified at signup) pre-populates as the default contact on new bracelets. They can change it, but new numbers require verification.
6. The physical bracelet shows NO phone numbers — they're hidden behind the QR code. This is the core product value: contact information without public display.

## Key Insights

- **Identity determines your data model.** If phone = identity, you get one phone per account, login-via-SMS, and no way for two accounts to share a number. If phone = data, you get flexible contact management with separate auth.
- **"Verify" means different things.** Verifying a phone for account identity means "this is who you are." Verifying a phone for bracelet data means "this number works and you have permission to use it." The same Twilio API serves both, but the user experience is different.
- **Pre-populate, don't mandate.** The user's phone is the default on new bracelets, but they can change it. This handles the common case (parent is the contact) without blocking the uncommon case (babysitter's number, school office, etc.).
- **Many-to-many is the right relationship.** One user can have many verified phones. One phone can appear on many bracelets. Different users can independently verify the same number. This matches real-world use.
- **The product promise drives the data model.** "No personal information on the bracelet" means the phone number is explicitly NOT displayed — it's hidden data accessed only via QR scan. This framing made it obvious that phone ≠ identity.

## Applicability

This applies whenever a contact method (phone, email, address) appears in a product. Ask: is this the user's identity, or is it data they manage? Emergency contact apps, delivery services, notification systems, and CRM tools all face this decision. Getting it wrong early is expensive to fix because it touches auth, schema, and every form in the app.

## Related Lessons

- [Twilio Verify](twilio-verify.md) — the tool used to verify phone numbers as data
- [OAuth Users Need Onboarding Gates](oauth-users-need-onboarding-gates.md) — what happens when identity (email) and data (phone) are properly separated
