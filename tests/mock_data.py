import pandas as pd

UNMATCHED_NEW_1 = pd.DataFrame(
    {
        "artistName": ["Artist1", "Artist1", "Artist2", "Artist3", "Artist3"],
        "trackName": ["Track A", "Track B", "Track B", "Track C", "Track C"],
    }
)

# To compare against UNMATCHED_NEW_1 (should return Artist1, Track B as unmatched)
UNMATCHED_EXIST_1 = pd.DataFrame(
    {
        "artistName": ["Artist1", "Artist2", "Artist3", "Artist3"],
        "trackName": ["Track A", "Track B", "Track C", "Track C"],
    }
)

# To compare againest UNMATCHED_NEW_1 - should return None
UNMATCHED_EXIST_2 = pd.DataFrame(
    {
        "artistName": ["Artist1", "Artist1", "Artist2", "Artist3", "Artist3"],
        "trackName": ["Track A", "Track B", "Track B", "Track C", "Track C"],
    }
)
