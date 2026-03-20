#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Resume Tailor — Setup Script
# Run once from the Resume Builder directory:
#   bash scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Resume Tailor Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Python venv ────────────────────────────────────────────────────────────
echo ""
echo "1/3  Creating Python virtual environment..."
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "     ✅  .venv created"
else
    echo "     ✅  .venv already exists"
fi

# ── 2. Install dependencies ───────────────────────────────────────────────────
echo ""
echo "2/3  Installing dependencies..."
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r scripts/requirements.txt
echo "     ✅  Dependencies installed"

# ── 3. .env setup ─────────────────────────────────────────────────────────────
echo ""
echo "3/3  Checking .env..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "     ✅  .env created from template — fill in your ANTHROPIC_API_KEY"
else
    echo "     ✅  .env already exists"
fi

# ── Manual steps ──────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  Setup complete. Two manual steps remaining:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  STEP 1 — Enable Google Drive API (one click):"
echo "  https://console.cloud.google.com/apis/library/drive.googleapis.com"
echo "  → Click ENABLE on that page"
echo ""
echo "  STEP 2 — Drop your service account JSON here:"
echo "  $PROJECT_DIR/google-credentials.json"
echo "  (Same account used in your LinkedIn outreach project)"
echo ""
echo "  STEP 3 — Add your Anthropic API key to .env:"
echo "  $PROJECT_DIR/.env"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Then run:"
echo ""
echo "    source .venv/bin/activate"
echo "    python scripts/tailor_resume.py --company 'Acme' --role 'AI Engineer'"
echo ""
echo "  Paste the JD when prompted → get a Google Doc link"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
