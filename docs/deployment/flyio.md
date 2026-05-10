# Fly.io Deployment

## Architecture

- **Backend:** Fly Machine (shared-cpu-1x, 512MB) running FastAPI container
- **Embeddings:** OpenAI text-embedding-3-small (API)
- **Chat model:** OpenAI gpt-4o-mini (API)
- **Vector store:** ChromaDB on persistent volume (1GB)
- **CI/CD:** GitHub Actions with Fly.io API token

## Prerequisites

1. Fly.io account: https://fly.io/app/sign-up
2. flyctl CLI installed: https://fly.io/docs/flyctl/install/
3. OpenAI API key: https://platform.openai.com/api-keys
4. GitHub repository secrets configured (see below)

## Infrastructure Setup

### Step 1: Authenticate

```bash
flyctl auth login
```

### Step 2: Run the setup script

```bash
cd infra/flyio
chmod +x setup.sh
./setup.sh lessons-hub sea
```

The script will:
- Create the Fly app
- Create a 1GB persistent volume for ChromaDB
- Prompt for your OpenAI API key and set it as a secret
- Deploy the backend container

### Step 3: Verify

```bash
curl https://lessons-hub.fly.dev/health
```

### Step 4: Index the corpus

After the first deploy, you need to build and embed the RAG corpus. SSH into the machine and run:

```bash
flyctl ssh console --app lessons-hub
cd /app
python -m scripts.build_rag_corpus
```

Or trigger the corpus build via the API if that endpoint is enabled.

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `FLY_API_TOKEN` | Fly.io API token (from `flyctl tokens create deploy`) |
| `BACKEND_URL` | Backend URL for smoke tests (e.g., `https://lessons-hub.fly.dev`) |

## Environment Variables

Set via `flyctl secrets set` or in `fly.toml` `[env]` section:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_PROFILE` | `flyio` | Set in fly.toml |
| `OPENAI_API_KEY` | — | OpenAI API key (set as secret) |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model |
| `CHROMADB_PERSIST_DIR` | `/data/chroma` | Persistent volume mount path |
| `CORS_ORIGINS` | localhost defaults | Comma-separated allowed origins |

## Deployment

### Manual deploy

```bash
flyctl deploy
```

### Via GitHub Actions

```bash
gh workflow run deploy-flyio.yml -f environment=staging
```

## Scaling

```bash
# Stop the machine (save costs when not in use)
flyctl scale count 0 --app lessons-hub

# Start it back up
flyctl scale count 1 --app lessons-hub

# Scale up memory (if needed for larger corpus)
flyctl scale memory 1024 --app lessons-hub
```

## Volume Management

ChromaDB data persists across deploys on the mounted volume:

```bash
# List volumes
flyctl volumes list --app lessons-hub

# Extend volume size
flyctl volumes extend <volume-id> --size 3

# Snapshots (automatic daily, 5-day retention)
flyctl volumes snapshots list <volume-id>
```

## Monitoring

```bash
# Live logs
flyctl logs --app lessons-hub

# App status
flyctl status --app lessons-hub

# Metrics
curl https://lessons-hub.fly.dev/metrics
```

## Cost Estimate

| Resource | Monthly Cost |
|----------|-------------|
| Fly Machine (shared-cpu-1x, 512MB, auto-stop) | ~$3-5 |
| Persistent volume (1GB) | ~$0.15 |
| OpenAI API (light usage) | ~$1-5 |
| **Total** | **~$4-10** |

Machines auto-stop when idle and auto-start on incoming requests, keeping costs low for staging/light usage.
