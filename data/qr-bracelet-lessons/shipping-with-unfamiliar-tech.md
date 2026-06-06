# Shipping a Product with Unfamiliar Technologies

## The Lesson

You can ship a production web app in a single day using technologies you've never touched before — if you choose technologies that have small API surfaces, skip the tutorials, and build the real thing from the start. The fastest way to learn a tool is to use it on a real problem, not to study it in isolation.

## Context

MyReachBand was built in one day using five technologies the developer had never used before: Cloudflare Workers, Cloudflare D1, Twilio Verify, Google OAuth2, and Wrangler CLI. The result was a live product at MyReachBand.com with user accounts, phone verification, OAuth login, QR code generation, and printable bracelet PDFs.

## What Happened

1. Started with a feasibility spike — deployed a minimal Worker that queried D1 and returned HTML. Proved the stack worked in 5 minutes. No tutorial, no starter template.
2. Built the real app immediately after the spike. Didn't build a "learning project" first — the learning happened while building the product.
3. Hit real bugs that tutorials wouldn't have covered: `echo` adding newlines to secrets, D1 schema divergence between environments, OAuth token propagation delays, jsPDF dash patterns rendering as blocks.
4. Each bug taught a lesson that only emerges from production use. The `echo` newline bug, for instance, isn't mentioned in any Wrangler tutorial — it's a Unix shell behavior that happens to break Cloudflare secrets.
5. By the end of the day: 7 implementation phases complete, custom domain configured, 16 commits, 12 files of production code.
6. Day two added: customer accounts, Twilio phone verification, Google OAuth, QR code downloads, printable PDF sheets, dev/prod environments.

## Key Insights

- **Small API surface = fast learning.** Twilio Verify is two REST calls. D1 is `prepare().bind().first()`. Google OAuth is four HTTP requests. Workers export one `fetch()` function. When the entire API fits on one screen, you don't need a course — you need a code example.
- **Skip the tutorial, build the thing.** Tutorials teach you how the author uses the tool. Building your product teaches you how YOU need to use it. The knowledge you gain is immediately applicable, not theoretical.
- **Bugs are the best teachers.** The `echo` newline bug taught more about secret management than any documentation page. The schema divergence bug taught more about migration discipline than any "best practices" guide. Real bugs in real context create durable knowledge.
- **Feasibility spikes derisk everything.** A 5-minute spike that proves "Workers can query D1 and return HTML under 500ms" eliminates the biggest risk before you write a single line of production code.
- **Don't study the ecosystem, use the minimum.** Cloudflare has Workers, KV, R2, Durable Objects, Queues, AI, Browser Rendering, and dozens more products. MyReachBand uses Workers + D1. Knowing two products deeply is better than knowing twelve superficially.
- **Production pressure accelerates learning.** When the code must work for real users, you read error messages carefully, you test edge cases, and you fix bugs immediately. Sandbox projects let you skip these steps — and the skipped steps are where the learning lives.

## Applicability

This approach works when: the technologies have small API surfaces, good error messages, and free tiers for experimentation. It does NOT work when: the technology has a large mandatory learning curve (Kubernetes, Terraform), requires significant upfront configuration (AWS IAM), or has expensive failure modes (cloud billing, data loss).
