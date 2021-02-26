"""
Main module to run the rehydrator from.
Imports functions from `functions.py` and API keys from `secrets.py`.
"""

import spotipy
import logging
import pathlib
import os

from secrets import CLIENT_ID, CLIENT_SECRET
from functions import Rehydrator

# Set up logging to print to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Spotify Developer Credentials
auth = spotipy.oauth2.SpotifyClientCredentials(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET
)

# Set up Spotipy access token
token = auth.get_access_token()
sp = spotipy.Spotify(auth=token)


if __name__ == "__main__":

    logger.info("Starting the rehydration now.")

    Rehydrator(
        input_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "input"),
        output_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "output"),
        sp_auth=sp,
    ).run()

    logger.info("Rehydration complete.")
