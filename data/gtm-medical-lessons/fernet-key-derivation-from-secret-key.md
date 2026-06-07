---
date: 2026-06-03
phase: implementation
---

# Fernet Key Derivation from SECRET_KEY

## The Lesson

Deriving a Fernet encryption key from an existing application secret avoids managing a second secret, but the derivation method and minimum-length constraint must be documented and enforced at startup — otherwise the encryption silently breaks when the secret is too short or changes.

## Context

A medical portal needed to encrypt AI provider API keys at rest in the database. The system already had a `SECRET_KEY` environment variable used for session signing. Rather than introducing a second secret (`ENCRYPTION_KEY`), the team derived the Fernet key from the first 32 bytes of `SECRET_KEY`.

## What Happened

1. The ConfigService derived a Fernet key: `base64.urlsafe_b64encode(settings.secret_key[:32].encode())`.
2. This required `SECRET_KEY` to be at least 32 characters — a constraint that was already enforced at startup validation (`sys.exit(1)` if `len(secret_key) < 32`).
3. The Fernet key is deterministic: same `SECRET_KEY` always produces the same encryption key. Encrypted values in the database remain decryptable across restarts.
4. The GET endpoint never returns plaintext API keys. It decrypts only to extract the last 4 characters for masking: `****...z789`.
5. Unit tests verified the round-trip: encrypt → store → decrypt → mask, using a test secret of `"a" * 32`.

## Key Insights

- **One secret is better than two, if the derivation is documented.** Every additional secret is a deployment failure mode. Deriving from an existing secret reduces operational surface area.
- **The minimum-length constraint is load-bearing.** If someone sets `SECRET_KEY=abc`, the `[:32]` slice silently produces a shorter key and `base64.urlsafe_b64encode` produces an invalid Fernet key. Startup validation must enforce the minimum.
- **Changing the secret breaks existing encrypted data.** If `SECRET_KEY` rotates, all Fernet-encrypted values become undecryptable. This is acceptable for a development-stage product but needs a key-rotation migration strategy before production.
- **Masking is a display concern, not a security boundary.** The "last 4 chars" masking lets admins confirm which key is stored without exposing the full value. The security boundary is the Fernet encryption itself and the `admin:config` permission gate.

## Applicability

Suitable for encrypting small, infrequently-rotated secrets (API keys, tokens) in applications with a single deployment. Not suitable for: high-volume encryption (Fernet has per-operation overhead), multi-tenant systems (tenants need independent keys), or systems requiring key rotation without data re-encryption.
