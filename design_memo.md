# CipherFlow — Design Memo

**Author:** CipherFlow Engineering  
**Date:** 2026-07-23  
**Status:** Final

---

## 1. Problem Statement

Security teams produce three structurally incompatible log formats
(firewall CSV, auth space-separated, DNS pipe-delimited key=value).
Analysts and dashboards downstream must handle all three, creating
brittle format-specific code scattered across multiple tools.

CipherFlow solves this with a **single normalisation layer** that
converts any supported format into one unified JSON schema.

---

## 2. Architecture

```
Raw logs (CSV / TXT)
        │
        ▼
 log_parser.py          ← single source of truth
  ├─ detect_log_type()
  ├─ parse_firewall()
  ├─ parse_auth()
  ├─ parse_dns()
  └─ save_jsonl()
        │
   ┌────┴────────────────┐
   │                     │
   ▼                     ▼
CLI (argparse)     FastAPI WebSocket
                    (api.py)
        │
        ▼
 quality_validator.py   ← validates normalized JSONL
        │
        ▼
  quality_report.json + console output
```

The parser is invoked identically from the CLI and the live WebSocket
endpoint — no duplicated logic.

---

## 3. Normalized Schema

Every event, regardless of source, is emitted as:

```json
{
  "event_id":     "evt_abc1234567",
  "timestamp":    "2026-07-15T10:15:22+00:00",
  "source_ip":    "192.168.1.15",
  "target_ip":    "45.33.10.8",
  "user":         null,
  "action":       "TCP_CONNECT",
  "status":       "BLOCKED",
  "log_type":     "firewall",
  "original_line":"2026-07-15T10:15:22Z,192.168.1.15,45.33.10.8,TCP,BLOCKED",
  "parsed_at":    "2026-07-23T06:00:00+00:00"
}
```

Fields not applicable to a log type are set to `null`, never omitted,
so downstream consumers can always reference any key safely.

---

## 4. Quality Validation (5 checks)

| # | Check | Trigger |
|---|-------|---------|
| 1 | Missing required field | Any of `event_id`, `timestamp`, `source_ip`, `action`, `status`, `log_type` is null/empty |
| 2 | Invalid source IP | `source_ip` is present but not a valid IPv4/IPv6 address |
| 3 | Invalid timestamp | `timestamp` cannot be parsed by `datetime.fromisoformat()` |
| 4 | Unrecognised log type | `log_type` not in `{firewall, auth, dns}` |
| 5 | Duplicate event_id | Same `event_id` seen more than once in a single file |

Results are written to `outputs/quality_report.json` and printed to stdout
with a PASS/FAIL-style quality score.

---

## 5. Design Decisions

**Why JSONL, not JSON array?**  
JSONL is streamable. Consumers can begin reading before the write completes,
and the file remains valid if the process is killed mid-write.

**Why sniff log type instead of requiring a flag?**  
The assignment specifies automatic detection. The heuristic (pipe+equals →
DNS, commas → firewall, spaces → auth) is unambiguous for the given formats.

**Why not Pandas / Polars?**  
The parser is a library used by both CLI and WebSocket. Introducing a
heavy data-frame dependency would inflate the Docker image and add import
latency to each WebSocket connection. Pure stdlib is sufficient for the
throughput requirements (> 40 000 records/s).

---

## 6. Testing

12 unit tests cover:
- Log-type auto-detection (3 tests)
- Parser output schema (3 tests)
- Multi-file process_file() (1 test)
- Validator: clean record, missing field, bad IP, bad timestamp, duplicate ID (5 tests)

Run with: `pytest backend/tests/ -v`
