# CipherFlow — frontend

A Vite + React dashboard for the CipherFlow pipeline. Black-and-red,
terminal-inspired theme, six routed pages, all backed by the FastAPI
service in `../backend`.

## Pages

| Route         | Page              | Purpose                                            |
|---------------|-------------------|-----------------------------------------------------|
| `/`           | Overview          | Stats, risk gauge, hourly volume chart, source mix, recent events |
| `/firewall`   | Firewall logs     | Firewall events with status filtering               |
| `/auth`       | Authentication    | Auth events with status filtering                    |
| `/dns`        | DNS activity      | DNS events with status filtering                      |
| `/store`      | Normalized store  | Unified schema reference + full record browser with JSON inspector |
| `/validator`  | Quality validator | Quality score, issue breakdown, flagged event list   |

## Run

```bash
npm install
npm run dev
```

Requires the backend running on port 8000 (see `../backend/README.md`) —
`vite.config.js` proxies `/api/*` there in dev.

## Build

```bash
npm run build
```

Outputs static files to `dist/`, deployable to any static host as long as
`/api/*` is reverse-proxied to the FastAPI service.

## Theme

All colors live in `src/theme.css` as CSS variables (`--ink`, `--card`,
`--red`, `--red-dim`, `--amber`, `--green`, `--text`, …) so the palette can
be adjusted from a single file.
