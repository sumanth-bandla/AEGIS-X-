import pandas as pd
from services.data_profiler import profile_dataset
from services.anomaly_detector import detect_all
from services.evidence_engine import profile_to_findings, anomaly_to_findings


def test_profile_to_findings_missing():
    df = pd.DataFrame({"x": [1, None]})
    p = profile_dataset(df)
    findings = profile_to_findings(p)
    assert any("Missing values" in f.title for f in findings)


def test_anomaly_to_findings():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})
    anoms = detect_all(df)
    findings = anomaly_to_findings(anoms, df)
    assert isinstance(findings, list)