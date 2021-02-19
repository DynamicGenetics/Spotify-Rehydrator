"""
Main module to run the rehydrator from.
Imports functions from `functions.py` and API keys from `secrets.py`.
"""

import spotipy

from secrets import CLIENT_ID, CLIENT_SECRET
from functions import 

# Spotify Developer Credentials
auth = spotipy.oauth2.SpotifyClientCredentials(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET
)

# Set up Spotipy access token
token = auth.get_access_token()
sp = spotipy.Spotify(auth=token)


if __name__ == "__main__":
    df = hydrate(sp)

    df.to_pickle("./hydrated_data.pkl")
