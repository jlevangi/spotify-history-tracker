#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Running Spotify history sync..."
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/main.py"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Checking for completed history to import into Kioto..."
"$SCRIPT_DIR/scripts/spotify_to_koito_import.sh"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Sync finished."
