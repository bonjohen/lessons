---
title: "Google OAuth2"
summary: "Google OAuth2 lets users sign in with their Google account. Your server redirects to Google, Google authenticates the user, and redirects back with a code. You exchange the code for the user's email. The entire flow is four HTTP calls and requires no client-side SDK."
date: 2026-06-06
lesson_type: implementation
tags: [cloudflare, serverless, authentication, frontend, devops]
---
# Google OAuth2

## The Lesson

Google OAuth2 lets users sign in with their Google account. Your server redirects to Google, Google authenticates the user, and redirects back with a code. You exchange the code for the user's email. The entire flow is four HTTP calls and requires no client-side SDK.

## Context

MyReachBand supports "Continue with Google" alongside email/password login. The OAuth2 flow runs entirely server-side in a Cloudflare Worker — no Firebase, no Google client SDK, no JavaScript loaded in the browser. The Worker handles the redirect, token exchange, and user creation.

## What Happened

1. Created a Google Cloud project (free) and configured the OAuth consent screen with the app name "MyReachBand."
2. Created OAuth credentials (Web application type) with authorized redirect URIs for both production (`myreachband.com/login/google/callback`) and dev (`dev.myreachband.com/login/google/callback`).
3. Stored `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` as Wrangler secrets.
4. Hit `redirect_uri_mismatch` errors repeatedly. Causes: trailing newline in the secret (from `echo`), new redirect URIs taking 2-5 minutes to propagate across Google's servers, and missing redirect URIs for the dev environment.
5. The app was initially in "Testing" mode — only manually-added test users could sign in. Published the app to production mode (free, no review needed for basic scopes).
6. OAuth users who sign up don't have a phone number yet. Added a `/setup-phone` gate that intercepts them before they can access the dashboard.

## Key Insights

- **No client SDK needed.** The entire flow is server-side HTTP redirects and REST calls. Your Worker redirects to Google, Google redirects back. You call Google's token endpoint and userinfo endpoint. No JavaScript SDK loads in the user's browser.
- **Redirect URI must match exactly.** The URI in your auth request must character-for-character match one registered in the Google console. Trailing slashes, port numbers, http vs https — any mismatch returns `redirect_uri_mismatch`.
- **Credential propagation takes minutes.** After adding a new redirect URI in the Google console, it may take 2-5 minutes before all Google servers recognize it. Different geographic regions propagate at different speeds — desktop and mobile may behave differently during this window.
- **Use `printf` for secrets.** `echo` adds a newline that becomes part of the client ID, which then gets URL-encoded into the redirect URI, which doesn't match what's registered. This was the hardest bug to find.
- **"Testing" vs "In Production" matters.** In testing mode, only users you manually add can sign in. Publishing to production (OAuth consent screen > Audience > Publish App) is free and doesn't require Google review for `email` and `profile` scopes.
- **OAuth users may lack required fields.** Google gives you email but not a phone number. If your app requires a phone, you need an onboarding gate that catches OAuth-created users and walks them through adding the missing data before they access the main app.

## Examples

### The four-step flow

```
1. User clicks "Continue with Google"
   → Worker redirects to:
   https://accounts.google.com/o/oauth2/v2/auth?
     client_id=...&redirect_uri=...&response_type=code&scope=openid email profile&state=random

2. User authenticates on Google
   → Google redirects to:
   https://myreachband.com/login/google/callback?code=AUTH_CODE&state=random

3. Worker exchanges code for tokens:
   POST https://oauth2.googleapis.com/token
   Body: code, client_id, client_secret, redirect_uri, grant_type=authorization_code
   → Returns: { access_token, id_token }

4. Worker fetches user info:
   GET https://www.googleapis.com/oauth2/v3/userinfo
   Header: Authorization: Bearer {access_token}
   → Returns: { email, sub, email_verified }
```

### CSRF protection with state parameter
```javascript
// On redirect to Google
const state = Array.from(crypto.getRandomValues(new Uint8Array(16)))
  .map(b => b.toString(16).padStart(2, "0")).join("");
// Store state in a cookie
const stateCookie = `oauth_state=${state}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600`;

// On callback from Google
const stateMatch = cookieHeader.match(/oauth_state=([^;]+)/);
if (stateMatch[1] !== url.searchParams.get("state")) {
  // CSRF attack or expired session — reject
}
```

