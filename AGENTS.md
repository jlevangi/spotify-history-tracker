# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: entrypoint that authenticates with Spotify, fetches recent plays, converts to Spotify Extended Streaming History format, and writes daily JSON output.
- `logger.py`: shared logging setup (file + stdout).
- `scripts/spotify_to_koito_import.sh`: optional helper to move finished JSON files and restart Koito import.
- Container files: `Dockerfile`, `docker-compose.yaml`, `docker-compose.build.yaml`.
- Config and docs: `.env.sample`, `requirements.txt`, `README.md`.
- Runtime artifacts (do not treat as source): `Streaming_History_Audio_*.json`, `spotify.log`, `.cache`.

## Build, Test, and Development Commands
- Install deps: `pip3 install -r requirements.txt`
- Run locally: `python3 main.py`
- Pull and run prebuilt container: `docker compose pull && docker compose up -d`
- Build local image: `docker compose -f docker-compose.yaml -f docker-compose.build.yaml build`
- Push image: `docker compose push`

Set up environment first:
- `cp .env.sample .env` and fill Spotify credentials.
- Set `OUTPUT_HOST_DIR` when using Docker so JSON files land on the host.

## Coding Style & Naming Conventions
- Follow Python 3.11 conventions and PEP 8.
- Use 4-space indentation, `snake_case` for functions/variables, and `UPPER_CASE` for constants (for example `OUTPUT_DIR`).
- Keep modules small and single-purpose; prefer clear helper functions like `fetch_recently_played` and `write_output`.
- Preserve UTF-8 JSON output behavior (`ensure_ascii=False`) and stable field names expected by downstream imports.

## Testing Guidelines
- There is no automated test suite yet. Validate changes with focused manual checks:
- `python3 main.py` runs without exceptions.
- Output file `Streaming_History_Audio_<YYYY-MM-DD>.json` is created/updated and deduplicated by `(ts, spotify_track_uri)`.
- Docker path works end-to-end with `docker compose up -d`.

If you add tests, place them under `tests/` and use `test_*.py` naming.

## Commit & Pull Request Guidelines
- Recent commits are short, imperative, and task-focused (`Align export schema...`, `Fix Docker Hub namespace...`).
- Prefer: `<verb> <specific change>`; avoid vague messages like `fix` or `typo`.
- PRs should include:
- What changed and why.
- Any env/config impact (`.env`, Docker image/tag, output paths).
- Manual verification steps and sample command(s) used.
