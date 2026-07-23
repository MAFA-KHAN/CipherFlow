import pathlib
from backend.log_parser import detect_log_type, parse_firewall, parse_auth, parse_dns, process_file

SAMPLE = pathlib.Path(__file__).resolve().parents[1] / "sample_logs"


def test_detect_log_type_firewall():
    assert detect_log_type(["2026-07-15T10:15:22Z,192.168.1.15,45.33.10.8,TCP,BLOCKED"]) == "firewall"


def test_detect_log_type_auth():
    assert detect_log_type(["2026-07-15T09:12:03Z user1 192.168.1.44 LOGIN SUCCESS"]) == "auth"


def test_detect_log_type_dns():
    assert detect_log_type(["query_time=2026-07-15T10:23:45Z|client=192.168.1.50|domain=example.com|type=A|response=NXDOMAIN"]) == "dns"


def test_parse_firewall():
    records = parse_firewall((SAMPLE / "sample_firewall_logs.csv").read_text().splitlines())
    assert isinstance(records, list) and len(records) > 0
    assert records[0]["log_type"] == "firewall"
    assert "event_id" in records[0]


def test_parse_auth():
    records = parse_auth((SAMPLE / "sample_auth_logs.txt").read_text().splitlines())
    assert isinstance(records, list) and len(records) > 0
    assert records[0]["log_type"] == "auth"
    assert "user" in records[0]


def test_parse_dns():
    records = parse_dns((SAMPLE / "sample_dns_logs.txt").read_text().splitlines())
    assert isinstance(records, list) and len(records) > 0
    assert records[0]["log_type"] == "dns"
    assert "domain" in records[0]


def test_process_file_combines_multiple():
    all_records = []
    for fname in ["sample_firewall_logs.csv", "sample_auth_logs.txt", "sample_dns_logs.txt"]:
        all_records.extend(process_file(str(SAMPLE / fname)))
    types = {r["log_type"] for r in all_records}
    assert types == {"firewall", "auth", "dns"}
