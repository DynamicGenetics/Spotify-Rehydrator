import logging
import spotipy
import pandas as pd

from alive_progress import alive_bar  # https://github.com/rsalmei/alive-progress

from secrets import CLIENT_ID, CLIENT_SECRET

# Spotify Developer Credentials
auth = spotipy.oauth2.SpotifyClientCredentials(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET
)

# Set up Spotipy access token
token = auth.get_access_token()
sp = spotipy.Spotify(auth=token)


# Read in the json files.
def read_files(file_list):
    dfs = []  # an empty list to store the data frames

    with alive_bar(len(file_list)) as bar:  # Progress bar
        for file in file_list:
            data = pd.read_json(file)  # read data frame from json file
            dfs.append(data)  # append the data frame to the list
            bar()  # For progress bar

    return pd.concat(dfs, ignore_index=True)


def add_URI(file: pd.DataFrame):
    """Add the track URI as a column at the end of the dataframe"""

    def get_track(artist, track):
        """Get the track URI by searching the API for the name and title"""
        results = sp.search(q="artist:" + artist + " track:" + track, type="track")
        return results["tracks"]["items"][0]["uri"]

    trackIDs = []

    for x, y in zip(file["artistName"], file["trackName"]):
        try:
            trackIDs.append(get_track(x, y))
        except IndexError:
            trackIDs.append("NONE")

    # Set up new column
    file["trackID"] = ""

    return file.assign(trackID=trackIDs)


def add_features_cols(df: pd.DataFrame):
    """Gets the track features for all the rows in the df based on trackID column."""

    def get_features(uri):
        """Get a dictionary of track features from a single URI"""
        features = sp.audio_features(uri)

        # If features is null then assign an empty dictionary
        if not features:
            features = {}

        # Append features to the dict list.
        feature_dict.append(features)

    feature_dict = {}

    unique_tracks = df["trackID"].unique()

    unique_tracks.apply(lambda x: get_features(x))

    feature_df = pd.DataFrame(feature_dict)

    df = df.set_index("trackID").join(feature_df.set_index("uri"))

    return df


def hydrate(file_list):
    df = read_files(file_list)
    logging.info("""I've read the files into a single dataframe""")

    # total_tracks =

    df = add_URI(df)
    logging.info("""I've got the unique ID for each song""")

    df = add_features_cols(df)
    return df


if __name__ == "__main__":
    file_list = (
        "./histories/StreamingHistory0.json",
        "./histories/StreamingHistory1.json",
        "./histories/StreamingHistory2.json",
    )

    len(file_list)

    # df = hydrate(file_list)

    # df.to_pickle("./hydrated_data.pkl")
