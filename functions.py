"""
Module containing the 'worker' functions for the rehydration process.
These include input/output and API calls.
"""
import os
import pandas as pd
import simplejson as json

from tqdm.auto import tqdm  # https://github.com/tqdm/tqdm


# Read in the json files (speed tested this against pd concat - this was faster)
def read_files():
    """Read in all the json files from the ./input/ folder and return one dataframe.
    Files should be prefixed with a unique identifier and '_'. This unique id will then be
    listed against each listening event in the dataframe. """

    print("Ok, I'm reading in the JSON files from input.")

    data = []  # an empty list to store the json files

    # Get a list of all the files in the input folder
    file_list = os.listdir("./input/")

    # Read each file
    for file in file_list:
        if file.endswith(".json"):
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

    print("All done, I've read the files.")

    # Export this as a dataframe.
    return pd.DataFrame.from_records(data)


def unmatched_tracks(new_tracks: pd.DataFrame):
    """Compares any existing `uri_matched.csv` files with the current tracks to be matched
    and only returns unmatched tracks to save API calls.

    This function expects a dataframe of two columns 'artistName' and 'trackName'.
    """
    # It might be that we have already run this before. So first, lets check for an existing file.
    try:
        existing_df = pd.read_csv(os.path.join("temp", "uri_matched.csv"), sep="\t")
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


def get_URI(sp, artist, track):
    """Get the track URI by searching the Spotify API for the name and title"""
    results = sp.search(
        q="artist:" + artist + " track:" + track, type="track", market="GB"
    )
    # Return the first result from this search
    return results["tracks"]["items"][0]["uri"]


def add_URI(sp, file: pd.DataFrame):
    """Add the track URI/ID as a column at the end of the dataframe"""

    # Subset the file to only be the artist and track name
    # Then get the unique artist/track combinations to reduce the number of API calls.
    tracks = file[["artistName", "trackName"]].drop_duplicates()

    # Reduce this to just the unmatched tracks
    tracks = unmatched_tracks(new_tracks=tracks)

    # If unmatched_tracks returned empty, then exit here and return the existing file.
    if tracks is None:
        print(
            """There are no new tracks to find so I'm just returning ./temp/uri_matched.csv"""
        )
        return pd.read_csv(os.path.join("temp", "uri_matched.csv"), sep="\t")

    # Print this to the console.
    print(
        "I'm going to search the Spotify API now for {} tracks. I'll keep you updated with a progress bar.".format(
            len(tracks)
        )
    )

    # Initialise empty list of trackIDs
    trackIDs = []

    # tqdm is a progress bar
    with tqdm(total=len(tracks.index)) as pbar:
        # For each artist and track name in the dataframe...
        for artist, track in tqdm(zip(tracks["artistName"], tracks["trackName"])):

            # Try to get the track and append it to the list.
            try:
                trackIDs.append(get_URI(sp, artist, track))

            # These errors come up if there are issues with the API
            except IndexError:
                trackIDs.append("NONE")
            except TypeError:
                trackIDs.append("NONE")

            # Update the progress bar
            pbar.update(1)

    print(
        "Great, I've searched for all the tracks. In total {} did not have a URI returned by the API.".format(
            trackIDs.count("NONE")
        )
    )

    # Add a new empty column to the tracks dataframe.
    tracks["trackID"] = ""
    # Attach the trackIDS list as a column to the dataframe
    tracks = tracks.assign(trackID=trackIDs)

    # Now we need to match the trackIDs back to the main dataset observations
    matched = pd.merge(file, tracks, how="left", on=["artistName", "trackName"])

    # Save it to csv too.
    if not os.path.exists("temp"):
        os.mkdir("temp")
    matched.to_csv(
        os.path.join("temp", "uri_matched.csv"), sep="\t"
    )  # Tab seperated values
    print(
        """I've added the URIs to the original dataset and saved it to the output folder."""
    )

    # Return the matched dataframe.
    return matched


def add_features_cols(sp, df: pd.DataFrame):
    """Gets the track features for all the rows in the df based on trackID column."""

    print("I'm going to search the Spotify API for each track's features now.")

    # Get all of the unique trackIDs.
    unique_tracks = df["trackID"]
    unique_tracks = unique_tracks.drop_duplicates().dropna()
    # Print the number of tracks to the console.
    print("The total number of retrieved trackIDs is {}".format(len(unique_tracks)))

    # Init empty list
    feature_dict = []

    def get_features(sp, uri):
        """Get a dictionary of track features from a single URI, and append to list."""
        features = sp.audio_features(uri)[0]

        if features:  # If 'features' exists then...
            feature_dict.append(features)  # ...append features to the the list.

    # Get the features for each unique track.
    unique_tracks.apply(lambda x: get_features(sp, x))

    # Turn the features dictionary to a dataframe.
    feature_df = pd.DataFrame.from_records(feature_dict)
    # Write the features to the output file.
    feature_df.to_csv(os.path.join("temp", "features_alone.csv"), sep="\t")

    # Merge this dataframe into the main dataframe so every listening event has associated data.
    df = pd.merge(df, feature_df, how="left", left_on="trackID", right_on="uri")

    print("I've found the features and now I'll write them to output/hydrated_data.csv")

    # Write the merged dataframe out.
    # Save it to csv too.
    if not os.path.exists("output"):
        os.mkdir("output")
    df.to_csv(os.path.join("output", "hydrated_data.csv"), sep="\t")

    return df


def hydrate(sp):
    """Run the re-hydration functionn in the correct order."""

    df = read_files()
    df = add_URI(sp, df)
    df = add_features_cols(sp, df)

    return df
