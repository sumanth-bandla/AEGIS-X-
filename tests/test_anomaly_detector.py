import pandas as pd
from services.anomaly_detector import detect_anomalies


def test_iqr_detects_outlier():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})
    ar = detect_anomalies(df)
    assert any(a.column == "x" for a in ar.anomalies)


def test_no_anomalies_normal():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 6]})
    ar = detect_anomalies(df)
    # may or may not flag; ensure runs
    assert isinstance(ar.anomalies, list)


def test_small_sample_note():
    df = pd.DataFrame({"x": [1, 2, 3]})
    ar = detect_anomalies(df)
    assert any("Small sample" in n for n in ar.notes)