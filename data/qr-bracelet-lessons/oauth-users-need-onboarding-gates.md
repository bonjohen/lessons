# OAuth Users Need Onboarding Gates

## The Lesson

When users can sign up via OAuth (Google, Apple, etc.), they bypass your signup form — and any required fields on it. If your app requires data that OAuth doesn't provide (a phone number, a company name, a role), you need a gate between login and the main app that collects it before proceeding.

## Context

MyReachBand requires a verified phone number to create bracelets. Users who sign up with email+password provide their phone during signup. Users who sign up with Google OAuth don't — Google only gives you an email and a name. Without a gate, OAuth users land on the dashboard and crash when they try to create a bracelet (the phone field is empty).

## What Happened

1. Built Google OAuth: click "Continue with Google," select account, user is created with email and empty phone, redirect to `/dashboard`.
2. Dashboard loaded fine (no phone needed to list bracelets). But creating a bracelet crashed — the form pre-populates the phone field from `user.phone`, which was empty.
3. First fix attempt: the Worker crashed with Error 1101 because the `INSERT` statement hit a `NOT NULL` constraint on a different field. Hard to diagnose because the error was generic.
4. Added a gate: after authentication, check `if (!user.phone)`. If true, redirect to `/setup-phone` instead of `/dashboard`.
5. The `/setup-phone` page says "One more step" — enter phone, verify via SMS code, then proceed to dashboard.
6. The gate checks on every authenticated request, not just after login. This catches edge cases like a user whose phone was deleted or a database migration that cleared the field.

## Key Insights

- **Check on every request, not just after login.** Putting the gate only in the OAuth callback misses users who were created in a previous session, users whose required data was later invalidated, and edge cases from database migrations.
- **The gate must allow its own routes through.** The phone check `if (!user.phone)` must exempt `/setup-phone` and `/setup-phone/verify` — otherwise the user is stuck in an infinite redirect loop.
- **Use the same verification flow.** The `/setup-phone` page reuses the same Twilio Verify flow as signup. Don't build a separate system — it's the same form, the same SMS code, the same verification logic.
- **OAuth providers give you less than you think.** Google gives: email, name, profile picture, locale. Google does NOT give: phone number, address, employer, or any custom field your app needs. Plan for this at design time, not after launch.
- **Frame it as onboarding, not an error.** "One more step" with a clear explanation ("This becomes the default contact on your bracelets") is better than "Error: phone number required."

## Examples

### The gate pattern
```javascript
const user = await getUser(cookieHeader, secret, db);
if (!user) return redirect("/login");

// Gate: required fields must exist before accessing the app
if (!user.phone && path !== "setup-phone" && path !== "setup-phone/verify") {
  return redirect("/setup-phone");
}

// ... normal route handling
```

### What NOT to do
```javascript
// Only checking in the OAuth callback — misses returning users
if (path === "login/google/callback") {
  const user = createOrFindUser(googleEmail);
  if (!user.phone) return redirect("/setup-phone"); // Only fires once!
  return redirect("/dashboard");
}
```

## Applicability

This applies whenever you support multiple signup methods with different data collection. OAuth + email/password is the most common case. It also applies to: SSO integrations (SAML gives you even less than OAuth), magic link login (no password, no form), and social login providers (Facebook, Apple, GitHub — each gives different fields).

## Related Lessons

- [Google OAuth2](google-oauth2.md) — the OAuth provider that creates users without phone numbers
- [Phone Numbers as Data Not Identity](phone-numbers-as-data-not-identity.md) — why the phone is required but not the identity
