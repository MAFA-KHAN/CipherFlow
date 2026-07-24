import pathlib
from backend.log_parser import (
    detect_log_type,
    parse_firewall,
    parse_auth,
    parse_dns,
    process_file,
    normalize_timestamp,
    validate_ip
)

SAMPLE = pathlib.Path(__file__).resolve().parents[1] / "sample_logs"

FW_LINE  = "2026-07-15T10:15:22Z,192.168.1.15,45.33.10.8,443,ALLOW,1024"
AU_LINE  = "2026-07-15 10:23:45 alice_web corporate-vpn SUCCESS 203.0.113.45"
DNS_LINE = "query_time=2026-07-15T10:23:45Z|client=192.168.1.50|domain=example.com|type=A|response=NXDOMAIN"


def test_detect_log_type_firewall():
    assert detect_log_type([FW_LINE]) == "firewall"


def test_detect_log_type_auth():
    assert detect_log_type([AU_LINE]) == "auth"


def test_detect_log_type_dns():
    assert detect_log_type([DNS_LINE]) == "dns"


def test_parse_firewall():
    records = parse_firewall((SAMPLE / "sample_firewall_logs.csv").read_text().splitlines())
    assert isinstance(records, list) and len(records) > 0
    assert records[0]["log_type"] == "firewall"
    assert "event_id" in records[0]
    assert records[0]["action"] in ("ALLOW", "DENY")


def test_parse_auth():
    records = parse_auth((SAMPLE / "sample_auth_logs.txt").read_text().splitlines())
    assert isinstance(records, list) and len(records) > 0
    assert records[0]["log_type"] == "auth"
    assert "user" in records[0]
    assert records[0]["status"] in ("SUCCESS", "FAILURE")


def test_parse_dns():
    records = parse_dns((SAMPLE / "sample_dns_logs.txt").read_text().splitlines())
    assert isinstance(records, list) and len(records) > 0
    assert records[0]["log_type"] == "dns"
    assert "domain" in records[0]


def test_normalize_timestamp():
    assert normalize_timestamp("2026-07-15T10:15:22Z") == "2026-07-15T10:15:22Z"
    assert normalize_timestamp("2026-07-15 10:23:45") == "2026-07-15T10:23:45Z"
    assert normalize_timestamp("not-a-timestamp") is None


def test_validate_ip():
    assert validate_ip("192.168.1.1") is True
    assert validate_ip("2001:db8::1") is True
    assert validate_ip("999.999.999.999") is False
    assert validate_ip("badip") is False


def test_malformed_line_skipped_gracefully():
    malformed_lines = [
        "short,csv",
        "2026-07-15T10:15:22Z,badip,45.33.10.8,443,ALLOW,1024"
    ]
    records = parse_firewall(malformed_lines)
    assert len(records) == 0


def test_process_file_combines_multiple():
    all_records = []
    for fname in ["sample_firewall_logs.csv", "sample_auth_logs.txt", "sample_dns_logs.txt"]:
        all_records.extend(process_file(str(SAMPLE / fname)))
    types = {r["log_type"] for r in all_records}
    assert types == {"firewall", "auth", "dns"}
