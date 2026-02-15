"""Headless-friendly Spotify OAuth authentication.

When a valid cached token exists (or can be refreshed), authentication
proceeds silently.  When interactive login is required, the auth URL is
printed to stdout/logs so it can be opened from any device, and a tiny
HTTP server listens on the redirect URI to capture the callback
automatically.
"""

import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from logger import logger

# How long (seconds) to wait for the user to complete browser auth.
AUTH_TIMEOUT = int(os.environ.get("SPOTIFY_AUTH_TIMEOUT", "300"))


def _get_auth_manager(scope: str) -> SpotifyOAuth:
    """Create a SpotifyOAuth manager with open_browser disabled."""
    return SpotifyOAuth(scope=scope, open_browser=False)


def _parse_port_from_redirect_uri(redirect_uri: str) -> int:
    """Extract the port number from the configured redirect URI."""
    parsed = urlparse(redirect_uri)
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return port


def _run_callback_server(auth_manager: SpotifyOAuth) -> str | None:
    """Start a one-shot HTTP server that captures the OAuth callback.

    Returns the full callback URL (with query string) or None on timeout.
    """
    redirect_uri = auth_manager.redirect_uri
    port = _parse_port_from_redirect_uri(redirect_uri)
    path = urlparse(redirect_uri).path or "/"

    result: dict[str, str | None] = {"url": None}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith(path):
                result["url"] = f"http://localhost:{port}{self.path}"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>Authentication successful!</h2>"
                    b"<p>You can close this tab and return to your terminal.</p>"
                    b"</body></html>"
                )
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            # Suppress default stderr logging from BaseHTTPRequestHandler
            pass

    server = HTTPServer(("0.0.0.0", port), CallbackHandler)
    server.timeout = AUTH_TIMEOUT

    # Handle exactly one request (the callback redirect).
    server.handle_request()
    server.server_close()

    return result["url"]


def get_spotify_client(scope: str = "user-read-recently-played") -> spotipy.Spotify:
    """Return an authenticated Spotify client, handling headless auth.

    1. If a cached token is present and valid (or refreshable), use it.
    2. Otherwise, print the auth URL and start a callback server so the
       user can authenticate from any browser.
    """
    auth_manager = _get_auth_manager(scope)

    # Try to use the existing cached token first.
    token_info = auth_manager.cache_handler.get_cached_token()

    if token_info:
        # Token exists — check if it needs a refresh.
        if auth_manager.is_token_expired(token_info):
            logger.info("Cached token expired, attempting refresh...")
            try:
                token_info = auth_manager.refresh_access_token(
                    token_info["refresh_token"]
                )
                logger.info("Token refreshed successfully")
                return spotipy.Spotify(auth_manager=auth_manager)
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                logger.info("Full re-authentication required")
                # Fall through to interactive flow below.
        else:
            logger.info("Using valid cached token")
            return spotipy.Spotify(auth_manager=auth_manager)

    # --- Interactive (but headless-friendly) auth flow ---
    auth_url = auth_manager.get_authorize_url()

    logger.info("=" * 60)
    logger.info("SPOTIFY AUTHENTICATION REQUIRED")
    logger.info("Open this URL in any browser to log in:")
    logger.info("")
    logger.info(f"  {auth_url}")
    logger.info("")
    logger.info(
        f"Waiting up to {AUTH_TIMEOUT}s for authentication callback on "
        f"redirect URI: {auth_manager.redirect_uri}"
    )
    logger.info("=" * 60)

    # Also print to stdout directly so `docker logs` always shows it,
    # even if logging is filtered.
    print(flush=True)
    print("=" * 60, flush=True)
    print("SPOTIFY AUTHENTICATION REQUIRED", flush=True)
    print("Open this URL in any browser to log in:", flush=True)
    print(f"\n  {auth_url}\n", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    callback_url = _run_callback_server(auth_manager)

    if callback_url is None:
        logger.error(
            "Authentication timed out. No callback received within "
            f"{AUTH_TIMEOUT}s. Exiting."
        )
        sys.exit(1)

    # Exchange the authorization code for an access token.
    code = auth_manager.parse_response_code(callback_url)
    try:
        auth_manager.get_access_token(code, as_dict=False)
    except Exception as e:
        logger.error(f"Failed to obtain access token: {e}")
        sys.exit(1)

    logger.info("Authentication successful — token cached for future runs")
    return spotipy.Spotify(auth_manager=auth_manager)
