"""
Tests for classes contained in rehydrator.py
"""

import pytest
import spotipy
import pathlib
import os
import logging
import shutil
import math

import simplejson as json
import pandas as pd

from src.spotifyrehydrator.rehydrate import Track, Tracks, Rehydrator

LOGGER = logging.getLogger(__name__)

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

    def test_missing(self):
        """Check missing tracks are handled correctly."""
        test = Track(
            artist="A track name",
            name="An artist",
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        ).get()

        assert test == {"trackID": "MISSING"}


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
    def test_get_person_ids(self, input, expected):
        """Check all ids given in the folder are reported accurately."""
        ids = Rehydrator(
            input,
            OUTPUT,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )._person_ids
        try:
            assert set(ids) == set(expected)
        except TypeError:
            assert ids == expected

    @pytest.mark.parametrize(
        "person, input, expected",
        [
            ("Person001", INPUT_PEOPLE, 113),
            ("Person002", INPUT_PEOPLE, 9),
            (None, INPUT_NO_PEOPLE, 65),
        ],
    )
    def test_read_data(self, person, input, expected):
        """Check that the data is read as expected"""
        data = Rehydrator(
            input,
            OUTPUT,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )._read_data(person_id=person)

        assert data.shape == (expected, 4)

    @pytest.mark.parametrize(
        "person, input, expected",
        [("Person002", INPUT_PEOPLE, 9), (None, INPUT_NO_PEOPLE, 65),],
    )
    def test_rehydrate(self, person, input, expected):
        data = Rehydrator(
            input,
            OUTPUT,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        ).rehydrate(person_id=person, return_all=True)

        if person is not None:
            assert data["personID"][0] == person

        assert data.shape[0] == expected

    def test_existing_data(self, caplog):
        """We have created output files already for "Person002" in test_rehydrate
        so we should be told that the rehydrator is skipping them."""
        with caplog.at_level(logging.WARNING):
            Rehydrator(
                INPUT_PEOPLE,
                OUTPUT,
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            ).run()
        # Assert we get the correct warning message in the logger.
        assert "Output file for Person002 already exists." in caplog.text

class TestIntegrationPeople:
    """Class to check the whole rehydrator behaves as expected when there are multiple people."""

    def setup_method(self):
        # Delete the current output folder
        if os.path.exists(OUTPUT):
            shutil.rmtree(OUTPUT)
        # Run the rehydrator
        Rehydrator(
            INPUT_PEOPLE,
            OUTPUT,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        ).run(return_all=True)

    def test_outputs_exist(self):
        assert os.path.exists(os.path.join(OUTPUT, "Person001_hydrated.tsv"))
        assert os.path.exists(os.path.join(OUTPUT, "Person002_hydrated.tsv"))

    def test_NA_recorded(self):
        data = pd.read_csv(os.path.join(OUTPUT, "Person001_hydrated.tsv"), sep="\t")
        missing = data[data["trackID"].isin(["MISSING"])]
        assert math.isnan(missing["artistID"].iloc[0])

    def teardown_method(self):
        # Delete the current output folder
        if os.path.exists(OUTPUT):
            shutil.rmtree(OUTPUT)


class TestIntegrationNoPeople:
    """Class to check the whole rehydrator behaves as expected when there are no people."""

    def setup_method(self):
        # Delete the current output folder
        if os.path.exists(OUTPUT):
            shutil.rmtree(OUTPUT)
        # Run the rehydrator
        Rehydrator(
            INPUT_NO_PEOPLE,
            OUTPUT,
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        ).run(return_all=True)

    def test_outputs_exist(self):
        # Check the file exists as expected
        assert os.path.exists(os.path.join(OUTPUT, "hydrated.tsv"))

    def test_NA_recorded(self):
        data = pd.read_csv(os.path.join(OUTPUT, "hydrated.tsv"), sep="\t")
        missing = data[data["trackID"].isin(["MISSING"])]
        assert math.isnan(missing["artistID"].iloc[0])

    def teardown_method(self):
        # Delete the current output folder
        if os.path.exists(OUTPUT):
            shutil.rmtree(OUTPUT)
