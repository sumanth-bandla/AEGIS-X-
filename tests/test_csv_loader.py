import io
import pandas as pd
from services.csv_loader import load_csv


def make_upload(content: bytes):
    class U:
        def read(self):
            return content
    return U()


def test_valid_csv():
    content = b"a,b\n1,2\n3,4\n"
    lr = load_csv(make_upload(content))
    assert lr.ok
    assert lr.df.shape == (2, 2)


def test_empty_file():
    lr = load_csv(make_upload(b""))
    assert not lr.ok


def test_missing_values_warning():
    content = b"a,b\n1,\n3,4\n"
    lr = load_csv(make_upload(content))
    assert lr.ok
    assert lr.df.isna().sum().sum() == 1


def test_duplicate_columns():
    content = b"a,a\n1,2\n"
    lr = load_csv(make_upload(content))
    assert lr.ok
    assert lr.duplicate_columns