# CipherFlow — backend

## Files

- **log_parser.py** — loads raw log files, detects their format
  (`firewall` CSV, `auth` space-delimited, `dns` key=value pipe-delimited),
  and normalizes every line into the shared event schema below. Malformed
  lines (bad IPs, unparsable timestamps, too few fields) are skipped with a
  `[WARNING]` and do not stop the run.
- **quality_validator.py** — re-reads the normalized JSONL and checks every
  record for missing fields, invalid IPs, invalid timestamps, unknown
  `log_type`, and duplicate `event_id`s. Produces a percentage quality
  score and a per-issue breakdown.
- **api.py** — FastAPI app exposing both scripts over HTTP for the
  dashboard (`/api/stats`, `/api/records`, `/api/quality-report`,
  `/api/event/{id}`, `POST /api/run`).

## Normalized schema

| field          | type              | notes                                   |
|----------------|-------------------|------------------------------------------|
| event_id       | string            | generated, unique per record             |
| timestamp      | ISO-8601          | normalized to UTC                        |
| source_ip      | string            | validated IPv4/IPv6                      |
| target_ip      | string \| null    | firewall events only                     |
| user           | string \| null    | auth events only                         |
| action         | string            | e.g. `LOGIN`, `QUERY`, `TCP_CONNECT`     |
| status         | string            | outcome as reported by the source        |
| log_type       | firewall/auth/dns | source format                            |
| original_line  | string            | raw source line, kept for audit          |
| parsed_at      | ISO-8601          | when the parser produced this record     |

## CLI usage

```bash
python log_parser.py <file> [<file> ...] --out outputs/output_normalized.jsonl
python quality_validator.py outputs/output_normalized.jsonl --report outputs/quality_report.json
```

## API

```bash
uvicorn api:app --reload --port 8000
```

| Endpoint                          | Method | Description                          |
|------------------------------------|--------|---------------------------------------|
| `/api/health`                      | GET    | Liveness check                        |
| `/api/run`                         | POST   | Re-run the pipeline on sample_logs/   |
| `/api/records?log_type=&limit=`    | GET    | List normalized events                |
| `/api/event/{event_id}`            | GET    | Fetch a single record                 |
| `/api/stats`                       | GET    | Counts + hourly timeline for charts   |
| `/api/quality-report`              | GET    | Full quality_validator.py report      |
