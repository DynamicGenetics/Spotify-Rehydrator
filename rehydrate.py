"""
Main module to run the rehydrator from.
Imports functions from `functions.py` and API keys from `secrets.py`.
"""

import spotipy
import logging

from secrets import CLIENT_ID, CLIENT_SECRET
from functions import rehydrate


def main():
    # Set up logging to print to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Spotify Developer Credentials
    auth = spotipy.oauth2.SpotifyClientCredentials(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )

    # Set up Spotipy access token
    token = auth.get_access_token()
    sp = spotipy.Spotify(auth=token)

    rehydrate(sp)


if __name__ == "__main__":
    main()
