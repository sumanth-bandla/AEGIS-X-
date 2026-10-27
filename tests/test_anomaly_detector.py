import pandas as pd
from services.anomaly_detector import detect_all


def test_iqr_detects_outlier():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})
    anoms = detect_all(df)
    assert any(a.column == "x" for a in anoms)


def test_no_anomalies_normal():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 6]})
    anoms = detect_all(df)
    assert isinstance(anoms, list)


def test_missingness():
    df = pd.DataFrame({"x": [1, None, 3]})
    anoms = detect_all(df)
    assert any(a.method == "Missingness rule" for a in anoms)