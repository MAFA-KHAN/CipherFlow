"""
CipherFlow — quality_validator.py

Runs a set of data-quality checks against the normalized JSONL produced
by log_parser.py and reports a score plus a breakdown of every issue
found, so problems in upstream sources are caught before they reach
analysts or the dashboard.

Usage:
    python quality_validator.py outputs/output_normalized.jsonl
    python quality_validator.py outputs/output_normalized.jsonl --report outputs/quality_report.json
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REQUIRED_FIELDS = [
    "event_id", "timestamp", "source_ip", "action", "status", "log_type",
]
VALID_LOG_TYPES = {"firewall", "auth", "dns"}


def load_records(path: str) -> list[dict]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Normalized file not found: {path}")

    records = []
    with file_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[WARNING] Skipping unparsable JSON on line {i}")
    return records


def is_valid_ip(value) -> bool:
    if not value:
        return False
    try:
        ipaddress.ip_address(str(value))
        return True
    except ValueError:
        return False


def is_valid_timestamp(value) -> bool:
    if not value:
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_records(records: list[dict]) -> dict:
    """
    Run all quality checks and return a structured report.
    Every record is checked for: missing fields, invalid IP format,
    invalid/unparsable timestamp, unrecognized log_type, and duplicate
    event_id across the file.
    """
    issues = Counter()
    flagged_events: list[dict] = []
    seen_ids: set[str] = set()

    for record in records:
        record_issues = []

        for field in REQUIRED_FIELDS:
            if record.get(field) in (None, ""):
                record_issues.append(f"missing_field:{field}")

        source_ip = record.get("source_ip")
        if source_ip is not None and not is_valid_ip(source_ip):
            record_issues.append("invalid_source_ip")

        timestamp = record.get("timestamp")
        if timestamp is not None and not is_valid_timestamp(timestamp):
            record_issues.append("invalid_timestamp")

        log_type = record.get("log_type")
        if log_type not in VALID_LOG_TYPES:
            record_issues.append("unrecognized_log_type")

        event_id = record.get("event_id")
        if event_id:
            if event_id in seen_ids:
                record_issues.append("duplicate_event_id")
            else:
                seen_ids.add(event_id)

        if record_issues:
            for issue in record_issues:
                issues[issue] += 1
            flagged_events.append({
                "event_id": event_id,
                "log_type": log_type,
                "issues": record_issues,
            })

    total = len(records)
    clean = total - len(flagged_events)
    score = round((clean / total) * 100, 2) if total else 0.0

    by_type = Counter(r.get("log_type", "unknown") for r in records)

    return {
        "total_records": total,
        "clean_records": clean,
        "flagged_records": len(flagged_events),
        "quality_score_pct": score,
        "issue_breakdown": dict(issues),
        "records_by_type": dict(by_type),
        "flagged_events": flagged_events,
    }


def print_summary(report: dict) -> None:
    print("CipherFlow — Data Quality Report")
    print("=" * 40)
    print(f"Total records     : {report['total_records']}")
    print(f"Clean records      : {report['clean_records']}")
    print(f"Flagged records    : {report['flagged_records']}")
    print(f"Quality score      : {report['quality_score_pct']}%")
    print()
    print("By log type:")
    for log_type, count in report["records_by_type"].items():
        print(f"  {log_type:<10} {count}")
    if report["issue_breakdown"]:
        print()
        print("Issue breakdown:")
        for issue, count in report["issue_breakdown"].items():
            print(f"  {issue:<25} {count}")


def write_csv_report(report: dict, csv_path: str, records: list[dict]) -> None:
    import csv
    
    out_path = Path(csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # We need line_number, check_type, severity, description, recommended_action
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["line_number", "check_type", "severity", "description", "recommended_action"])
        
        # Build mapping of event_id to line number
        event_to_line = {}
        for i, r in enumerate(records, start=1):
            if r.get("event_id"):
                if r["event_id"] not in event_to_line:
                    event_to_line[r["event_id"]] = []
                event_to_line[r["event_id"]].append(i)
                
        for event in report["flagged_events"]:
            eid = event["event_id"]
            line_nums = event_to_line.get(eid, ["unknown"])
            line_str = " & ".join(map(str, line_nums))
            
            for issue in event["issues"]:
                severity = "ERROR"
                action = "Investigate"
                if "missing_field" in issue:
                    severity = "ERROR"
                    action = "Check log source configuration"
                elif "invalid_source_ip" in issue:
                    severity = "WARNING"
                    action = "Verify IP extraction regex or source data"
                elif "invalid_timestamp" in issue:
                    severity = "ERROR"
                    action = "Fix timestamp formatting"
                elif "duplicate_event_id" in issue:
                    severity = "ERROR"
                    action = "Review duplicate event_ids for log source issues"
                elif "unrecognized_log_type" in issue:
                    severity = "WARNING"
                    action = "Update parser to support new log types"
                    
                writer.writerow([line_str, issue, severity, f"Event {eid} has issue: {issue}", action])

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="quality_validator.py",
        description="Validate a normalized CipherFlow JSONL file and produce a quality report.",
    )
    parser.add_argument("input", help="Path to the normalized JSONL file")
    parser.add_argument(
        "--report",
        default="outputs/quality_report.json",
        help="Destination path for the JSON quality report",
    )
    parser.add_argument(
        "--csv-report",
        default="outputs/quality_report.csv",
        help="Destination path for the CSV quality report",
    )
    args = parser.parse_args()

    try:
        records = load_records(args.input)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    report = validate_records(records)

    out_path = Path(args.report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    write_csv_report(report, args.csv_report, records)

    print_summary(report)
    print(f"\nFull JSON report written to {args.report}")
    print(f"Full CSV report written to {args.csv_report}")

if __name__ == "__main__":
    main()
