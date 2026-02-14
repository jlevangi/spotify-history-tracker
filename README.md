# Spotify History Tracker

Automate the process of capturing your Spotify streaming history into a PostgreSQL database. This script has two primary features:

- **Fetches recently played songs and adds it into the database**. Perfect for running on a cronjob.
- **Process all your "extended streaming history"** JSON file, querying all tracks, artists and albums and adding them into the database.

More about Spotify specific topics later.

If you're interested in build a data warehouse, this [other repository](https://github.com/mtrentz/spotify-tracker-warehouse) contains dbt models for this specific PostgreSQL schema.

# Installation and configuration

- Clone the repo
- Rename `.env.sample` to `.env` and fill in your PostgresSQL and Spotify credentials
- Install requirements: `pip3 install -r requirements.txt`

**Query your recently played songs:**

```
python3 main.py --recently-played
```

**Add your Extended Streaming History**

- Request your Extended Streaming History from Spotify
- Place all JSON files in `./streaming_history`
  - Only works for "Audio" files. Podcasts, videos and others are not supported.
- Run the script.

```
python3 main.py --extended-history
```

**IMPORTANT**: Requesting a large streaming history can take a lot of time and get your API key blocked for a while. If you're requesting data for a large period of time it might be necessary to run the script over multiple days.

# Docker

- Copy `.env.sample` to `.env` and fill in Spotify credentials.
- Set `IMAGE_NAME` to your Docker Hub image tag (for example `yourname/spotify-history-tracker:latest`).
- Set `OUTPUT_HOST_DIR` to where files should be written on your host.
  - In WSL/Linux, this must be an absolute Linux path (for example `/mnt/c/Users/...`).
- Build the container:

```
docker compose build
```

- Run the container:

```
docker compose up
```

- Output files are written directly to `OUTPUT_HOST_DIR` on your host machine.

## Push To Docker Hub

```
docker login
docker compose build
docker compose push
```

## Run Elsewhere (Without Source Code)

Use an env file on the target host with Spotify credentials and set `OUTPUT_HOST_DIR` to a host path.

```
docker run --rm \
  --env-file /path/to/.env \
  -e OUTPUT_DIR=/app/output \
  -v /absolute/host/output/path:/app/output \
  yourname/spotify-history-tracker:latest
```

# Spotify Data and Credentials

- You can request your API Keys in the [Spotify Developer Dashboard](https://developer.spotify.com/)
- Your Extended Streaming History can be obtained in your Spotify Profile page via the Web
  - Go into Profile --> Account --> Privacy Settings --> Request Extended Streaming History
  - Spotify usually takes a few weeks to email you the history
