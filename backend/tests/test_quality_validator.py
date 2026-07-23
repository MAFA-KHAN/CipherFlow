import json
import pathlib
import tempfile
from backend.quality_validator import (
    validate_records,
    check_missing_fields,
    check_ip_validation,
    check_timestamp_anomalies,
    check_duplicates,
    check_suspicious_patterns,
    load_records,
    write_csv_report
)

SAMPLE = pathlib.Path(__file__).resolve().parents[1] / "sample_logs"


def _make_record(overrides=None):
    rec = {
        "event_id": "00000000-0000-4000-8000-000000000001",
        "timestamp": "2026-07-15T10:15:22+00:00",
        "source_ip": "192.168.1.1",
        "target_ip": "192.168.1.254",
        "user": None,
        "action": "ALLOW",
        "status": "success",
        "log_type": "firewall",
        "original_line": "2026-07-15T10:15:22Z,192.168.1.1,192.168.1.254,443,ALLOW,100",
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
    rec = _make_record({"source_ip": None})
    issues = check_missing_fields(rec)
    assert any("missing_field:source_ip" in i for i in issues)

    report = validate_records([rec])
    assert report["flagged_records"] == 1


def test_invalid_ip_detected():
    rec = _make_record({"source_ip": "999.999.999.999"})
    issues = check_ip_validation(rec)
    assert "invalid_source_ip" in issues

    rec_ext = _make_record({"source_ip": "192.168.1.1", "target_ip": "8.8.8.8"})
    issues_ext = check_ip_validation(rec_ext)
    assert "private_ip_in_external_log" in issues_ext


def test_invalid_timestamp_detected():
    rec_bad = _make_record({"timestamp": "not-a-date"})
    issues_bad = check_timestamp_anomalies(rec_bad)
    assert "invalid_timestamp" in issues_bad

    rec_future = _make_record({"timestamp": "2099-01-01T00:00:00+00:00"})
    issues_future = check_timestamp_anomalies(rec_future)
    assert "future_timestamp" in issues_future

    rec_stale = _make_record({"timestamp": "2020-01-01T00:00:00+00:00"})
    issues_stale = check_timestamp_anomalies(rec_stale)
    assert "stale_timestamp_gt_1yr" in issues_stale


def test_duplicate_event_id_detected():
    r1 = _make_record({"_line_num": 1})
    r2 = _make_record({"_line_num": 2})
    dupes = check_duplicates([r1, r2])
    assert "00000000-0000-4000-8000-000000000001" in dupes
    assert dupes["00000000-0000-4000-8000-000000000001"] == [1, 2]


def test_suspicious_patterns_detected():
    rec_impossible = _make_record({"action": "ALLOW", "status": "FAILURE"})
    issues_imp = check_suspicious_patterns(rec_impossible)
    assert "impossible_action_status_combination" in issues_imp

    rec_bytes = _make_record({"original_line": "2026-07-15T10:15:22Z,192.168.1.1,192.168.1.254,443,ALLOW,2000000000000"})
    issues_bytes = check_suspicious_patterns(rec_bytes)
    assert "extreme_byte_count" in issues_bytes

    r_prev = _make_record({"timestamp": "2026-07-15T10:15:22+00:00"})
    r_next = _make_record({"timestamp": "2026-07-15T10:15:22+00:00"})  # 0s diff
    issues_rapid = check_suspicious_patterns(r_next, prev_record=r_prev)
    assert "rapid_sequential_events" in issues_rapid


def test_end_to_end_run():
    rec = _make_record()
    with tempfile.NamedTemporaryFile("w+", suffix=".jsonl", delete=False, encoding="utf-8") as f_jsonl, \
         tempfile.NamedTemporaryFile("w+", suffix=".csv", delete=False, encoding="utf-8") as f_csv:
        f_jsonl.write(json.dumps(rec) + "\n")
        jsonl_path = f_jsonl.name
        csv_path = f_csv.name

    records = load_records(jsonl_path)
    report = validate_records(records)
    write_csv_report(report, csv_path, records)

    assert report["total_records"] == 1
    assert report["quality_score_pct"] == 100.0
    pathlib.Path(csv_path).read_text(encoding="utf-8").startswith("line_number,check_type")
