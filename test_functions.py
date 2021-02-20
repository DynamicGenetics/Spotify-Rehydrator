"""
Tests for any functions involving data manipulation in `functions.py`.
Functions that solely perform API calls are not tested since API functionality is assumed.
"""

import pytest
import os
from functions import get_ids


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
    try:
        assert sorted(get_ids(input)) == sorted(expected)
    except TypeError:  # You can't sort None
        assert get_ids(input) == expected

