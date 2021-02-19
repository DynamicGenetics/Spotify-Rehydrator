"""Module to read json files and concatenate into one csv file per 'person'
"""
import os
import spotipy
import pandas as pd
import simplejson as json

from tqdm.auto import tqdm  # https://github.com/tqdm/tqdm


# Read in the json files (speed tested this against pd concat - this was faster)
def read_files():
    """Read in all the json files from the ./input/ folder and return one dataframe.
    Files should be prefixed with a unique identifier and '_'. This unique id will then be
    listed against each listening event in the dataframe. """

    data = []  # an empty list to store the json files

    # Get a list of all the files in the input folder
    file_list = os.listdir("./input/")

    # Read each file
    for file in file_list:
        # Get the unique user ID
        person_id = file.split(sep="_")[0]
        # Make the full filepath for reading the file.
        file = os.path.join("input", file)

        # For this file, load the json to a dict, and add the ID as a key/value.
        with open(file) as f:

            loaded_dict = json.load(f)

            for item in loaded_dict:
                item.update({"id": person_id})

        # Add this dict to the list
        data.extend(loaded_dict)  # Read data frame from json file

    # Export this as a dataframe.
    return pd.DataFrame.from_records(data)


def unmatched_tracks(new_tracks: pd.DataFrame):
    """Compares any existing `uri_matched.csv` files with the current tracks to be matched
    and only returns unmatched tracks to save API calls. 

    This function expects a dataframe of two columns 'artistName' and 'trackName'. 
    """
    # It might be that we have already run this before. So first, lets check for an existing file.
    try:
        existing_df = pd.read_csv("./output/uri_matched.csv", sep="\t")
        existing_tracks = existing_df[["artistName", "trackName"]].drop_duplicates()

        # If they are the same then there are no tracks to process.
        if existing_tracks.equals(new_tracks):
            return None
        # If they are different, get the tracks in the current df that aren't in the existing one.
        # These will be the API calls we still need to make.
        else:
            # To find new only tracks, do a left join.
            unmatched = new_tracks.merge(
                existing_tracks,
                on=["artistName", "trackName"],
                how="left",
                indicator=True,
            )
            # Only keep rows which were 'left_only' rather than 'both'
            unmatched = unmatched[unmatched["_merge"] == "left_only"]
            # Keep just the relevant columns when returning the data.
            return unmatched[["artistName", "trackName"]]

    # If the file doesn't exist then we just and process everything :)
    except FileNotFoundError:
        return new_tracks


def add_URI(sp, file: pd.DataFrame):
    """Add the track URI as a column at the end of the dataframe"""

    # Subset the file to only be the artist and track name
    # Then get the unique artist/track combinations to reduce the number of API calls.
    tracks = file[["artistName", "trackName"]].drop_duplicates()

    # Get the unmatched tracks:
    tracks = unmatched_tracks(new_tracks=tracks)

    # Print this to the console.
    print("The total number of unique tracks is {}".format(len(tracks)))

    def get_track(artist, track):
        """Get the track URI by searching the Spotify API for the name and title"""
        results = sp.search(
            q="artist:" + artist + " track:" + track, type="track", market="GB"
        )
        # Return the first result from this search
        return results["tracks"]["items"][0]["uri"]

    # Initialise empty list of trackIDs
    trackIDs = []

    # tqdm is a progress bar
    with tqdm(total=len(tracks.index)) as pbar:
        # For each artist and track name in the dataframe...
        for x, y in tqdm(zip(tracks["artistName"], tracks["trackName"])):

            # Try to get the track and append it to the list.
            try:
                trackIDs.append(get_track(x, y))

            # These errors come up if there are issues with the API
            except IndexError:
                trackIDs.append("NONE")
            except TypeError:
                trackIDs.append("NONE")
            pbar.update(1)  # Update the progress bar

    # Add a new column to the tracks dataframe.
    tracks["trackID"] = ""
    # Attach the track IDS list as a column to the dataframe
    tracks = tracks.assign(trackID=trackIDs)

    # Now we need to match the trackIDs back to the main dataset observations
    matched = pd.merge(file, tracks, how="left", on=["artistName", "trackName"])

    # Return the matched dataframe.
    return matched


def add_features_cols(df: pd.DataFrame):
    """Gets the track features for all the rows in the df based on trackID column."""

    # Get all of the unique trackIDs.
    unique_tracks = df["trackID"]
    unique_tracks = unique_tracks.drop_duplicates().dropna()
    # Print the number of tracks to the console.
    print("The total number of retrieved trackIDs is {}".format(len(unique_tracks)))

    # Init empty list
    feature_dict = []

    def get_features(uri):
        """Get a dictionary of track features from a single URI"""
        features = sp.audio_features(uri)[0]

        if features:  # If 'features' exists then...
            feature_dict.append(features)  # ...append features to the the list.

    # Get the features for each unique track.
    unique_tracks.apply(lambda x: get_features(x))

    # Turn the features dictionary to a dataframe.
    feature_df = pd.DataFrame.from_records(feature_dict)
    feature_df.to_csv("./output/features_alone.csv", sep="\t")

    # Merge this dataframe into the main dataframe so every listening event has associated data.
    df = pd.merge(df, feature_df, how="left", left_on="trackID", right_on="uri")

    return df


def hydrate():
    """Run the re-hydration functionn in the correct order."""

    # URI matching requires a lot of api calls.
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
