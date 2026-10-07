import base64
import calendar
import json
import os
import time
from urllib import parse, request


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_RECENTLY_PLAYED_URL = "https://api.spotify.com/v1/me/player/recently-played"


def spotify_access_token():
    credentials = base64.b64encode(
        f"{os.environ['SPOTIFY_CLIENT_ID']}:{os.environ['SPOTIFY_CLIENT_SECRET']}".encode()
    ).decode()
    body = parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"]}
    ).encode()
    req = request.Request(
        SPOTIFY_TOKEN_URL,
        data=body,
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with request.urlopen(req) as response:
        return json.load(response)["access_token"]


def recent_listens(access_token):
    after_ms = int((time.time() - 20 * 60) * 1000)
    req = request.Request(
        f"{SPOTIFY_RECENTLY_PLAYED_URL}?{parse.urlencode({'limit': 50, 'after': after_ms})}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with request.urlopen(req) as response:
        return json.load(response).get("items", [])


def koito_payload(items):
    return {
        "listen_type": "import",
        "payload": [
            {
                "listened_at": int(parse_time(item["played_at"])),
                "track_metadata": {
                    "artist_name": item["track"]["artists"][0]["name"],
                    "track_name": item["track"]["name"],
                    "release_name": item["track"]["album"]["name"],
                    "additional_info": {
                        "duration_ms": item["track"]["duration_ms"],
                        "submission_client": "spotify-history-tracker",
                    },
                },
            }
            for item in items
        ],
    }


def parse_time(played_at):
    return calendar.timegm(time.strptime(played_at.split(".")[0], "%Y-%m-%dT%H:%M:%S"))


def submit_to_koito(items):
    if not items:
        print("Spotify returned no recent listens.")
        return
    req = request.Request(
        os.environ["KOITO_URL"].rstrip("/") + "/apis/listenbrainz/1/submit-listens",
        data=json.dumps(koito_payload(items)).encode(),
        method="POST",
        headers={
            "Authorization": f"Token {os.environ['KOITO_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req) as response:
        if response.status != 200:
            raise RuntimeError(f"Koito returned HTTP {response.status}")
    print(f"Submitted {len(items)} Spotify listens to Koito.")


if __name__ == "__main__":
    submit_to_koito(recent_listens(spotify_access_token()))
