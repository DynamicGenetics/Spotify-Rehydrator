"""
Main module to run the rehydrator from.
Imports functions from `functions.py` and API keys from `secrets.py`.
"""

import logging
import pathlib
import os

from spotipy.oauth2 import SpotifyClientCredentials

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
auth = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

if __name__ == "__main__":

    logger.info("Starting the rehydration now.")

    Rehydrator(
        input_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "input"),
        output_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "output"),
        sp_creds=auth,
    ).run()

    logger.info("Rehydration complete.")
