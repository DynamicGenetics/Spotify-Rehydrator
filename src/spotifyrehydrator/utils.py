"""
Main module for the `spotifyrehydrator` package, containing three dataclasses.

`Track` operates on a single Track instance, starting from just a `name` and an `artist`,
as would be provided in self-requested data. It is possible to use `Track` to get information
about a single Track.

`Tracks` contains similar logic as for `Track`, but makes use of the batch endpoints to save on
API calls. Therefore, its more efficient than `Track` for many calls, and I/O is primarily
Pandas DataFrame objects, rather than dictionaries.

`Rehydrator` is mainly intended to rebuild multiple datasets in instances
when you have many listening histories from multiple different users with additional metadata
such as datetimes. The Rehydrator is the only class which will write files.
"""

import os
import logging
import pandas as pd
import simplejson as json

from spotipy import oauth2, Spotify
from spotipy.exceptions import SpotifyException
from alive_progress import alive_bar
from dataclasses import dataclass, field

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
    client_id: Spotify API client ID Credentials
    client_secret: Spotify API client secret Credentials
    _person_ids: A list of each of the unique 'people' files identified for, or None.

    Example
    -------
        ``Rehydrator(input_path, output_path, sp).run()``
    """

    input_path: str
    output_path: str
    client_id: str
    client_secret: str
    _person_ids: list = field(init=False, repr=False)

    def __post_init__(self):
        # When this class is set up get the list of person_ids.
        self._person_ids = self._person_ids(self.input_path)

    @staticmethod
    def _person_ids(input_path):

        """Get a list of all the participant ids in the input folder.
        Return if None if there are no ids."""

        file_list = os.listdir(input_path)
        # Initialise id list
        ids = set()

        # Get the unique ids for each file.
        for file in file_list:
            if file.endswith(".json"):
                # Get the unique user ID
                name_split = file.split(sep="_")
                # If it has split into 2 parts, take the first part
                if len(name_split) > 1:
                    ids.add(file.split(sep="_")[0])
                # If there are no files with ids then pass
                else:
                    pass

        if ids:
            return list(ids)
        else:
            return None

    def _read_data(self, person_id: str = None) -> pd.DataFrame:

        """
        Read in the .json files from input folder. If person_id is passed, it will only read
        files that start with the person_id. Returns a dataframe of file content with an
        additional column for person_id if included.
        """

        data = []  # an empty list to store the json files

        files = os.listdir(self.input_path)

        # If person_id was passed as an argument
        if person_id is not None:
            # Read each file
            for file in files:
                if file.startswith(person_id):
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

        if person_id is not None:
            logger.info("---> I've read all the files for {}".format(person_id))

        return pd.DataFrame.from_records(data)

    def rehydrate(
        self,
        person_id: str = None,
        return_all: bool = False,
        audio_features: bool = False,
        artist_info: bool = False,
    ) -> pd.DataFrame:

        """
        For a single person's set of data, use the Tracks class to get all of
        the track IDs and features, then join these on the full listening 
        history data. Save out the complete data, and return it too. 

        Parameters
        -----------
        person_id: str = None
        return_all: bool = False
        audio_features: bool = False
        artist_info: bool = False
        """

        if person_id is not None:
            logging.info("---> Rehydrating {}".format(person_id))

        # Read the input data
        input_data = self._read_data(person_id=person_id)

        # Get the data for the individual tracks
        track_data = Tracks(
            data=input_data[["artistName", "trackName"]],
            client_id=self.client_id,
            client_secret=self.client_secret,
        ).get(return_all, audio_features, artist_info)

        # Merge the Tracks data with the listening history metadata
        rehydrated_data = pd.merge(
            input_data, track_data, how="left", on=["artistName", "trackName"]
        )

        # Set a column as the personID
        if person_id is not None:
            rehydrated_data["personID"] = person_id

        # Save out the rehydrated data
        self._save(rehydrated_data, person_id=person_id)

        return rehydrated_data

    def run(
        self,
        return_all: bool = False,
        audio_features: bool = False,
        artist_info: bool = False,
    ) -> None:

        """
        Iterate through each person's set of data by calling the 'rehydrate' method on each.

        Parameters
        -----------
        return_all: bool = False
            Return both audio_features and artist_info
        audio_features: bool = False
            Return each track's audio features. 
            `Spotify documentation available here. <https://developer.spotify.com/documentation/web-api/reference/#object-audiofeaturesobject>`_
        artist_info: bool = False
            Return the popularity and genre list for each track's artist. 
            `Spotify documentation available here. <https://developer.spotify.com/documentation/web-api/reference/#object-artistobject>`_
        """

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
                    self.rehydrate(person, return_all, audio_features, artist_info)
        except TypeError:  # NoneType error thrown if no unique people
            logging.warn(
                "---> No unique identifiers found. Rehydrating all files together."
            )
            self.rehydrate(return_all=return_all, audio_features=audio_features, artist_info=artist_info)

    def _save(self, data: pd.DataFrame, person_id: str = None):

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
            "---> Rehydrated data has been saved to the output folder".format(
                person_id
            )
        )


@dataclass
class Tracks:

    """
    A class that takes a dataframe of listening events with artistName and trackName,
    and returns these with the trackID and audio features of each track as a dataframe.

    Attributes
    ----------
    data: A dataframe with two columns 'artistName' and 'trackName'.
    client_id: Spotify API client ID Credentials
    client_secret: Spotify API client secret Credentials
    _sp_auth: Spotipy OAuth object for API calls.

    Example
    -------
        ``Tracks(data, client_id, client_secret).get(return_all=True)``

    This will return a pd.Dataframe with feature columns filled for each unique track
    in the original data.
    """

    data: pd.DataFrame
    client_id: str
    client_secret: str
    _sp_auth: oauth2.SpotifyOAuth = field(init=False, repr=False)

    def __post_init__(self):
        # Set the track information to make sure it contains the right cols and has no duplicates
        try:
            self.data = self.data[["artistName", "trackName"]].drop_duplicates()
            self.data.reset_index(drop=True, inplace=True)
        except KeyError:
            raise KeyError(
                "Input data does not contain the required columns 'artistName' and 'trackName'."
            )
        # Set the initial Spotify authentication obejct
        self._set_sp()

    def _set_sp(self):

        """Set up the Spotify API authentication object.
        This can also be used to refresh if it expires."""

        logger.info("---> I've (re)set the Spotify API authenticator")
        sp_creds = oauth2.SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.client_secret
        )
        self._sp_auth = Spotify(auth_manager=sp_creds)

    def _get_track_info(self) -> pd.DataFrame:

        """Iterate through the tracks provided in `data` and get basic search info for each of them."""

        # Make a list of dictionaries, one for each track.
        tracks = self.data.to_dict("index")

        # Print this to the console.
        logger.info(
            """---> I'm going to search the Spotify API now for {} tracks""".format(
                len(tracks)
            )
        )

        # Init empty listc
        track_list = []

        with alive_bar(len(tracks), spinner="dots_recur") as bar:
            # For each artist and track name in the dataframe...
            for index, track in tracks.items():
                try:
                    track_info = Track(
                        artist=track["artistName"],
                        name=track["trackName"],
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                    ).get()

                except SpotifyException:
                    # This should be raised if token expires
                    # Reset the authentication object
                    self._set_sp()
                    logger.info("Spotify Token Reset")
                    # Try again
                    track_info = Track(
                        artist=track["artistName"],
                        name=track["trackName"],
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                    ).get()

                # Update the dict in the original list with the new info
                track.update(track_info)
                track_list.append(track)
                # Iterate the progress bar
                bar()

        # Convert the dicts to a dataframe when finished.
        tracks = pd.DataFrame.from_records(track_list)

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

    def _get_audio_features(self, track_ids: list) -> pd.DataFrame:

        """
        Given a list of spotifyIDs, get the features for them all in batches of 100.
        `Documentation for this endpoint is
        here <https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-several-audio-features>`_
        """

        feature_dicts = []

        for i in range(0, len(track_ids), 100):

            try:
                features = self._sp_auth.audio_features(track_ids[i : i + 100])
            except SpotifyException:
                # This should be raised if token expires
                self._set_sp()  # Reset the authentication object
                # Try again
                features = self._sp_auth.audio_features(track_ids[i : i + 100])
                logger.info("Spotify Token Reset")

            for feature_set in features:
                if feature_set:  # If is is not empty
                    feature_dicts.append(
                        feature_set
                    )  # ...append features to the the list.

        # Return the features as a dataframe
        return pd.DataFrame.from_records(feature_dicts)

    def _get_artist_info(self, artist_ids: list) -> pd.DataFrame:

        artist_dicts = []

        for i in range(0, len(artist_ids), 50):

            try:
                artists = self._sp_auth.artists(artist_ids[i : i + 50])

            except SpotifyException:
                # This should be raised if token expires
                self._set_sp()  # Reset the authentication object
                logger.info("Spotify Token Reset")
                # Try again
                artists = self._sp_auth.artists(artist_ids[i : i + 50])

            for artist in artists["artists"]:
                if artist:  # If is is not empty
                    # Add relevant items to the list.
                    artist_dicts.append(
                        dict((k, artist[k]) for k in ("id", "genres", "popularity"))
                    )

        # Return the features as a dataframe
        return pd.DataFrame.from_records(artist_dicts)

    def get(
        self,
        return_all: bool = False,
        audio_features: bool = False,
        artist_info: bool = False,
    ) -> pd.DataFrame:

        """
        Get the requested data for each track. Returns a dataframe of unique tracks. 

        Parameters
        ------------
        return_all: bool, default = False
            Run with all optional data arguments as True
        artist_info: bool, default = False
            Include keys of 'artist_genres' and 'artist_pop' with list of artist's genres and popularity rating
            given by the Spotify API artist end point.
        audio_features: bool, default = False
            Include key of 'audio_features' with value as a dict of the results from the audio_features endpoint.
        """

        # Get the basic track information
        tracks = self._get_track_info()

        # Make a subdf without any trackIDs that were missing or errors.
        to_find = tracks[~tracks["trackID"].isin(["MISSING", "ERROR"])]

        if audio_features or return_all is True:
            trackids = to_find["trackID"].tolist()
            features = self._get_audio_features(track_ids=trackids)

            # Merge again so we have all of the tracks (including missing ones we filtered out earlier).
            tracks = pd.merge(
                tracks, features, how="left", left_on="trackID", right_on="id"
            )

        if artist_info or return_all is True:
            # Make a list of artist IDs.
            artists = to_find["artistID"].unique()
            artist_info = self._get_artist_info(artist_ids=artists.tolist())

            # Merge into the main tracks dataset.
            tracks = pd.merge(
                tracks, artist_info, how="left", left_on="artistID", right_on="id"
            )

        # Drop left over / repeated columns if they are in the dataframe
        leftover_columns = ["uri", "track_href", "analysis_url", "id_x", "id_y"]
        tracks.drop(
            columns=[col for col in tracks if col in leftover_columns], inplace=True
        )

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
    client_id: Spotify API client ID Credentials
    client_secret: Spotify API client secret Credentials
    Example
    -------
    .. code-block::
        heroes = Track(name="Heroes", artist="David Bowie", sp_creds=creds)
        # Returns dict with just the SpotifyID
        heroes.get()
        # Returns dict with all requested information
        heroes.get(return_all=True)

    """

    name: str
    artist: str
    client_id: str
    client_secret: str

    @property
    def sp_auth(self):
        sp_creds = oauth2.SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.client_secret
        )
        return Spotify(auth_manager=sp_creds)

    def search_results(self, remove_char=None) -> dict:

        """
        Searches the Spotify API for the track and artist and returns the whole
        results object.

        Takes remove_char as a char to remove from the artist and track before
        searching if needed - this can improve results.
        """

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

    def _get_artist_info(self, artist_id):

        """API call to retrieve an artist's genres and popularity.
        Returns a tuple of (genres, popularity)"""

        artist = self.sp_auth.artist(artist_id)

        genres = artist["genres"]
        pop = artist["popularity"]

        return genres, pop

    def _extract_results(
        self,
        results: dict,
        return_all: bool = False,
        artist_info: bool = False,
        audio_features: bool = False,
    ):

        """Extract the required data from the results object, based on input arguments."""

        # Initalise object with track info to be returned.
        track_info = {}
        track_info["trackID"] = results["tracks"]["items"][0]["id"]

        # TODO: Once a matching alg is written, include as a step here.

        # Get the name of the first artist only, save this and their unique ID
        try:
            track_info["returned_artist"] = results["tracks"]["items"][0]["artists"][0][
                "name"
            ]
            track_info["artistID"] = results["tracks"]["items"][0]["artists"][0]["id"]
        except IndexError:
            # If these haven't been returned then set as NA
            track_info["returned_artist"], track_info["artistID"] = "NA", "NA"

        # Get the name of the track
        try:
            track_info["returned_track"] = results["tracks"]["items"][0]["name"]
        except IndexError:
            track_info["returned_track"] = "NA"

        if artist_info is True or return_all is True:
            # Get the artist's genres and popularity (requires extra API call)
            try:
                artist_id = results["tracks"]["items"][0]["artists"][0]["id"]
                (
                    track_info["artist_genres"],
                    track_info["artist_pop"],
                ) = self._get_artist_info(artist_id)
            except IndexError:
                track_info["artist_genres"], track_info["artist_pop"] = "NA", "NA"

        if audio_features is True or return_all is True:
            # Get the track's audio features (requires extra API call)
            try:
                track_info["audio_features"] = self.sp_auth.audio_features(
                    track_info["trackID"]
                )[0]
            except IndexError:
                track_info["audio_features"] = "NA"

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
        return_all: bool, default = False
            Run with all optional data arguments as True
        artist_info: bool, default = False
            Include keys of 'artist_genres' and 'artist_pop' with list of artist's genres and popularity rating
            given by the Spotify API artist end point.
        audio_features: bool, default = False
            Include key of 'audio_features' with value as a dict of the results from the audio_features endpoint.
        """

        try:
            results = self.search_results()
            if not results["tracks"]["items"]:  # If the results are empty
                results = self.search_results(remove_char="'")
                if not results["tracks"]["items"]:  # If the results are empty
                    results = self.search_results(remove_char="- ")
                    if not results["tracks"]["items"]:  # If the results are still empty
                        logger.info(
                            "---> {} not found.".format((self.artist, self.name))
                        )
                        return {"trackID": "MISSING"}

        except Exception as e:  # other errors
            logger.info(
                "---> {} caused an error {}.".format((self.artist, self.name), e)
            )
            return {"trackID": "ERROR"}

        # Assuming we successfully got some results, extract requested info and return
        return self._extract_results(results, return_all, artist_info, audio_features)

