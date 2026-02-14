import os
import json
from datetime import datetime, timedelta, timezone

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from logger import logger

load_dotenv()

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", ".")


def fetch_recently_played(sp):
    """Fetch recently played tracks from the last 3 days."""
    three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
    after_ms = int(three_days_ago.timestamp() * 1000)

    logger.info("Fetching recently played tracks from Spotify")
    results = sp.current_user_recently_played(limit=50, after=after_ms)
    items = results.get("items", [])
    logger.info(f"Fetched {len(items)} tracks")
    return items


def convert_to_extended_format(items, username):
    """Convert Spotify API recently played items to the extended streaming history format."""
    records = []
    for item in items:
        track = item.get("track", {})
        album = track.get("album", {})
        artists = album.get("artists", [])
        artist_name = artists[0]["name"] if artists else None

        # Strip milliseconds from timestamp: "2024-01-15T12:34:56.789Z" -> "2024-01-15T12:34:56Z"
        played_at = item.get("played_at", "")
        if "." in played_at:
            played_at = played_at.split(".")[0] + "Z"

        records.append({
            "ts": played_at,
            "username": username,
            "platform": None,
            "ms_played": track.get("duration_ms"),
            "conn_country": None,
            "ip_addr_decrypted": None,
            "user_agent_decrypted": None,
            "master_metadata_track_name": track.get("name"),
            "master_metadata_album_artist_name": artist_name,
            "master_metadata_album_album_name": album.get("name"),
            "spotify_track_uri": track.get("uri"),
            "episode_name": None,
            "episode_show_name": None,
            "spotify_episode_uri": None,
            "reason_start": None,
            "reason_end": None,
            "shuffle": None,
            "skipped": None,
            "offline": None,
            "offline_timestamp": None,
            "incognito_mode": None,
        })
    return records


def write_output(records):
    """Write records to a daily JSON file, merging and deduplicating if the file already exists."""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"Streaming_History_Audio_{today}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    existing = []
    if os.path.exists(filepath):
        logger.info(f"File {filename} already exists, will merge and deduplicate")
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # Merge and deduplicate by (ts, spotify_track_uri)
    seen = set()
    merged = []
    for record in existing + records:
        key = (record.get("ts"), record.get("spotify_track_uri"))
        if key not in seen:
            seen.add(key)
            merged.append(record)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    new_count = len(merged) - len(existing)
    logger.info(f"Wrote {len(merged)} records to {filename} ({new_count} new)")


def main():
    scope = "user-read-recently-played"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    username = sp.current_user().get("id", "unknown")
    logger.info(f"Authenticated as {username}")

    items = fetch_recently_played(sp)
    if not items:
        logger.info("No recently played tracks found")
        return

    records = convert_to_extended_format(items, username)
    write_output(records)
    logger.info("Done")


if __name__ == "__main__":
    main()
