"""
Module containing the 'worker' functions for the rehydration process.
These include input/output and API calls.
"""
import os
import pathlib
import logging
import pandas as pd
import simplejson as json

from tqdm.auto import tqdm  # https://github.com/tqdm/tqdm

logger = logging.getLogger(__name__)


def get_ids(file_list: list):
    """Get a list of all the participant ids in the input folder.
    Write them to a.txt file in the temp folder. Return if None if
    there are no ids."""

    # Initialise id list
    ids = set()

    # Get the unique ids for each file.
    for file in file_list:
        if file.endswith(".json"):
            # Get the unique user ID
            name_split = file.split(sep="_")
            # If it has split into 2 parts
            if len(name_split) > 1:
                ids.add(file.split(sep="_")[0])
            # If there are no files with ids then pass
            else:
                pass

    if ids:
        return list(ids)
    else:
        return None


def read(path, person_id=None):
    """Read in the .json files from input folder. If person_id is passed, it will only read
    files that start with the person_id. Returns a dataframe of file content with an
    additional column for person_id if included."""

    data = []  # an empty list to store the json files

    files = os.listdir(path)

    # If person_id was passed as an argument
    if person_id:
        # Read each file
        for file in files:
            if file.startswith(person_id):
                # Make the full filepath for rqeading the file.
                file = os.path.join(path, file)

                # For this file, load the json to a dict, and add the ID as a key/value.
                with open(file) as f:
                    loaded_dict = json.load(f)
                    # Add person_id as a key/value.
                    for item in loaded_dict:
                        item.update({"person_id": person_id})

                # Add this dict to the list
                data.extend(loaded_dict)  # Read data frame from json file

    else:
        # Read each file
        for file in files:
            if file.endswith(".json"):
                # Make the full filepath for reading the file.
                file = os.path.join(path, file)
                # For this file, load the json to a dict.
                with open(file) as f:
                    loaded_dict = json.load(f)

                # Add this dict to the list
                data.extend(loaded_dict)  # Read data frame from json file

    logger.info("---> All done, I've read all the files.")

    # Export this as a dataframe.
    return pd.DataFrame.from_records(data)


def unmatched_tracks(new_tracks: pd.DataFrame, person_id=None):
    """Compares any existing `uri_matched.tsv` files with the current tracks to be matched
    and only returns unmatched tracks to save API calls.

    This function expects a dataframe of two columns 'artistName' and 'trackName'.
    """
    # It might be that we have already run this before. So first, lets check for an existing file.
    try:
        if person_id:
            existing_df = pd.read_csv(
                os.path.join("temp", person_id + "_uri_matched.tsv"), sep="\t"
            )
        else:
            existing_df = pd.read_csv(os.path.join("temp", "uri_matched.tsv"), sep="\t")
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


