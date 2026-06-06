---
title: "Twilio Verify"
summary: "Twilio Verify is a two-API-call service for phone number verification. You call \"send code,\" Twilio texts a 6-digit code to the phone. You call \"check code\" with what the user entered, Twilio tells you if it matches. You never see, store, or manage the code yourself."
date: 2026-06-06
lesson_type: implementation
tags: [cloudflare, serverless, security, sms, devops]
---
# Twilio Verify

## The Lesson

Twilio Verify is a two-API-call service for phone number verification. You call "send code," Twilio texts a 6-digit code to the phone. You call "check code" with what the user entered, Twilio tells you if it matches. You never see, store, or manage the code yourself.

## Context

MyReachBand verifies phone numbers before they can be used on bracelets. When a user creates an account or adds a new phone number to a bracelet, they must prove they can receive texts at that number. Twilio Verify handles the SMS delivery, code generation, expiry, rate limiting, and fraud detection.

## What Happened

1. Created a Twilio account at twilio.com (free trial with ~$15 credit).
2. Created a Verify Service in the Twilio console — this gives you a Service SID (starts with `VA`).
3. Stored three credentials as Wrangler secrets: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_VERIFY_SID`.
4. Built a thin wrapper (`src/twilio.js`) with two functions: `sendVerification(phone, env)` and `checkVerification(phone, code, env)`.
5. Integrated into two flows: account signup (verify the user's phone) and bracelet creation (verify a new contact phone).
6. Phone numbers are normalized server-side before sending to Twilio — stripping parentheses, dashes, spaces, and prepending `+1` for US 10-digit numbers. Twilio requires E.164 format (`+14258301802`).

## Key Insights

- **Two REST calls, that's it.** Send: `POST /v2/Services/{SID}/Verifications` with `To` and `Channel=sms`. Check: `POST /v2/Services/{SID}/VerificationCheck` with `To` and `Code`. Both use HTTP Basic auth with your Account SID and Auth Token.
- **You never handle the code.** Twilio generates it, sends it, stores it, expires it, and checks it. Your backend never sees the 6-digit number. This eliminates an entire class of security concerns.
- **Normalize phone numbers before calling Twilio.** `(425) 830-1802` will fail. `+14258301802` will work. Strip non-digits, prepend `+1` for 10-digit US numbers.
- **Built-in rate limiting.** Twilio allows 5 send attempts per phone per hour and 5 check attempts per verification. You don't need to build your own rate limiter.
- **$0.05 per successful verification.** Failed attempts are free. The free trial gives you ~300 verifications. At MyReachBand's scale, this costs less than $1/month.
- **Store verified phones to avoid re-verification.** Once a user verifies a number, record it in a `verified_phones` table. They shouldn't have to verify the same number again for another bracelet.

## Examples

### Sending a verification code
```javascript
const res = await fetch(
  `https://verify.twilio.com/v2/Services/${env.TWILIO_VERIFY_SID}/Verifications`,
  {
    method: "POST",
    headers: {
      Authorization: "Basic " + btoa(env.TWILIO_ACCOUNT_SID + ":" + env.TWILIO_AUTH_TOKEN),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `To=${encodeURIComponent(phone)}&Channel=sms`,
  }
);
```

### Checking a code
```javascript
const res = await fetch(
  `https://verify.twilio.com/v2/Services/${env.TWILIO_VERIFY_SID}/VerificationCheck`,
  {
    method: "POST",
    headers: {
      Authorization: "Basic " + btoa(env.TWILIO_ACCOUNT_SID + ":" + env.TWILIO_AUTH_TOKEN),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `To=${encodeURIComponent(phone)}&Code=${encodeURIComponent(code)}`,
  }
);
const data = await res.json();
if (data.status === "approved") { /* verified */ }
```

### Phone normalization
```javascript
function normalizePhone(raw) {
  let digits = raw.replace(/[^\d]/g, "");
  if (digits.length === 10) digits = "1" + digits;
  if (digits.length === 11 && digits.startsWith("1")) return "+" + digits;
  return "+" + digits;
}
```

## Applicability

Twilio Verify works from any backend that can make HTTP requests — Workers, Lambda, traditional servers. The same API supports voice calls and email verification (change `Channel` to `call` or `email`). NOT needed if you only need to verify email addresses — most email services have their own verification flows.

## Related Lessons

- [Phone Numbers as Data Not Identity](phone-numbers-as-data-not-identity.md) — why phone verification is separate from account identity
- [Cloudflare Workers](cloudflare-workers.md) — the runtime that calls Twilio's API
