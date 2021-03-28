"""
Main module for the `spotifyrehydrator` package, containing four dataclasses.

`Track` operates on a single Track instance, starting from just a `name` and an `artist`,
as would be provided in self-requested data. It is possible to use `Track` to get information
about a single Track.

`Tracks` contains similar logic as for `Track`, but makes use of the batch endpoints to save on
API calls. Therefore, its more efficient than `Track` for many calls, and works primarily with
Pandas dataframe objects, rather than delivering dictionaries.

`ListeningHistory` encapsulates the data and logic for a single user's listening history, which
includes managing the additional metadata such as datetimes
and repetitions. Before `Tracks` is called to build a dataset the history will be reduced the
set of unique tracks, and then matched back to the meta data for each listening event.

`Rehydrator` is mainly intended to rebuild multiple datasets in instances
when you have many listening histories from multiple different users. The Rehydrator is the
only class which will write files.
"""
import os
import logging
import pandas as pd
import simplejson as json

from spotipy import oauth2, Spotify
from spotipy.exceptions import SpotifyException
from alive_progress import alive_bar
from dataclasses import dataclass, field

# Initialise logger

# Set up logging to print to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@dataclass
class Rehydrator:

    """
    Class to iterate through input files, generate full datasets for each listening
    history and save the data to the output folder. Will create output folder if it
    does not exist.

    Attributes
    ----------
    input_path: path to the directory (folder) where the input json files are stored.
    output_path: path to the directory (folder) where the output .tsv files are saved.
    sp_creds: SpotifyClientCredentials object used to generate _sp_auth.
    _person_ids: Private attribute of each of the unique 'people' files identified for.

    Example
    -------
        ``Rehydrator(input_path, output_path, sp).run()``
    """

    input_path: str
    output_path: str
    sp_creds: oauth2.SpotifyClientCredentials
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

        """Function to run the rehydrator for each 'person' identified."""

        try:
            for person in self._person_ids:
                # Check if the file for this person already exists.
                if os.path.isfile(
                    os.path.join(self.output_path, person + "_hydrated.tsv")
                ):
                    logger.warn(
                        "Output file for {} already exists. Skipping.".format(person)
                    )
                # If it doesn't then carry on.
                else:
                    data = ListeningHistory(
                        input_path=self.input_path,
                        person_id=person,
                        sp_creds=self.sp_creds,
                    ).rehydrate
                    self.save(data, person_id=person)
        except AttributeError:  # NoneType error thrown if no unique people
            data = ListeningHistory(
                input_path=self.input_path, sp_creds=self.sp_creds
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

        logger.info(
            "---> Rehydrated data for {} has been saved to the output folder".format(
                person_id
            )
        )


@dataclass
class ListeningHistory:

    """
    Retrieves the full dataset for a set of input files (which can be prefixed by `person_id`).
    This dataset includes each listening event as a row, with relevant track features attached.

    Attributes
    ----------
    input_path: path to the directory (folder) where the input json files are stored.
    sp_creds: SpotifyClientCredentials object used to generate _sp_auth.
    person_id: The unique identifier that files should be consolidated for.
    _input_data: Private attribute of the data read from the json files.

    Example
    -------
        ``ListeningHistory(input_path, id, sp_auth).rehydrate()``
    """

    input_path: str
    sp_creds: oauth2.SpotifyClientCredentials
    person_id: str = None
    _input_data: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self):
        # When this class is set up, read the input data to _input_data.
        # Also generate a Spotify OAuth object to start with.
        self._input_data = self.input_data()

    def input_data(self) -> pd.DataFrame:

        """Read in the .json files from input folder. If person_id is passed, it will only read
        files that start with the person_id. Returns a dataframe of file content with an
        additional column for person_id if included."""

        data = []  # an empty list to store the json files

        files = os.listdir(self.input_path)

        # If person_id was passed as an argument
        if self.person_id is not None:
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

        logger.info("---> I've read all the files for {}".format(self.person_id))

        self._from_file = pd.DataFrame.from_records(data)

        return self._from_file

    def rehydrate(self) -> pd.DataFrame:

        """Uses the Tracks class to get all of the track IDs and features, then
        joins these on the full listening history data. Returns this complete
        dataset.

        Returns
        -------
        pd.DataFrame
            A dataframe with all track features for each listening event.
        """

        if self.person_id is not None:
            logging.info("---> Rehydrating {}".format(self.person_id))

        track_data = Tracks(
            names=self._input_data[["artistName", "trackName"]], sp_creds=self.sp_creds
        ).full_dataset

        rehydrated_data = pd.merge(
            self._input_data, track_data, how="left", on=["artistName", "trackName"]
        )

        if self.person_id is not None:
            rehydrated_data["personID"] = self.person_id

        return rehydrated_data