def add_URI(sp, file: pd.DataFrame, person_id=None):
    """Add the track URI/ID as a column at the end of the dataframe"""

    # Subset the file to only be the artist and track name
    # Then get the unique artist/track combinations to reduce the number of API calls.
    tracks = file[["artistName", "trackName"]].drop_duplicates()

    # Reduce this to just the unmatched tracks
    tracks = unmatched_tracks(tracks, person_id)

    # If unmatched_tracks returned empty, then exit here and return the existing file.
    if tracks is None:
        logger.info(
            """---> There are no new tracks to find so I'm just returning the existing file."""
        )
        if person_id:
            return pd.read_csv(
                os.path.join("temp", person_id + "_uri_matched.tsv"), sep="\t"
            )
        else:
            return pd.read_csv(os.path.join("temp", "uri_matched.tsv"), sep="\t")

    # Print this to the console.
    logger.info(
        """---> I'm going to search the Spotify API now for {} tracks""".format(
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

    logger.info(
        "---> I've searched for all the tracks. In total {} did not have a URI returned by the API.".format(
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

    if person_id:
        matched.to_csv(
            os.path.join("temp", person_id + "_uri_matched.tsv"), sep="\t", index=False
        )  # Tab seperated values
    else:
        matched.to_csv(
            os.path.join("temp", "uri_matched.tsv"), sep="\t", index=False
        )  # Tab seperated values
    logger.info(
        """---> I've added the URIs to this dataset and saved it to the output folder."""
    )

    # Return the matched dataframe.
    return matched


def add_features_cols(sp, df: pd.DataFrame, person_id=None):
    """Gets the track features for all the rows in the df based on trackID column."""

    logger.info(
        "---> I'm going to search the Spotify API for each track's features now."
    )

    # Get a list of the unique trackIDs.
    unique_tracks = df["trackID"]
    unique_tracks = unique_tracks.drop_duplicates().dropna()
    unique_tracks = unique_tracks.to_list()

    # Print the number of tracks to the console.
    logger.info(
        "---> The total number of retrieved trackIDs is {}".format(len(unique_tracks))
    )

    # Init empty list
    feature_dict = []

    def get_features(sp, uri_list):
        """Get a dictionary of track features from a list of URI, and append to list.
        Documentation for this endpoint is here
        https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-several-audio-features"""
        features = sp.audio_features(uri_list)

        for feature_set in features:
            if feature_set:  # If is is not empty
                feature_dict.append(feature_set)  # ...append features to the the list.

    # Get the features for each unique track. Iterate in batches of 100 because the audio_features API
    # can handle batches up to that size.
    for i in tqdm(range(0, len(unique_tracks), 100)):
        get_features(sp, unique_tracks[i : i + 100])

    # Turn the features dictionary to a dataframe.
    feature_df = pd.DataFrame.from_records(feature_dict)
    # Write the features to the output file.
    if person_id:
        feature_df.to_csv(
            os.path.join("temp", person_id + "_uri_to_features.tsv"),
            sep="\t",
            index=False,
        )
    else:
        feature_df.to_csv(
            os.path.join("temp", "uri_to_features.tsv"), sep="\t", index=False
        )

    # Merge this dataframe into the main dataframe so every listening event has associated data.
    df = pd.merge(df, feature_df, how="left", left_on="trackID", right_on="uri")

    logger.info(
        "---> I've found the features and now I'll write them to the output folder"
    )

    # Write the merged dataframe out.
    # Save it to csv too.
    if not os.path.exists("output"):
        os.mkdir("output")

    if person_id:
        df.to_csv(
            os.path.join("output", person_id + "_hydrated.tsv"), sep="\t", index=False
        )
    else:
        df.to_csv(os.path.join("output", "hydrated.tsv"), sep="\t", index=False)

    return df


def run_pipeline(sp, person_id=None):
    """Run the re-hydration functions in the correct order."""

    if person_id:
        logging.info("Rehydrating {}".format(person_id))

    df = read(
        path=os.path.join(pathlib.Path(__file__).parent.absolute(), "input"),
        person_id=person_id,
    )
    df = add_URI(sp, df, person_id)
    df = add_features_cols(sp, df, person_id)

    if person_id:
        logger.info("---> Finished {}.".format(person_id))


def rehydrate(sp):

    # Get ids by passing the list of files in the sub-folder input (relative to this file)
    ids = get_ids(
        os.listdir(os.path.join(pathlib.Path(__file__).parent.absolute(), "input"))
    )

    # If there are no seperate participants the run the pipeline with no participant_id
    if ids is None:
        if not os.path.isfile(os.path.join("output", "hydrated.tsv")):
            run_pipeline(sp)
        else:
            logger.info(
                """There is already a hydrated.tsv file in output. Remove this
            file if you want to run the rehydrator again for new data."""
            )
    else:  # Otherwise, iterate over all the participants.
        for index, person_id in enumerate(ids, start=1):

            # Print update on how many there are to go
            logger.info("{} of {}".format(index, len(ids)))

            if not os.path.isfile(os.path.join("output", person_id + "_hydrated.tsv")):
                run_pipeline(sp, person_id)
            else:
                logger.info(
                    "Skipping {}. Output file already exists.".format(person_id)
                )

    logger.info("Rehydration complete.")
