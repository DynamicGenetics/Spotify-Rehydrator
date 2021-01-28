"""Module containing functions to read, concatenate and request data from Spotify from multiple JSON
"""
import os
import spotipy
import pandas as pd
import simplejson as json

from tqdm.auto import tqdm  # https://github.com/tqdm/tqdm

from secrets import CLIENT_ID, CLIENT_SECRET

# Spotify Developer Credentials
auth = spotipy.oauth2.SpotifyClientCredentials(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET
)

# Set up Spotipy access token
token = auth.get_access_token()
sp = spotipy.Spotify(auth=token)


# Read in the json files (speed tested this against pd concat - this was faster)
def read_files():
    """Read in all the json files, and export a single dataframe"""
    data = []  # an empty list to store the json files

    # Get a list of all the files in the input folder
    file_list = os.listdir("./input/")

    for file in file_list:
        file = os.path.join("input", file)
        with open(file) as f:
            data.extend(json.load(f))  # Read data frame from json file

    return pd.DataFrame.from_records(data)


def add_URI(file: pd.DataFrame):
    """Add the track URI as a column at the end of the dataframe"""

    # Subset the file to only be the artist and track name
    # Then get the unique artist/track combinations to reduce the number of API calls.
    tracks = file[["artistName", "trackName"]].drop_duplicates()

    def get_track(artist, track):
        """Get the track URI by searching the API for the name and title"""
        results = sp.search(q="artist:" + artist + " track:" + track, type="track")
        return results["tracks"]["items"][0]["uri"]

    # Initialise empty list of trackIDs
    trackIDs = []

    with tqdm(total=len(tracks.index)) as pbar:
        for x, y in tqdm(zip(tracks["artistName"], tracks["trackName"])):
            try:
                trackIDs.append(get_track(x, y))
            except IndexError:
                trackIDs.append("NONE")
            pbar.update(1)

    tracks["trackID"] = ""
    tracks = tracks.assign(
        trackID=trackIDs
    )  # Attach the track IDS list as a column to the dataframe

    # Now we need to match the trackIDs back to the main dataset observations
    matched = pd.merge(file, tracks, how="left", on=["artistName", "trackName"])

    return matched


def add_features_cols(df: pd.DataFrame):
    """Gets the track features for all the rows in the df based on trackID column."""

    unique_tracks = df["trackID"]
    unique_tracks = unique_tracks.drop_duplicates().dropna()
    print("The total number of unique tracks is {}".format(len(unique_tracks)))

    # Init empty list
    feature_dict = []

    def get_features(uri):
        """Get a dictionary of track features from a single URI"""
        features = sp.audio_features(uri)[0]

        if features:  # If 'features' exists then...
            feature_dict.append(features)  # ...append features to the the list.

    unique_tracks.apply(lambda x: get_features(x))

    feature_df = pd.DataFrame.from_records(feature_dict)
    feature_df.to_csv("./output/features_alone.csv", sep="\t")

    df = pd.merge(df, feature_df, how="left", left_on="trackID", right_on="uri")

    return df


def hydrate():

    try:
        df = pd.read_csv("./output/uri_matched.csv", sep="\t")
        print("I've found an already matched dataset so I will use that.")
        print(df.head())
    except FileNotFoundError:
        print("There is not an existing matched dataset so I will generate one.")
        df = read_files()
        print(
            """I've read the files into a single dataframe. Now I'll process the URIs."""
        )
        df = add_URI(df)
        print("""I've got the unique ID for each song""")
        df.to_csv("./output/uri_matched.csv", sep="\t")  # Tab seperated values
        print("""I've saved the matched dataset to the output folder.""")

    print("Now I am going to find the features of each track")
    df = add_features_cols(df)
    print(
        "I've found all the features and now I'll write them to output/track_features.csv"
    )
    df.to_csv("./output/track_features.csv", sep="\t")

    return df


if __name__ == "__main__":
    df = hydrate()

    df.to_pickle("./hydrated_data.pkl")