@dataclass
class Tracks:

    """
    A class that takes a dataframe of listening events with artistName and trackName,
    and retrieves the trackID and audio features of each track.

    Attributes
    ----------
    names: A dataframe with two columns 'artistName' and 'trackName'.
    sp_creds: SpotifyClientCredentials object used to generate _sp_auth.
    _sp_auth: Spotipy OAuth object for API calls.

    Example
    -------
        ``Tracks(data, sp).full_dataset``

    This will return a pd.Dataframe with feature columns filled for each unique track
    in the original data.
    """

    names: pd.DataFrame
    sp_creds: oauth2.SpotifyClientCredentials
    _sp_auth: oauth2.SpotifyOAuth = field(init=False, repr=False)
    _full_dataset: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self):
        # Set the track information to make sure it contains the right cols and has no duplicates
        self.names = self.names[["artistName", "trackName"]].drop_duplicates()
        # Set the initial Spotify authentication obejct
        self.set_sp()

    @property
    def full_dataset(self):

        """Runs the function required to acquire the full dataset and
        the return it."""

        self._full_dataset = self.get_features()
        return self._full_dataset

    def set_sp(self):

        """Set up the Spotify API authentication object.
        This can also be used to refresh if it expires."""

        logger.info("---> I've (re)set the Spotify API authenticator")
        self._sp_auth = Spotify(auth_manager=self.sp_creds)

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
                try:
                    tracks["trackID"][i] = Track(
                        artist=tracks["artistName"][i],
                        name=tracks["trackName"][i],
                        sp_auth=self._sp_auth,
                    ).spotifyID
                    bar()  # Progress bar
                except SpotifyException:
                    # This should be raised if token expires
                    # Reset the authentication object
                    self.set_sp()
                    # Try again
                    tracks["trackID"][i] = Track(
                        artist=tracks["artistName"][i],
                        name=tracks["trackName"][i],
                        sp_auth=self._sp_auth,
                    ).spotifyID
                    bar()  # Progress bar
                    logger.info("Spotify Token Reset")

        # Report number of found, missing and errors from track search.
        try:
            missing = tracks.trackID.value_counts()["MISSING"]
        except KeyError:
            missing = 0
        try:
            errors = tracks.trackID.value_counts()["ERROR"]
        except KeyError:
            errors = 0
        found = len(tracks) - missing - errors
        logger.info(
            """---> I've searched all the tracks. {} were found. {} are missing. {} threw errors""".format(
                found, missing, errors
            )
        )

        return tracks

    def get_features(self) -> pd.DataFrame:

        """Iterate through the trackIDs to get the features for each track.
        `Documentation for this endpoint is
        here <https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-several-audio-features>`_
        """

        tracks = self.get_track_ids()

        # Make a list of IDs without any trackIDs that were missing or errors
        to_find = tracks[~tracks["trackID"].isin(["MISSING", "ERROR"])]
        to_find = tracks["trackID"].to_list()

        feature_dict = []

        for i in range(0, len(to_find), 100):

            try:
                features = self._sp_auth.audio_features(to_find[i : i + 100])
            except SpotifyException:
                # This should be raised if token expires
                self.set_sp()  # Reset the authentication object
                # Try again
                features = self._sp_auth.audio_features(to_find[i : i + 100])
                logger.info("Spotify Token Reset")

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
    A class that searches for and returns a spotify ID and other optional information for a track,
    given a trackName and and artistName.

    Attributes
    ----------
    name: The name of the track (str).
    artist: The name of the artist (str).
    sp_creds: SpotifyClientCredentials object used to generate an auth object.

    Example
    -------
    .. code-block::
        heroes = Track(name="Heroes", artist="David Bowie", sp_creds=creds)
        # Returns dict with just the SpotifyID
        heroes.get()
        # Returns dict with all requested information
        heroes.get(returned_artist=True, returned_track=True, artist_info=True, audio_features=True)

    """

    name: str
    artist: str
    sp_creds: oauth2.SpotifyClientCredentials

    @property
    def sp_auth(self):
        return Spotify(auth_manager=self.sp_creds)

    def search_results(self, remove_char=None) -> dict:

        """Searches the Spotify API for the track and artist and returns the whole
        results object.

        Takes remove_char as a char to remove from the artist and track before
        searching if needed - this can improve results."""

        if remove_char is not None:
            artist = self.artist.replace(remove_char, "")
            track = self.name.replace(remove_char, "")
        else:
            artist = self.artist
            track = self.name

        results = self.sp_auth.search(
            q="artist:" + artist + " track:" + track, type="track",
        )
        # Return the first result from this search
        return results

    def _get_genre_pop(self, artist_urn):

        """API call to retrieve an artist's genres and popularity.
        Returns a tuple of (genres, popularity)"""

        artist = self.sp_auth.artist(artist_urn)

        genres = artist["genres"]
        pop = artist["popularity"]

        return genres, pop

    def _extract_results(
        self,
        results: dict,
        return_all: bool = False,
        returned_artist: bool = False,
        returned_track: bool = False,
        artist_info: bool = False,
        audio_features: bool = False,
    ):

        """Extract the required data from the results object, based on input arguments."""

        # Initalise object with track info to be returned.
        track_info = {}
        track_info["spotifyID"] = results["tracks"]["items"][0]["id"]

        # TODO: Once a matching alg is written, include as a step here.

        if returned_artist is True or return_all is True:
            # Get the name of the first artist only
            track_info["returned_artist"] = results["tracks"]["items"][0]["artists"][0][
                "name"
            ]

        if returned_track is True or return_all is True:
            # Get the name of the track
            track_info["returned_track"] = results["tracks"]["items"][0]["name"]

        if artist_info is True or return_all is True:
            artist_urn = results["tracks"]["items"][0]["artists"][0]["id"]
            track_info["artist_genres"], track_info["artist_pop"] = self._get_genre_pop(
                artist_urn
            )

        if audio_features is True or return_all is True:
            track_info["audio_features"] = self.sp_auth.audio_features(
                track_info["spotifyID"]
            )[0]

        return track_info

    def get(
        self,
        return_all: bool = False,
        returned_artist: bool = False,
        returned_track: bool = False,
        artist_info: bool = False,
        audio_features: bool = False,
    ) -> dict:

        """Calls search_results() to get the spotifyID, trying to remove apostrophes
        and dashes if an IndexError is raised. Returns a dictionary of objects, with
        spotifyID and then any other objects as defined in function call.

        Parameters
        ------------
        all: bool, default = False
            Run with all optional data arguments as True
        returned_artist: bool, default = False
            Include key of 'returned_artist' with value as exact name of the artist of the returned track.
        returned_track: bool, default = False
            Include key of 'returned_track' with value as exact name of the returned track.
        artist_info: bool, default = False
            Include keys of 'artist_genres' and 'artist_pop' with list of artist's genres and popularity rating
            given by the Spotify API.
        audio_features: bool, default = False
            Include key of 'audio_features' with value as a dict of the results from the audio_features endpoint.
        """

        try:
            results = self.search_results()
        except IndexError:
            try:  # remove apostrophes (most common problem)
                results = self.search_results(remove_char="'")

            except IndexError:
                try:  # remove dash and a space (2nd most common problem)
                    results = self.search_results(remove_char="- ")

                except IndexError:  # other punctuation / spelling error, ~1.5% spotify records
                    logger.info("---> {} not found.".format((self.artist, self.name)))
                    return {"spotifyID": "MISSING"}

        except Exception as e:  # other errors
            logger.info(
                "---> {} caused an error {}.".format((self.artist, self.name), e)
            )
            return {"spotifyID": "ERROR"}

        # Assuming we successfully got some results, extract requested info and return
        return self._extract_results(
            results,
            return_all,
            returned_artist,
            returned_track,
            artist_info,
            audio_features,
        )

