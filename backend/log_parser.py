"""
CipherFlow — log_parser.py

Parses firewall, authentication, and DNS security logs and normalizes
them into a single, unified JSON schema so downstream tools (the quality
validator, the dashboard API) never need to know which source produced
a given event.

Usage:
    python log_parser.py <path-to-log-file> [--out outputs/output_normalized.jsonl]
    python log_parser.py sample_logs/sample_firewall_logs.csv
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

FIREWALL_ACTIONS = {"ALLOW", "DENY"}
AUTH_STATUSES = {"SUCCESS", "FAILURE"}
DNS_RESPONSES = {"NOERROR", "NXDOMAIN", "SERVFAIL", "REFUSED"}

SCHEMA_FIELDS = [
    "event_id", "timestamp", "source_ip", "target_ip", "user",
    "action", "status", "log_type", "original_line", "parsed_at",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def generate_event_id() -> str:
    """Return a real UUID4 string for a normalized event."""
    return str(uuid.uuid4())


def current_timestamp() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def normalize_timestamp(raw: Optional[str]) -> Optional[str]:
    """
    Normalize a variety of incoming timestamp formats to ISO-8601 UTC.
    Returns None if the value can't be parsed, so callers can decide
    whether that makes the record invalid.
    """
    if not raw:
        return None
    raw = raw.strip()
    candidates = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def validate_ip(value: str) -> bool:
    """Return True if value is a syntactically valid IPv4/IPv6 address."""
    if not value:
        return False
    try:
        ipaddress.ip_address(value.strip())
        return True
    except ValueError:
        return False


def load_file(path: str) -> list[str]:
    """Read a log file and return its non-empty lines."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")
    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def detect_log_type(lines: list[str]) -> str:
    """
    Sniff the format of a log file from its first non-empty line.
      - key=value pairs joined with '|'  -> dns
      - comma-separated fields           -> firewall
      - space-separated fields           -> auth
    """
    if not lines:
        raise ValueError("Cannot detect log type: file is empty.")

    sample = lines[0]

    if "=" in sample and "|" in sample:
        return "dns"
    if "," in sample:
        return "firewall"
    if " " in sample:
        return "auth"

    raise ValueError(f"Unrecognized log format, first line: {sample!r}")


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #

def parse_firewall(lines: list[str]) -> list[dict]:
    """
    Parse firewall logs.
    Expected CSV format:
        timestamp,source_ip,dest_ip,protocol,action
    Example:
        2026-07-15T10:15:22Z,192.168.1.15,45.33.10.8,TCP,BLOCKED
    """
    records = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        fields = [f.strip() for f in line.split(",")]
        if len(fields) < 6:
            print(f"[WARNING] Skipping malformed firewall line: {line!r}")
            continue

        raw_ts, source_ip, dest_ip, port, action, bytes_transferred = fields[:6]
        timestamp = normalize_timestamp(raw_ts)
        action = action.upper()
        if action not in FIREWALL_ACTIONS:
            action = "DENY" if action in ("BLOCKED", "DROPPED") else "ALLOW"

        if not validate_ip(source_ip):
            print(f"[WARNING] Invalid source IP, skipping: {line!r}")
            continue
        if timestamp is None:
            print(f"[WARNING] Unparseable timestamp, skipping: {line!r}")
            continue

        record = {
            "event_id": generate_event_id(),
            "timestamp": timestamp,
            "source_ip": source_ip,
            "target_ip": dest_ip if validate_ip(dest_ip) else None,
            "user": None,
            "action": action,
            "status": "success",
            "log_type": "firewall",
            "original_line": line,
            "parsed_at": current_timestamp(),
        }
        records.append(record)

    return records


def parse_auth(lines: list[str]) -> list[dict]:
    """
    Parse authentication logs.
    Expected space-separated format:
        timestamp username source_ip action status
    Example:
        2026-07-15T09:12:03Z m.fatima 192.168.1.44 LOGIN SUCCESS
    """
    records = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        fields = line.split()
        if len(fields) < 6:
            print(f"[WARNING] Skipping malformed auth line: {line!r}")
            continue

        raw_date, raw_time, username, host, status, source_ip = fields[:6]
        raw_ts = f"{raw_date} {raw_time}"
        timestamp = normalize_timestamp(raw_ts)
        status = status.upper()
        if status not in AUTH_STATUSES:
            status = "FAILURE" if status in ("FAILED", "LOCKED") else "SUCCESS"

        if not validate_ip(source_ip):
            print(f"[WARNING] Invalid source IP, skipping: {line!r}")
            continue
        if timestamp is None:
            print(f"[WARNING] Unparseable timestamp, skipping: {line!r}")
            continue

        record = {
            "event_id": generate_event_id(),
            "timestamp": timestamp,
            "source_ip": source_ip,
            "target_ip": None,
            "user": username,
            "action": "LOGIN",
            "status": status,
            "log_type": "auth",
            "original_line": line,
            "parsed_at": current_timestamp(),
        }
        records.append(record)

    return records


def parse_dns(lines: list[str]) -> list[dict]:
    """
    Parse DNS query logs.
    Expected pipe-delimited key=value format:
        query_time=2026-07-15T10:23:45Z|client=192.168.1.50|domain=suspicious.example.com|type=A|response=NXDOMAIN
    """
    records = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        fields = {}
        for item in line.split("|"):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            fields[key.strip()] = value.strip()

        client_ip = fields.get("client", "")
        if not validate_ip(client_ip):
            print(f"[WARNING] Invalid client IP, skipping: {line!r}")
            continue

        timestamp = normalize_timestamp(fields.get("query_time"))
        if timestamp is None:
            print(f"[WARNING] Unparseable timestamp, skipping: {line!r}")
            continue

        record = {
            "event_id": generate_event_id(),
            "timestamp": timestamp,
            "source_ip": client_ip,
            "target_ip": None,
            "user": None,
            "action": "QUERY",
            "status": fields.get("response", "unknown").lower(),
            "log_type": "dns",
            "original_line": line,
            "parsed_at": current_timestamp(),
            "domain": fields.get("domain"),
        }
        records.append(record)

    return records


PARSERS = {
    "firewall": parse_firewall,
    "auth": parse_auth,
    "dns": parse_dns,
}


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def save_jsonl(records: list[dict], out_path: str) -> None:
    """Write normalized records to a JSON Lines file, one record per line."""
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


# --------------------------------------------------------------------------- #
# Pipeline / CLI
# --------------------------------------------------------------------------- #

def process_file(path: str) -> list[dict]:
    """Load, detect, and parse a single log file into normalized records."""
    lines = load_file(path)
    log_type = detect_log_type(lines)
    parser = PARSERS[log_type]
    return parser(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="log_parser.py",
        description="Parse firewall, authentication, or DNS logs into a normalized JSONL schema.",
    )
    parser.add_argument(
        "input", nargs="+", help="Path(s) to raw log file(s) (.csv or .txt)"
    )
    parser.add_argument(
        "--out",
        default="outputs/output_normalized.jsonl",
        help="Destination JSONL file (default: outputs/output_normalized.jsonl)",
    )
    args = parser.parse_args()

    all_records: list[dict] = []
    for path in args.input:
        try:
            records = process_file(path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"[ERROR] {path}: {exc}")
            continue
        print(f"  parsed {len(records)} records from {path}")
        all_records.extend(records)

    if not all_records:
        print("[ERROR] No records were parsed from any input file.")
        sys.exit(1)

    save_jsonl(all_records, args.out)
    print(f"Successfully processed {len(all_records)} records -> {args.out}")


if __name__ == "__main__":
    main()
