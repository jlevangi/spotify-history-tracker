#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="/mnt/fileserver/my_spotify_data/auto"
TODAY_FILE="Streaming_History_Audio_$(date +%F).json"
MOVED_COUNT=0

POD=$(kubectl get pod -n kioto -l app=kioto -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
if [[ -z "$POD" ]]; then
  echo "Error: Kioto pod not found in cluster" >&2
  exit 1
fi

shopt -s nullglob
for src in "$SRC_DIR"/Streaming_History_Audio_*.json; do
  base="$(basename "$src")"
  if [[ "$base" == "$TODAY_FILE" ]]; then
    continue
  fi

  # Check if already in import or import_complete
  if kubectl exec -n kioto "$POD" -- test -e "/etc/koito/import_complete/$base" 2>/dev/null || \
     kubectl exec -n kioto "$POD" -- test -e "/etc/koito/import/$base" 2>/dev/null; then
    continue
  fi

  echo "Copying $base to Kioto import..."
  kubectl cp "$src" "kioto/$POD:/etc/koito/import/$base"
  MOVED_COUNT=$((MOVED_COUNT + 1))
done

if (( MOVED_COUNT > 0 )); then
  echo "Restarting Kioto deployment to trigger import ($MOVED_COUNT file(s) copied)..."
  kubectl rollout restart deployment/kioto -n kioto
  kubectl rollout status deployment/kioto -n kioto --timeout=60s
fi
