"""
Tests for any functions involving data manipulation in `functions.py`.
Functions that solely perform API calls are not tested since API functionality is assumed.
"""

import pytest
import pathlib
import os

from rehydrator.functions import Track

test_data_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "input")


@pytest.mark.parametrize(
    "input,expected",
    [
        (
            [
                "person1_StreamingHistory0.json",
                "person1_StreamingHistory1.json",
                "person2_StreamingHistory0.json",
            ],
            ["person1", "person2"],
        ),
        (["StreamingHistory0.json", "StreamingHistory1.json"], None),
    ],
)
def test_getids(input, expected):
    """Assert that the IDs read in from the files are as expected for both
    IDs and no IDs.
    """
    try:
        assert sorted(get_user_ids(input)) == sorted(expected)
    except TypeError:  # You can't sort None
        assert get_user_ids(input) == expected


@pytest.mark.parametrize(
    "path, person_id", [(test_data_path, "Person001"), (test_data_path, None)]
)
def test_read_rows(path, person_id):
    """Test that read() generates a dataframe with the expected number of rows."""
    df = read(path, person_id)

    print(df)

    if person_id is None:
        assert df.shape[0] == 168  # Test data is everything, so 168 entries
    else:
        assert df.shape[0] == 112  # If we get here, something's gone wrong.


@pytest.mark.parametrize(
    "path, person_id", [(test_data_path, "Person001"), (test_data_path, None)]
)
def test_read_cols(path, person_id):
    """Test that read() generates a dataframe with the expected number of
    rows and correct columns."""
    df = read(path, person_id)

    print(df)

    if person_id:
        assert set(df.columns) == set(
            (["msPlayed", "endTime", "artistName", "trackName", "person_id"])
        )
    else:
        assert set(df.columns) == set(
            (["msPlayed", "endTime", "artistName", "trackName"])
        )


@pytest.mark.parametrize(
    "new, existing, rows_out",
    [
        (UNMATCHED_NEW_1, UNMATCHED_EXIST_1, 1),
        (UNMATCHED_NEW_1, UNMATCHED_EXIST_2, None),
    ],
)
def test_unmatched_tracks(new, existing, rows_out):
    to_match = unmatched_tracks(new_df=new, existing_df=existing)

    try:
        print(to_match)
        assert to_match.shape[0] == rows_out
    except AttributeError as e:  # Raised if df is None
        if rows_out is None:
            pass  # If it's supposed to be None then no problem!
        else:  # Otherwise, raise it.
            raise e

