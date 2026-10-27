from services.evidence_engine import Finding
from services.report_generator import build_markdown_report, findings_to_csv


def test_markdown_report():
    f = Finding(finding_id="F1", title="t", finding_type="data_quality", summary="s", metric="m")
    md = build_markdown_report("Title", "data.csv", "rows=2", [f], "none", "ai text")
    assert "Title" in md
    assert "F1" in md


def test_findings_csv():
    f = Finding(finding_id="F1", title="t", finding_type="data_quality", summary="s", metric="m")
    csv = findings_to_csv([f])
    assert "finding_id" in csv