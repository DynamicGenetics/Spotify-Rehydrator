"""Tests for any functions involving data manipulation in `functions.py`.
Functions that solely perform API calls are not tested since API functionality is assumed.
"""

import pytest
from functions import unmatched_tracks


class TestUnmatchedTracks:
    def test_unmatched_tracks():
        