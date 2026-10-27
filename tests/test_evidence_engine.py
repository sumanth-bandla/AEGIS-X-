from services.evidence_engine import make_finding, build_findings_from_profile
import pandas as pd
from services.data_profiler import profile_dataset


def test_make_finding_id():
    f = make_finding("t", "data_quality", "s", "m")
    assert f.finding_id.startswith("F-")


def test_build_findings_missing():
    df = pd.DataFrame({"x": [1, None]})
    p = profile_dataset(df)
    findings = build_findings_from_profile(p, df)
    assert any("Missing values" in f.title for f in findings)