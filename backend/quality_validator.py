"""
CipherFlow — quality_validator.py

Runs 5 data-quality checks against normalized JSONL records produced by log_parser.py:
  1. Check Missing Fields (event_id, timestamp, source_ip, action, log_type)
  2. Check IP Validation (IPv4 format, flags private IPs in external logs)
  3. Check Timestamp Anomalies (unparseable, future, >1 year old)
  4. Check Duplicate Detection (duplicate event_ids and line numbers)
  5. Check Suspicious Patterns (impossible action/status, extreme bytes, rapid events)
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REQUIRED_FIELDS = ["event_id", "timestamp", "source_ip", "action", "status", "log_type"]
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
                rec = json.loads(line)
                rec["_line_num"] = i
                records.append(rec)
            except json.JSONDecodeError:
                print(f"[WARNING] Skipping unparsable JSON on line {i}")
    return records


def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False


def is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except (ValueError, AttributeError):
        return False


def parse_iso_ts(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# 5 Validation Check Functions
# --------------------------------------------------------------------------- #

def check_missing_fields(record: dict) -> list[str]:
    issues = []
    for field in REQUIRED_FIELDS:
        val = record.get(field)
        if val is None or val == "":
            issues.append(f"missing_field:{field}")
    return issues


def check_ip_validation(record: dict) -> list[str]:
    issues = []
    src = record.get("source_ip")
    if src:
        if not is_valid_ip(src):
            issues.append("invalid_source_ip")
        elif record.get("log_type") == "firewall" and is_private_ip(src) and record.get("target_ip") and not is_private_ip(record.get("target_ip")):
            issues.append("private_ip_in_external_log")
    
    tgt = record.get("target_ip")
    if tgt and not is_valid_ip(tgt):
        issues.append("invalid_target_ip")
    return issues


def check_timestamp_anomalies(record: dict, ref_time: Optional[datetime] = None) -> list[str]:
    issues = []
    ts_str = record.get("timestamp")
    if not ts_str:
        return issues
    dt = parse_iso_ts(ts_str)
    if dt is None:
        issues.append("invalid_timestamp")
        return issues

    now = ref_time or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    if dt > now:
        issues.append("future_timestamp")
    elif (now - dt).days > 365:
        issues.append("stale_timestamp_gt_1yr")

    return issues


def check_duplicates(records: list[dict]) -> dict[str, list[int]]:
    id_to_lines = defaultdict(list)
    for r in records:
        eid = r.get("event_id")
        line_num = r.get("_line_num", 0)
        if eid:
            id_to_lines[eid].append(line_num)
    return {eid: lines for eid, lines in id_to_lines.items() if len(lines) > 1}


def check_suspicious_patterns(record: dict, prev_record: Optional[dict] = None) -> list[str]:
    issues = []
    action = str(record.get("action", "")).upper()
    status = str(record.get("status", "")).upper()

    # Impossible combinations
    if (action in ("ALLOW", "SUCCESS") and status in ("FAILURE", "FAILED", "BLOCKED")) or \
       (action in ("DENY", "BLOCKED") and status in ("SUCCESS", "SUCCESSFUL")):
        issues.append("impossible_action_status_combination")

    # Byte count check
    orig = record.get("original_line", "")
    if record.get("log_type") == "firewall" and orig:
        parts = orig.split(",")
        if len(parts) >= 6:
            try:
                b = int(parts[5].strip())
                if b < 0 or b > 1_000_000_000_000:
                    issues.append("extreme_byte_count")
            except ValueError:
                pass

    # Rapid sequential events (<1s apart from same source_ip)
    if prev_record and prev_record.get("source_ip") == record.get("source_ip"):
        t1 = parse_iso_ts(prev_record.get("timestamp"))
        t2 = parse_iso_ts(record.get("timestamp"))
        if t1 and t2:
            diff = abs((t2 - t1).total_seconds())
            if diff < 1.0:
                issues.append("rapid_sequential_events")

    return issues


# --------------------------------------------------------------------------- #
# Main Validation Pipeline
# --------------------------------------------------------------------------- #

def validate_records(records: list[dict]) -> dict:
    issues_counter = Counter()
    flagged_events: list[dict] = []
    duplicate_map = check_duplicates(records)

    by_ip_last_record = {}

    for r in records:
        r_issues = []
        eid = r.get("event_id")
        src_ip = r.get("source_ip")

        # Check 1: Missing Fields
        r_issues.extend(check_missing_fields(r))

        # Check 2: IP Validation
        r_issues.extend(check_ip_validation(r))

        # Check 3: Timestamp Anomalies
        r_issues.extend(check_timestamp_anomalies(r))

        # Check 4: Duplicate Detection
        if eid and eid in duplicate_map:
            r_issues.append("duplicate_event_id")

        # Check 5: Suspicious Patterns
        prev_r = by_ip_last_record.get(src_ip) if src_ip else None
        r_issues.extend(check_suspicious_patterns(r, prev_r))
        if src_ip:
            by_ip_last_record[src_ip] = r

        if r_issues:
            for issue in r_issues:
                issues_counter[issue] += 1
            flagged_events.append({
                "event_id": eid,
                "line_number": r.get("_line_num"),
                "log_type": r.get("log_type"),
                "issues": r_issues,
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
        "issue_breakdown": dict(issues_counter),
        "records_by_type": dict(by_type),
        "duplicate_map": duplicate_map,
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
            print(f"  {issue:<35} {count}")


def write_csv_report(report: dict, csv_path: str, records: list[dict]) -> None:
    out_path = Path(csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["line_number", "check_type", "severity", "description", "recommended_action"])

        for event in report["flagged_events"]:
            eid = event.get("event_id", "unknown")
            line_str = str(event.get("line_number", "unknown"))

            for issue in event["issues"]:
                severity = "ERROR"
                action = "Investigate"
                if "missing_field" in issue:
                    severity = "ERROR"
                    action = "Check log source configuration"
                elif "invalid" in issue or "private_ip" in issue:
                    severity = "WARNING"
                    action = "Verify IP extraction regex or network topology"
                elif "timestamp" in issue:
                    severity = "ERROR"
                    action = "Synchronize system clock / fix NTP timestamp formatting"
                elif "duplicate" in issue:
                    severity = "ERROR"
                    action = "Review duplicate event_ids for log source ingestion issues"
                elif "suspicious" in issue or "impossible" in issue or "extreme" in issue or "rapid" in issue:
                    severity = "WARNING"
                    action = "Investigate potential malformed data or security anomaly"

                writer.writerow([line_str, issue, severity, f"Event {eid} issue: {issue}", action])


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="quality_validator.py",
        description="Validate a normalized CipherFlow JSONL file and produce quality reports.",
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
