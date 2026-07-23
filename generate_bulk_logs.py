"""
Generate bulk synthetic log files for CipherFlow performance benchmarking.

Usage:
    python generate_bulk_logs.py --records 5000 --out backend/sample_logs/bulk/
"""
import argparse
import random
import pathlib
from datetime import datetime, timedelta, timezone


def rnd_ip():
    return f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"

def rnd_ext():
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def rnd_ts(base, offset):
    return (base + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")

def rnd_date_time(base, offset):
    dt = base + timedelta(seconds=offset)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")


def gen_firewall(n, base):
    actions = ["ALLOW", "DENY"]
    ports = [22, 80, 443, 53, 3389, 8080]
    rows = []
    for i in range(n):
        ts = rnd_ts(base, i * 2)
        src = rnd_ip()
        dst = rnd_ext()
        port = random.choice(ports)
        act = random.choice(actions)
        b = random.randint(64, 1048576) if act == "ALLOW" else 0
        rows.append(f"{ts},{src},{dst},{port},{act},{b}")
    return rows


def gen_auth(n, base):
    users = ["alice_web", "bob_db", "charlie_dev", "diana_admin", "evan_hr", "fatima_sec"]
    hosts = ["corporate-vpn", "internal-db", "dev-server", "jump-host", "hr-portal"]
    statuses = ["SUCCESS", "FAILURE"]
    rows = []
    for i in range(n):
        d, t = rnd_date_time(base, i * 3)
        user = random.choice(users)
        host = random.choice(hosts)
        st = random.choice(statuses)
        src = rnd_ip()
        rows.append(f"{d} {t} {user} {host} {st} {src}")
    return rows


def gen_dns(n, base):
    domains = ["example.com", "suspicious.ru", "update.microsoft.com", "cdn.cloudflare.net", "malware-c2.xyz"]
    qtypes = ["A", "AAAA", "MX", "CNAME", "TXT"]
    responses = ["NOERROR", "NXDOMAIN", "SERVFAIL", "REFUSED"]
    rows = []
    for i in range(n):
        ts = rnd_ts(base, i * 2)
        client = rnd_ip()
        domain = random.choice(domains)
        qtype = random.choice(qtypes)
        res = random.choice(responses)
        rows.append(f"query_time={ts}|client={client}|domain={domain}|type={qtype}|response={res}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", type=int, default=5000)
    ap.add_argument("--out", default="backend/sample_logs/bulk")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = datetime(2026, 7, 15, tzinfo=timezone.utc)
    n = args.records

    files = {
        "bulk_firewall_logs.csv": gen_firewall(n, base),
        "bulk_auth_logs.txt": gen_auth(n, base),
        "bulk_dns_logs.txt": gen_dns(n, base),
    }

    for fname, rows in files.items():
        (out / fname).write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"  Wrote {len(rows):>6,} records -> {out / fname}")

    print(f"\nDone. {n*3:,} total records across 3 files.")


if __name__ == "__main__":
    main()
