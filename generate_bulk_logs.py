"""
Generate bulk synthetic log files for CipherFlow performance benchmarking.

Usage:
    python generate_bulk_logs.py --records 10000 --out backend/sample_logs/bulk/
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


def gen_firewall(n, base):
    protocols = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS"]
    actions   = ["ALLOWED", "BLOCKED", "DROPPED"]
    return [f"{rnd_ts(base,i*2)},{rnd_ip()},{rnd_ext()},{random.choice(protocols)},{random.choice(actions)}" for i in range(n)]

def gen_auth(n, base):
    users    = ["alice","bob","charlie","diana","evan","fatima","george"]
    actions  = ["LOGIN","LOGOUT","SUDO","SSH"]
    statuses = ["SUCCESS","FAILED","LOCKED"]
    return [f"{rnd_ts(base,i*3)} {random.choice(users)} {rnd_ip()} {random.choice(actions)} {random.choice(statuses)}" for i in range(n)]

def gen_dns(n, base):
    domains   = ["example.com","suspicious.ru","update.microsoft.com","cdn.cloudflare.net","malware-c2.xyz"]
    qtypes    = ["A","AAAA","MX","CNAME","TXT"]
    responses = ["NOERROR","NXDOMAIN","SERVFAIL","REFUSED"]
    return [
        f"query_time={rnd_ts(base,i*2)}|client={rnd_ip()}|domain={random.choice(domains)}|type={random.choice(qtypes)}|response={random.choice(responses)}"
        for i in range(n)
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", type=int, default=1000)
    ap.add_argument("--out", default="backend/sample_logs/bulk")
    args = ap.parse_args()

    out  = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = datetime(2026, 7, 15, tzinfo=timezone.utc)
    n    = args.records

    files = {
        "bulk_firewall_logs.csv": gen_firewall(n, base),
        "bulk_auth_logs.txt":     gen_auth(n, base),
        "bulk_dns_logs.txt":      gen_dns(n, base),
    }

    for fname, rows in files.items():
        (out / fname).write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"  Wrote {len(rows):>6,} records -> {out / fname}")

    print(f"\nDone. {n*3:,} total records across 3 files.")

if __name__ == "__main__":
    main()
