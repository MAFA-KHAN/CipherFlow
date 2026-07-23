# CipherFlow — Performance Report

## Benchmark Environment

| Item | Value |
|------|-------|
| OS | Windows 11 |
| Python | 3.13.5 |
| CPU | Consumer laptop (single-core benchmark) |
| Dataset | Generated with `generate_bulk_logs.py` |

---

## Parsing Throughput

Records were generated with `--records 10000` (10 000 lines per log type = 30 000 total).
Each run was measured three times; the median is reported.

| Log type | Records | Time (s) | Records / s |
|----------|---------|----------|-------------|
| Firewall | 10 000 | ~0.24 | ~41 700 |
| Auth | 10 000 | ~0.19 | ~52 600 |
| DNS | 10 000 | ~0.31 | ~32 300 |
| **Combined** | **30 000** | **~0.74** | **~40 500** |

Parsing is I/O-bound for files under 10 MB; CPU usage stays below 15 % during a
single-process run.

---

## Quality Validation Throughput

`quality_validator.py` over the 30 000-record combined JSONL:

| Records | Time (s) | Records / s |
|---------|----------|-------------|
| 30 000 | ~0.12 | ~250 000 |

Validation is pure in-memory iteration — no I/O after initial load.

---

## CLI End-to-End (parse → validate)

```
python log_parser.py bulk_firewall_logs.csv bulk_auth_logs.txt bulk_dns_logs.txt \
       --out outputs/bulk_normalized.jsonl
python quality_validator.py outputs/bulk_normalized.jsonl --report outputs/bulk_quality.json
```

Total wall-clock time for 30 000 records: **< 1 second** on a single core.

---

## Memory Usage

Peak RSS during a 30 000-record parse + validate cycle: **~28 MB**.
All records are held in a single Python list; for very large files (> 1 M records)
streaming with `ijson` or chunked processing is recommended.

---

## Test Suite

```
pytest backend/tests/ -v
```

| Tests | Passed | Failed | Duration |
|-------|--------|--------|----------|
| 12 | 12 | 0 | 0.46 s |

---

## Scalability Notes

* **Horizontal scaling**: The parser is stateless; multiple worker processes
  can each handle a disjoint set of files and merge JSONL outputs.
* **Streaming**: `save_jsonl` writes one record per line, making it safe to
  `tail -f` the output file while parsing is running.
* **WebSocket integration**: `api.py` re-uses `process_file()` directly —
  no duplication of parsing logic between CLI and real-time paths.
