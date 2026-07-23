import json
import pathlib
from backend.quality_validator import validate_records, load_records

SAMPLE = pathlib.Path(__file__).resolve().parents[1] / "sample_logs"


def _make_record(overrides=None):
    rec = {
        "event_id": "evt_abc12345",
        "timestamp": "2026-07-15T10:15:22+00:00",
        "source_ip": "192.168.1.1",
        "target_ip": None,
        "user": None,
        "action": "TCP_CONNECT",
        "status": "BLOCKED",
        "log_type": "firewall",
        "original_line": "dummy",
        "parsed_at": "2026-07-15T10:15:22+00:00",
    }
    if overrides:
        rec.update(overrides)
    return rec


def test_clean_record_passes():
    report = validate_records([_make_record()])
    assert report["quality_score_pct"] == 100.0
    assert report["flagged_records"] == 0


def test_missing_field_detected():
    rec = _make_record({"status": None})
    report = validate_records([rec])
    assert report["flagged_records"] == 1
    issues = report["flagged_events"][0]["issues"]
    assert any("missing_field" in i for i in issues)


def test_invalid_ip_detected():
    rec = _make_record({"source_ip": "999.999.999.999"})
    report = validate_records([rec])
    assert any("invalid_source_ip" in i for e in report["flagged_events"] for i in e["issues"])


def test_invalid_timestamp_detected():
    rec = _make_record({"timestamp": "not-a-date"})
    report = validate_records([rec])
    assert any("invalid_timestamp" in i for e in report["flagged_events"] for i in e["issues"])


def test_duplicate_event_id_detected():
    r1 = _make_record()
    r2 = _make_record()  # same event_id
    report = validate_records([r1, r2])
    all_issues = [i for e in report["flagged_events"] for i in e["issues"]]
    assert "duplicate_event_id" in all_issues
