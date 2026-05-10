# Railway Deployment

## Architecture

- **Backend:** Railway service running FastAPI container
- **Embeddings:** OpenAI text-embedding-3-small (API)
- **Chat model:** OpenAI gpt-4o-mini (API)
- **Vector store:** ChromaDB on persistent volume (1GB)
- **CI/CD:** GitHub Actions with Railway CLI

## Prerequisites

1. Railway account: https://railway.com (Hobby plan required for volumes, $5/month)
2. Railway CLI installed: `npm install -g @railway/cli`
3. OpenAI API key: https://platform.openai.com/api-keys
4. GitHub repository secrets configured (see below)

## Infrastructure Setup

### Step 1: Authenticate

```bash
railway login
```

### Step 2: Create the project

```bash
railway init
```

Select "Empty Project" when prompted.

### Step 3: Add a persistent volume

In the Railway dashboard:

1. Go to your project
2. Click **+ New** → **Database** → skip, or add the service first
3. Click on your service → **Settings** → **Volumes**
4. Click **Add Volume**
5. Set mount path: `/data/chroma`
6. Size: 1GB (expandable later)

### Step 4: Set environment variables

```bash
railway variables set DEPLOYMENT_PROFILE=railway
railway variables set CHROMADB_PERSIST_DIR=/data/chroma
railway variables set PORT=8000
railway variables set OPENAI_API_KEY=sk-your-key-here
```

Or use the setup script:

```bash
cd infra/railway
chmod +x setup.sh
./setup.sh
```

### Step 5: Deploy

```bash
railway up
```

Railway detects `railway.json` and uses `backend/Dockerfile` with the `openai` profile automatically.

### Step 6: Generate a public domain

```bash
railway domain
```

This creates a `*.up.railway.app` domain. Custom domains are available on paid plans.

### Step 7: Verify

```bash
curl https://your-app.up.railway.app/health
```

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `RAILWAY_TOKEN` | Railway project token (from dashboard → Project → Settings → Tokens) |
| `BACKEND_URL` | Backend URL for smoke tests (e.g., `https://your-app.up.railway.app`) |

## Environment Variables

Set via `railway variables set` or the dashboard:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_PROFILE` | `railway` | Adapter profile selection |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model |
| `CHROMADB_PERSIST_DIR` | `/data/chroma` | Persistent volume mount path |
| `PORT` | `8000` | Railway reads this for routing |
| `CORS_ORIGINS` | localhost defaults | Comma-separated allowed origins |

## Deployment

### Manual deploy

```bash
railway up
```

### Via GitHub Actions

```bash
gh workflow run deploy-railway.yml -f environment=staging
```

### Auto-deploy from GitHub

Railway supports automatic deploys on push. In the dashboard:

1. Go to your service → **Settings** → **Source**
2. Connect your GitHub repository
3. Select the branch (e.g., `main`)
4. Railway will auto-deploy on every push

## Monitoring

```bash
# Live logs
railway logs

# Service status
railway status

# Open shell in container
railway shell

# Open dashboard
railway open
```

## Cost Estimate

| Resource | Monthly Cost |
|----------|-------------|
| Railway Hobby plan (base) | $5 (includes $5 usage credit) |
| Compute (small container, ~$0.000463/min) | ~$3-5 |
| Persistent volume (1GB) | ~$0.25 |
| OpenAI API (light usage) | ~$1-5 |
| **Total** | **~$5-10** |

The Hobby plan's $5 base includes $5 of usage credit, so for light usage the effective compute cost can be near zero.

## Comparison with fly.io

| Feature | fly.io | Railway |
|---------|--------|---------|
| Auto-stop when idle | Yes (Machines) | No (always running) |
| Auto-deploy from GitHub | Via workflow only | Native (connect repo) |
| Volume snapshots | Yes (daily, auto) | Manual |
| CLI simplicity | Moderate | Very simple |
| Custom domains | Free | Hobby plan |
| Cost (light usage) | ~$4-10/mo | ~$5-10/mo |
