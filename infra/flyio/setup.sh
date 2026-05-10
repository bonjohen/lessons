#!/usr/bin/env bash
# Fly.io setup script for Lessons Hub backend
#
# Prerequisites:
#   - flyctl installed: https://fly.io/docs/hands-on/install-flyctl/
#   - Authenticated: flyctl auth login
#   - OpenAI API key ready
#
# Usage:
#   ./setup.sh [app-name] [region]
#
# Cost estimate (~$3-7/month):
#   - shared-cpu-1x 512MB Machine: ~$3-5/month (auto-stop when idle)
#   - 1GB persistent volume: ~$0.15/month
#   - OpenAI API (pay-per-token): ~$1-5/month for light usage

set -euo pipefail

APP_NAME="${1:-lessons-hub}"
REGION="${2:-sea}"

echo "=== Fly.io Setup for Lessons Hub ==="
echo "App:    $APP_NAME"
echo "Region: $REGION"
echo ""

# 1. Create the app (if it doesn't exist)
echo "--- Creating app ---"
flyctl apps create "$APP_NAME" --machines 2>/dev/null || echo "App '$APP_NAME' already exists"

# 2. Create persistent volume for ChromaDB
echo "--- Creating volume for ChromaDB ---"
flyctl volumes create chroma_data \
  --app "$APP_NAME" \
  --region "$REGION" \
  --size 1 \
  2>/dev/null || echo "Volume 'chroma_data' already exists"

# 3. Set secrets
echo "--- Setting secrets ---"
echo "You will be prompted for your OpenAI API key."
read -rsp "OPENAI_API_KEY: " OPENAI_KEY
echo ""

flyctl secrets set \
  --app "$APP_NAME" \
  OPENAI_API_KEY="$OPENAI_KEY"

# Optionally set LESSONS_REPO_TOKEN for private repo harvesting
read -rp "LESSONS_REPO_TOKEN (press Enter to skip): " REPO_TOKEN
if [ -n "$REPO_TOKEN" ]; then
  flyctl secrets set --app "$APP_NAME" LESSONS_REPO_TOKEN="$REPO_TOKEN"
fi

# 4. Deploy
echo ""
echo "--- Deploying ---"
flyctl deploy --app "$APP_NAME"

echo ""
echo "=== Setup Complete ==="
echo "App URL: https://$APP_NAME.fly.dev"
echo "Health:  https://$APP_NAME.fly.dev/health"
echo ""
echo "Useful commands:"
echo "  flyctl status --app $APP_NAME        # Check app status"
echo "  flyctl logs --app $APP_NAME           # View logs"
echo "  flyctl ssh console --app $APP_NAME    # SSH into the machine"
echo "  flyctl volumes list --app $APP_NAME   # Check volume status"
echo "  flyctl scale count 0 --app $APP_NAME  # Stop (save costs)"
echo "  flyctl scale count 1 --app $APP_NAME  # Restart"
