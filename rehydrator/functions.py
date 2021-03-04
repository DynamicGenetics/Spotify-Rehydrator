import os
import logging
import pandas as pd
import simplejson as json

from spotipy.oauth2 import SpotifyOAuth
from alive_progress import alive_bar
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Rehydrator:
    """
    Class to iterate through input files, generate full datasets for each listening
    history and save the data to the output folder. Will create output folder if it
    does not exist.

    Example
    -------
    Rehydrator(input_path, output_path, sp).run()
    """

    input_path: str
    output_path: str
    sp_auth: SpotifyOAuth
    _person_ids: list = field(init=False, repr=False)

    def __post_init__(self):
        # When this class is set up get the list of person_ids.
        self._person_ids = self.person_ids()

    def person_ids(self):

        """Get a list of all the participant ids in the input folder.
        Return if None if there are no ids."""

        file_list = os.listdir(self.input_path)
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
                    # ~ should this be "can't find anyone, exiting?"

        if ids:
            return list(ids)
        else:
            return None

    def run(self):

        """Function to run the rehydrator for each 'person' identified"""

        try:
            for person in self._person_ids:
                data = ListeningHistory(
                    input_path=self.input_path, person_id=person, sp_auth=self.sp_auth
                ).rehydrate
                self.save(data, person_id=person)
        except AttributeError:  # NoneType error thrown if no unique people
            data = ListeningHistory(
                input_path=self.input_path, sp_auth=self.sp_auth
            ).rehydrate
            self.save(data)

    def save(self, data, person_id=None):

        """Function to save the rehydrated data out to .tsv. person_id is optional for file naming."""

        # Create an output folder if it doesn't already exist
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

        # If the person_id is not None then write out with the id
        if person_id is not None:
            data.to_csv(
                os.path.join(self.output_path, person_id + "_hydrated.tsv"),
                sep="\t",
                index=False,
                na_rep="NA",
            )
        else:  # Otherwise just write it out
            data.to_csv(
                os.path.join(self.output_path, "hydrated.tsv"),
                sep="\t",
                index=False,
                na_rep="NA",
            )


@dataclass
class ListeningHistory:

    """
    Retrieves the full dataset for an set of input files (which can be prefixed by `person_id`).
    This dataset includes each listening event as a row, with relevant track features attached.

    Attributes
    ----------
        input_path: path to the directory (folder) where the input json files are stored.
        person_id: The unique identifier that files should be consolidated for.
        sp_auth: Spotify Authentication object for API calls.
        _input_data: private attribute, holding the data read from the json files.
        _rehydrated_data: holding the fully rehydrated data.

    Example
    -------
        ListeningHistory(input_path, id, sp).rehydrate()
    """

    input_path: str
    sp_auth: SpotifyOAuth
    person_id: str = None
    _input_data: pd.DataFrame = field(init=False, repr=False)
    _rehydrated_data: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self):
        # When this class is set up, read the input data to _input_data.
        self._input_data = self.input_data()

    def input_data(self) -> pd.DataFrame:

        """Read in the .json files from input folder. If person_id is passed, it will only read
        files that start with the person_id. Returns a dataframe of file content with an
        additional column for person_id if included."""

        data = []  # an empty list to store the json files

        files = os.listdir(self.input_path)

        # If person_id was passed as an argument
        if self.person_id:
            # Read each file
            for file in files:
                if file.startswith(self.person_id):
                    # Make the full filepath for rqeading the file.
                    file = os.path.join(self.input_path, file)

                    # For this file, load the json to a dict.
                    with open(file) as f:
                        data.extend(json.load(f))

        else:
            # Read each file
            for file in files:
                if file.endswith(".json"):
                    # Make the full filepath for reading the file.
                    file = os.path.join(self.input_path, file)
                    # For this file, load the json to a dict.
                    with open(file) as f:
                        loaded_dict = json.load(f)

                    # Add this dict to the list
                    data.extend(loaded_dict)  # Read data frame from json file

        logger.info(
            "---> All done, I've read all the files for {}".format(self.person_id)
        )

        self._from_file = pd.DataFrame.from_records(data)

        return self._from_file

    @property
    def rehydrate(self):

        "Returns the rehydrated dataframe."

        self._rehydrated_data = self.rehydrate_data()
        return self._rehydrated_data

    def rehydrate_data(self) -> pd.DataFrame:

        """Uses the Tracks class to get all of the track IDs and features, then
        joins these on the full listening history data. Returns this complete
        dataset.

        Returns
        -------
        pd.DataFrame
            A dataframe with all track features for each listening event.
        """

        if self.person_id:
            logging.info("---> Rehydrating {}".format(self.person_id))

        track_data = Tracks(
            names=self._input_data[["artistName", "trackName"]], sp_auth=self.sp_auth
        ).full_dataset

        rehydrated_data = pd.merge(
            self._input_data, track_data, how="left", on=["artistName", "trackName"]
        )

        if self.person_id:
            rehydrated_data["personID"] = self.person_id

        return rehydrated_data


