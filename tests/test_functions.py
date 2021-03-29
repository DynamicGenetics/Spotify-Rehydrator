"""
Tests for classes contained in rehydrator.py
"""

import pytest
import spotipy
import pathlib
import os
import simplejson as json
import pandas as pd

from src.spotifyrehydrator.rehydrate import Track, Tracks, Rehydrator

INPUT_PEOPLE = os.path.join(pathlib.Path(__file__).parent.absolute(), "input_people")
INPUT_NO_PEOPLE = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "input_no_people"
)

OUTPUT = os.path.join(pathlib.Path(__file__).parent.absolute(), "output")


class TestTrack:
    def setup_method(self):
        self.test_track = Track(
            artist="David Bowie",
            name="Heroes",
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )

    def test_search_results(self):
        results = self.test_track.search_results()
        assert results["tracks"]["items"][0]["id"]  # Make sure ID exists

    def test_extract_results(self):
        "Test that track info is returned, and that objects are the expected types"
        results = self.test_track.search_results()
        track_info = self.test_track._extract_results(results, return_all=True)
        assert isinstance(track_info["returned_track"], str)
        assert isinstance(track_info["returned_artist"], str)
        assert isinstance(track_info["artist_genres"], list)
        assert isinstance(track_info["artist_pop"], int)
        assert isinstance(track_info["audio_features"], dict)

    def test_track_get(self):
        track_info = self.test_track.get()
        assert isinstance(track_info, dict)
        assert isinstance(track_info["trackID"], str)


class TestTracks:
    def setup_method(self):
        with open(os.path.join(INPUT_PEOPLE, "Person002_StreamingHistory.json")) as f:
            data = json.load(f)
        data = pd.DataFrame.from_records(data)
        self.tracks = Tracks(
            data,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )
        self.data = self.tracks.get(return_all=True)

    def test_incorrect_input_columns(self):
        """Try to give Tracks obj a df with incorrect columns."""
        df = pd.DataFrame({"col1": [2, 1, 9, 8, 7, 4], "col2": [0, 1, 9, 4, 2, 3],})
        with pytest.raises(KeyError):
            tracks = Tracks(
                df,
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            )

    def test_returned_column_names(self):
        """Check that the column names are as expected"""
        expected_cols = [
            "artistName",
            "trackName",
            "trackID",
            "returned_artist",
            "artistID",
            "returned_track",
            "danceability",
            "energy",
            "key",
            "loudness",
            "mode",
            "speechiness",
            "acousticness",
            "instrumentalness",
            "liveness",
            "valence",
            "tempo",
            "type",
            "duration_ms",
            "time_signature",
            "genres",
            "popularity",
        ]
        returned_cols = self.data.columns
        assert set(expected_cols) == set(returned_cols)

    def test_artist_data_matched_correctly(self):
        """Check that artist data for the same artists is the same"""
        artist_data = self.data[
            ["artistName", "returned_artist", "artistID", "popularity"]
        ].copy()
        # If the artist matching has been successful, there should only be as many unique rows as there are artists.
        no_artists = len(artist_data["artistName"].unique())
        artist_data.drop_duplicates(inplace=True)
        assert no_artists == artist_data.shape[0]

    def test_all_entries_returned(self):
        """Ensure all artist/track combinations that were input were returned"""
        with open(os.path.join(INPUT_PEOPLE, "Person002_StreamingHistory.json")) as f:
            input_data = json.load(f)
        input_data = pd.DataFrame.from_records(input_data)
        input_data = input_data[["artistName", "trackName"]]
        input_data.drop_duplicates(inplace=True)
        assert input_data.shape[0] == self.data.shape[0]


class TestRehydrator:
    @pytest.mark.parametrize(
        "input, expected",
        [(INPUT_PEOPLE, ["Person001", "Person002"]), (INPUT_NO_PEOPLE, None)],
    )
    def test_read_person_ids(self, input, expected):
        ids = Rehydrator(
            input,
            OUTPUT,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )._person_ids
        assert ids == expected


# @pytest.mark.parametrize(
#     "input,expected",
#     [
#         (
#             [
#                 "person1_StreamingHistory0.json",
#                 "person1_StreamingHistory1.json",
#                 "person2_StreamingHistory0.json",
#             ],
#             ["person1", "person2"],
#         ),
#         (["StreamingHistory0.json", "StreamingHistory1.json"], None),
#     ],
# )
# def test_getids(input, expected):
#     """Assert that the IDs read in from the files are as expected for both
#     IDs and no IDs.
#     """
#     try:
#         assert sorted(get_user_ids(input)) == sorted(expected)
#     except TypeError:  # You can't sort None
#         assert get_user_ids(input) == expected


# @pytest.mark.parametrize(
#     "path, person_id", [(test_data_path, "Person001"), (test_data_path, None)]
# )
# def test_read_rows(path, person_id):
#     """Test that read() generates a dataframe with the expected number of rows."""
#     df = read(path, person_id)

#     print(df)

#     if person_id is None:
#         assert df.shape[0] == 168  # Test data is everything, so 168 entries
#     else:
#         assert df.shape[0] == 112  # If we get here, something's gone wrong.


# @pytest.mark.parametrize(
#     "path, person_id", [(test_data_path, "Person001"), (test_data_path, None)]
# )
# def test_read_cols(path, person_id):
#     """Test that read() generates a dataframe with the expected number of
#     rows and correct columns."""
#     df = read(path, person_id)

#     print(df)

#     if person_id:
#         assert set(df.columns) == set(
#             (["msPlayed", "endTime", "artistName", "trackName", "person_id"])
#         )
#     else:
#         assert set(df.columns) == set(
#             (["msPlayed", "endTime", "artistName", "trackName"])
#         )

