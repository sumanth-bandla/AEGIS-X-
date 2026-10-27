import pandas as pd
from services.data_profiler import profile_dataset


def test_profile_basic():
    df = pd.DataFrame({"x": [1, 2, 3, 4], "cat": ["a", "b", "a", "b"]})
    p = profile_dataset(df)
    assert p.row_count == 4
    assert p.column_count == 2
    assert p.duplicate_rows == 0


def test_profile_missing():
    df = pd.DataFrame({"x": [1, None, 3]})
    p = profile_dataset(df)
    assert p.columns[0].missing_count == 1