@dataclass
class Tracks:
    """
    A class that takes a dataframe of listening events with artistName and trackName,
    and retrieves the trackID and audio features of each track.

    Example
    -------
    Tracks(data, sp).full_dataset

    This will return a pd.Dataframe with feature columns filled for each unique track
    in the original data.
    """

    names: pd.DataFrame
    sp_auth: SpotifyOAuth
    _full_dataset: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self):
        # Set the track information to make sure it contains the right cols and has no duplicates
        self.names = self.names[["artistName", "trackName"]].drop_duplicates()

    @property
    def full_dataset(self):
        self._full_dataset = self.get_features()
        return self._full_dataset

    def get_track_ids(self) -> pd.DataFrame:
        """Iterate through the tracks provided in `names` and get the trackID for each of them."""

        tracks = self.names

        # Print this to the console.
        logger.info(
            """---> I'm going to search the Spotify API now for {} tracks""".format(
                len(tracks)
            )
        )

        # Add a new empty row for the trackID
        tracks["trackID"] = ""

        with alive_bar(len(tracks.index), spinner="dots_recur") as bar:
            # For each artist and track name in the dataframe...
            for i, row in tracks.iterrows():
                tracks["trackID"][i] = Track(
                    artist=tracks["artistName"][i],
                    name=tracks["trackName"][i],
                    sp_auth=self.sp_auth,
                ).spotifyID
                bar()

        return tracks

    def get_features(self) -> pd.DataFrame:
        """Iterate through the trackIDs to get the features for each track.
        Documentation for this endpoint is here
        https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-several-audio-features"""

        tracks = self.get_track_ids()

        # Make a list of IDs without any trackIDs that were missing or errors
        to_find = tracks[~tracks["trackID"].isin(["MISSING", "ERROR"])]
        to_find = tracks["trackID"].to_list()

        feature_dict = []

        for i in range(0, len(to_find), 100):
            features = self.sp_auth.audio_features(to_find[i : i + 100])

            for feature_set in features:
                if feature_set:  # If is is not empty
                    feature_dict.append(
                        feature_set
                    )  # ...append features to the the list.

        # Turn the features set of dicts into a dataframe
        features = pd.DataFrame.from_records(feature_dict)

        # Merge again so we have all of the tracks (including missing ones we deleted earlier.)
        tracks = pd.merge(
            tracks, features, how="left", left_on="trackID", right_on="id"
        )

        tracks.drop(columns=["id", "uri", "track_href", "analysis_url"], inplace=True)

        return tracks


@dataclass
class Track:
    """
    A class that searches for and returns a spotify ID object for a track, given a trackName and
    and artistName.

    Example
    -------
    Track(name, artist, sp_auth).spotifyID

    This will return the top matched Spotify ID as a string.
    """

    name: str
    artist: str
    sp_auth: SpotifyOAuth
    _spotifyID: str = field(init=False, repr=False)

    def track_search(self, remove_char=None) -> str:

        """Get the track ID by searching the Spotify API for the name and title.
        Takes remove_char as a char to remove from the artist and track before
        searching if needed."""

        if remove_char is not None:
            artist = self.artist.replace(remove_char, "")
            track = self.artist.replace(remove_char, "")
        else:
            artist = self.artist
            track = self.name

        results = self.sp_auth.search(
            q="artist:" + artist + " track:" + track, type="track", market="GB",
        )
        # Return the first result from this search
        return results["tracks"]["items"][0]["id"]

    def get_spotifyID(self) -> str:

        """Calls track_search() to get the spotifyID, trying to remove apostrophes
        and dashes if an IndexError is raised. Returns a spotifyID, which is MISSING
        if it cannot be found, or ERROR if the search has raised an unexpected error."""

        try:
            spotifyID = self.track_search()
        except IndexError:
            try:  # remove apostrophes (most common problem)
                spotifyID = self.track_search(remove_char="'")

            except IndexError:
                try:  # remove dash and a space (2nd most common problem)
                    spotifyID = self.track_search(remove_char="- ")

                except IndexError:  # other punctuation / spelling error, ~1.5% spotify records
                    spotifyID = "MISSING"
                    logger.info("---> {} not found.".format((self.artist, self.name)))
        except Exception as e:  # other errors
            spotifyID = "ERROR", e
            logger.info(
                "---> {} caused an error {}.".format((self.artist, self.name), e)
            )

        return spotifyID

    @property
    def spotifyID(self) -> pd.DataFrame:
        self._spotifyID = self.get_spotifyID()
        return self._spotifyID
