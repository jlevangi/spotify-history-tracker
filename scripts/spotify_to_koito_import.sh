#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="/mnt/fileserver/my_spotify_data/auto"
DEST_DIR="/home/pierce/docker/kioto/koito-data/import"
TODAY_FILE="Streaming_History_Audio_$(date +%F).json"
MOVED_COUNT=0

mkdir -p "$DEST_DIR"

shopt -s nullglob
for src in "$SRC_DIR"/Streaming_History_Audio_*.json; do
  base="$(basename "$src")"
  if [[ "$base" == "$TODAY_FILE" ]]; then
    continue
  fi

  dest="$DEST_DIR/$base"
  if [[ -e "$dest" ]]; then
    continue
  fi

  mv "$src" "$dest"
  echo "Moved $base"
  MOVED_COUNT=$((MOVED_COUNT + 1))
done

if (( MOVED_COUNT > 0 )); then
  echo "Restarting koito to trigger import"
  docker restart koito >/dev/null
fi
