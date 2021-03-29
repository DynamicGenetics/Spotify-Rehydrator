"""
Tests for classes contained in rehydrator.py
"""

import pytest
import spotipy
import pathlib
import os
import simplejson as json
import pandas as pd

from src.spotifyrehydrator.rehydrate import Track, Tracks

creds = spotipy.oauth2.SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
)

test_data = os.path.join(pathlib.Path(__file__).parent.absolute(), "input")


class TestTrack:
    def setup_method(self):
        self.test_track = Track(artist="David Bowie", name="Heroes", sp_creds=creds)

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
        with open(os.path.join(test_data, "Person002_StreamingHistory.json")) as f:
            data = json.load(f)
        data = pd.DataFrame.from_records(data)
        self.tracks = Tracks(data, sp_creds=creds)

    def test_incorrect_input_columns(self):
        """Try to give Tracks obj a df with incorrect columns."""
        df = pd.DataFrame({"col1": [2, 1, 9, 8, 7, 4], "col2": [0, 1, 9, 4, 2, 3],})
        with pytest.raises(KeyError):
            tracks = Tracks(df, sp_creds=creds)

    def test_get(self):
        data = self.tracks.get(return_all=True)
        assert data.shape[1] == 22


# class TestRehydrator:

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

