from services.report_generator import build_markdown_report, findings_to_csv
from services.evidence_engine import make_finding


def test_markdown_report():
    f = make_finding("t", "data_quality", "s", "m")
    md = build_markdown_report("Title", "data.csv", "rows=2", [f], "none", "ai text")
    assert "Title" in md
    assert f.finding_id in md


def test_findings_csv():
    f = make_finding("t", "data_quality", "s", "m")
    csv = findings_to_csv([f])
    assert "finding_id" in csv