### Google Cloud setup checklist
1. console.cloud.google.com → Create project
2. APIs & Services → OAuth consent screen → External → app name, email
3. Audience → Publish App (switch from Testing to Production)
4. Credentials → Create OAuth Client ID → Web application
5. Add redirect URIs for every environment
6. Copy Client ID and Client Secret → `wrangler secret put`

## Implementation Guide

### Step 1: Register your application with Google

Go to [console.cloud.google.com](https://console.cloud.google.com):

1. Create a new project (or select an existing one).
2. Navigate to **APIs & Services → OAuth consent screen**. Choose "External" for user type. Fill in the app name and support email.
3. Go to **Audience → Publish App** to switch from Testing mode to Production. This is free and doesn't require Google review for `email` and `profile` scopes. Without this, only manually-added test users can sign in.
4. Navigate to **Credentials → Create Credentials → OAuth Client ID**. Choose "Web application."
5. Add **Authorized redirect URIs** for every environment — production, staging, and local development. Each must match character-for-character what your server sends in the `redirect_uri` parameter.
6. Copy the **Client ID** and **Client Secret**. Store them securely (environment variables, secret manager, or encrypted config — never in source code).

### Step 2: Build the login redirect

When the user clicks "Continue with Google," redirect them to Google's authorization endpoint with your client ID, redirect URI, and a CSRF state parameter:

```javascript
// Generate CSRF state token
const state = Array.from(crypto.getRandomValues(new Uint8Array(16)))
  .map(b => b.toString(16).padStart(2, "0")).join("");

// Store state in an HttpOnly cookie for verification on callback
const headers = new Headers();
headers.append("Set-Cookie",
  `oauth_state=${state}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600`);

// Build the Google auth URL
const params = new URLSearchParams({
  client_id: GOOGLE_CLIENT_ID,
  redirect_uri: "https://yourapp.com/login/google/callback",
  response_type: "code",
  scope: "openid email profile",
  state: state,
});

// Redirect the user to Google
return Response.redirect(
  `https://accounts.google.com/o/oauth2/v2/auth?${params}`, 302);
```

### Step 3: Handle the callback and exchange the code for tokens

When Google redirects back to your callback URL, verify the state parameter, then exchange the authorization code for an access token:

```javascript
async function handleOAuthCallback(request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");

  // Verify CSRF state matches the cookie
  const cookies = request.headers.get("Cookie") || "";
  const savedState = cookies.match(/oauth_state=([^;]+)/)?.[1];
  if (!savedState || savedState !== state) {
    return new Response("Invalid state", { status: 403 });
  }

  // Exchange authorization code for tokens
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      redirect_uri: "https://yourapp.com/login/google/callback",
      grant_type: "authorization_code",
    }),
  });
  const tokens = await tokenRes.json();

  // Fetch user info with the access token
  const userRes = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  const user = await userRes.json();
  // user.email, user.sub (Google ID), user.email_verified

  // Create or find user in your database, set session cookie, redirect to app
}
```

### Step 4: Handle user creation and missing fields

Google provides email, name, and a unique `sub` identifier, but not application-specific fields (phone number, preferences, etc.). After creating the user record, check for required fields and redirect to an onboarding flow if anything is missing:

```javascript
let dbUser = await db.getUserByEmail(user.email);
if (!dbUser) {
  dbUser = await db.createUser({
    email: user.email,
    google_id: user.sub,
    auth_method: "google",
  });
}

// Check for required fields the OAuth provider doesn't supply
if (!dbUser.phone_number) {
  return Response.redirect("/setup-phone", 302);
}
return Response.redirect("/dashboard", 302);
```

## Applicability

This flow works identically for Microsoft, Apple, GitHub, and most OAuth2 providers — only the URLs change. The pattern (redirect → code → token exchange → userinfo) is universal. Firebase Auth and Auth0 wrap this flow in SDKs, but for server-rendered apps, raw OAuth2 is simpler and has no dependencies.

## Related Lessons

- [OAuth Users Need Onboarding Gates](oauth-users-need-onboarding-gates.md) — handling users created without required fields
- [Echo vs Printf for Secrets](echo-vs-printf-for-secrets.md) — the newline bug that broke OAuth
