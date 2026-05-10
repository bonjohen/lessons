#!/usr/bin/env bash
# Railway setup script for Lessons Hub backend
#
# Prerequisites:
#   - Railway CLI installed: npm install -g @railway/cli
#   - Authenticated: railway login
#   - OpenAI API key ready
#
# Usage:
#   ./setup.sh
#
# Cost estimate (~$5-10/month):
#   - Railway Hobby plan: $5/month (includes $5 usage credit)
#   - Compute: ~$0.000463/min (~$3-5/month for a small service)
#   - Volume storage: $0.25/GB/month
#   - OpenAI API (pay-per-token): ~$1-5/month for light usage

set -euo pipefail

echo "=== Railway Setup for Lessons Hub ==="
echo ""

# 1. Initialize the project
echo "--- Initializing Railway project ---"
railway init 2>/dev/null || echo "Project already initialized"

# 2. Create a persistent volume for ChromaDB
echo "--- Creating volume for ChromaDB ---"
echo "Note: Railway volumes are created via the dashboard or CLI."
echo "Create a volume mounted at /data/chroma in the Railway dashboard."
echo "  Dashboard → Service → Settings → Volumes → Add Volume"
echo "  Mount path: /data/chroma"
echo "  Size: 1GB"
echo ""
read -rp "Press Enter once the volume is configured..."

# 3. Set environment variables
echo "--- Setting environment variables ---"
railway variables set DEPLOYMENT_PROFILE=railway
railway variables set CHROMADB_PERSIST_DIR=/data/chroma
railway variables set PORT=8000

echo "Setting secrets..."
read -rsp "OPENAI_API_KEY: " OPENAI_KEY
echo ""
railway variables set OPENAI_API_KEY="$OPENAI_KEY"

read -rp "LESSONS_REPO_TOKEN (press Enter to skip): " REPO_TOKEN
if [ -n "$REPO_TOKEN" ]; then
  railway variables set LESSONS_REPO_TOKEN="$REPO_TOKEN"
fi

# 4. Deploy
echo ""
echo "--- Deploying ---"
railway up

echo ""
echo "=== Setup Complete ==="
DOMAIN=$(railway domain 2>/dev/null || echo "<check Railway dashboard>")
echo "App URL: https://$DOMAIN"
echo "Health:  https://$DOMAIN/health"
echo ""
echo "Useful commands:"
echo "  railway status           # Check deployment status"
echo "  railway logs             # View logs"
echo "  railway shell            # Open shell in container"
echo "  railway variables        # List environment variables"
echo "  railway down             # Stop service (save costs)"
echo "  railway up               # Redeploy"
