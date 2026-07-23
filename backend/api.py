"""
CipherFlow — api.py

Refactored FastAPI layer with in-memory store, real-time log ingestion simulator,
custom attack scenarios, and live notifications feed.
"""

from __future__ import annotations

import asyncio
import json
import random
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from log_parser import process_file, save_jsonl
from quality_validator import load_records, validate_records

BASE_DIR = Path(__file__).parent
SAMPLE_DIR = BASE_DIR / "sample_logs"
OUTPUT_DIR = BASE_DIR / "outputs"
NORMALIZED_FILE = OUTPUT_DIR / "output_normalized.jsonl"
REPORT_FILE = OUTPUT_DIR / "quality_report.json"

SOURCE_FILES = {
    "firewall": SAMPLE_DIR / "sample_firewall_logs.csv",
    "auth": SAMPLE_DIR / "sample_auth_logs.txt",
    "dns": SAMPLE_DIR / "sample_dns_logs.txt",
}

app = FastAPI(title="CipherFlow API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Global In-Memory State
# --------------------------------------------------------------------------- #

RECORDS: list[dict] = []
REPORT: dict = {}
NOTIFICATIONS: list[dict] = []
SETTINGS: dict = {
    "simulation_speed": "normal",  # off, slow, normal, fast
    "active_attack": None,        # None, ddos, brute_force, dns_tunneling
    "attack_remaining": 0
}

# --------------------------------------------------------------------------- #
# Pipeline & Generation Helpers
# --------------------------------------------------------------------------- #

def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def run_pipeline() -> list[dict]:
    """Parse every configured source file and return merged output."""
    all_records: list[dict] = []
    for path in SOURCE_FILES.values():
        if path.exists():
            all_records.extend(process_file(str(path)))
    # Save a copy to the filesystem
    save_jsonl(all_records, str(NORMALIZED_FILE))
    return all_records

def generate_random_normal_event() -> dict:
    now = current_timestamp()
    evt_id = f"evt_{uuid.uuid4().hex[:10]}"
    log_type = random.choice(["firewall", "auth", "dns"])

    if log_type == "firewall":
        src = f"192.168.1.{random.randint(2, 254)}"
        dst = f"10.0.0.{random.randint(2, 254)}"
        status = random.choice(["allowed", "allowed", "allowed", "blocked", "dropped"])
        action = "TCP_CONNECT" if status == "allowed" else "TCP_REJECT"
        line = f"{now},{src},{dst},TCP,{status.upper()}"
        
        record = {
            "event_id": evt_id,
            "timestamp": now,
            "source_ip": src,
            "target_ip": dst,
            "user": None,
            "action": action,
            "status": status,
            "log_type": log_type,
            "original_line": line,
            "parsed_at": now
        }

    elif log_type == "auth":
        src = f"192.168.1.{random.randint(2, 254)}"
        user = random.choice(["m.fatima", "a.raza", "svc-deploy", "svc-backup", "guest"])
        status = random.choice(["success", "success", "success", "failed"])
        action = "LOGIN"
        line = f"{now} {user} {src} LOGIN {status.upper()}"
        
        record = {
            "event_id": evt_id,
            "timestamp": now,
            "source_ip": src,
            "target_ip": None,
            "user": user,
            "action": action,
            "status": status,
            "log_type": log_type,
            "original_line": line,
            "parsed_at": now
        }

    else:  # dns
        src = f"192.168.1.{random.randint(2, 254)}"
        domain = random.choice(["google.com", "github.com", "slack.com", "internal-wiki.local", "malicious-site.tk"])
        status = "noerror" if domain != "malicious-site.tk" else "nxdomain"
        line = f"{now} | client={src} | query={domain} | rcode={status.upper()}"
        
        record = {
            "event_id": evt_id,
            "timestamp": now,
            "source_ip": src,
            "target_ip": None,
            "user": None,
            "action": "QUERY",
            "status": status,
            "log_type": log_type,
            "original_line": line,
            "parsed_at": now,
            "domain": domain
        }

    # Introduce data quality issues occasionally (5% chance)
    if random.random() < 0.05:
        issue_type = random.choice(["missing_field", "invalid_ip", "future_timestamp"])
        if issue_type == "missing_field":
            record["source_ip"] = None
        elif issue_type == "invalid_ip":
            record["source_ip"] = "999.invalid.ip"
        elif issue_type == "future_timestamp":
            record["timestamp"] = "2099-12-31T23:59:59Z"

    return record

def generate_attack_event(attack_type: str) -> dict | None:
    now = current_timestamp()
    evt_id = f"evt_{uuid.uuid4().hex[:10]}"
    remaining = SETTINGS.get("attack_remaining", 0)

    if remaining <= 0:
        SETTINGS["active_attack"] = None
        NOTIFICATIONS.insert(0, {
            "id": f"notif_{uuid.uuid4().hex[:8]}",
            "timestamp": now,
            "severity": "info",
            "message": f"Attack simulation '{attack_type.upper()}' has concluded.",
            "source": "system"
        })
        return None

    SETTINGS["attack_remaining"] = remaining - 1

    if attack_type == "ddos":
        # DDoS Attack: firewall blocked connections targeting 10.0.0.99
        src = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        dst = "10.0.0.99"
        status = "blocked"
        line = f"{now},{src},{dst},TCP,BLOCKED"
        
        record = {
            "event_id": evt_id,
            "timestamp": now,
            "source_ip": src,
            "target_ip": dst,
            "user": None,
            "action": "TCP_CONNECT",
            "status": status,
            "log_type": "firewall",
            "original_line": line,
            "parsed_at": now
        }
        
        if remaining == 25:  # Trigger alert at the start
            NOTIFICATIONS.insert(0, {
                "id": f"notif_{uuid.uuid4().hex[:8]}",
                "timestamp": now,
                "severity": "critical",
                "message": "CRITICAL: High packet blocking frequency detected targeting host 10.0.0.99 (DDoS signature).",
                "source": "firewall"
            })
        return record

    elif attack_type == "brute_force":
        # Brute Force: failed logins ending in lockout
        user = "admin"
        src = "203.0.113.88"
        
        if remaining == 1:
            status = "locked"
            line = f"{now} {user} {src} LOGIN LOCKED"
        else:
            status = "failed"
            line = f"{now} {user} {src} LOGIN FAILED"

        record = {
            "event_id": evt_id,
            "timestamp": now,
            "source_ip": src,
            "target_ip": None,
            "user": user,
            "action": "LOGIN",
            "status": status,
            "log_type": "auth",
            "original_line": line,
            "parsed_at": now
        }

        if remaining == 8:
            NOTIFICATIONS.insert(0, {
                "id": f"notif_{uuid.uuid4().hex[:8]}",
                "timestamp": now,
                "severity": "warning",
                "message": f"WARNING: Successive failed logins detected for user '{user}' from external source {src}.",
                "source": "auth"
            })
        elif remaining == 1:
            NOTIFICATIONS.insert(0, {
                "id": f"notif_{uuid.uuid4().hex[:8]}",
                "timestamp": now,
                "severity": "critical",
                "message": f"CRITICAL: User account '{user}' has been LOCKED due to brute force attempts.",
                "source": "auth"
            })
        return record

    elif attack_type == "dns_tunneling":
        # DNS Tunneling: high frequency queries to encoded domains
        src = "192.168.1.105"
        domain = f"exfil-chk-{random.randint(100,999)}-{random.randint(1000,9999)}.leak-db.cybersec-sim.org"
        line = f"{now} | client={src} | query={domain} | rcode=NOERROR"
        
        record = {
            "event_id": evt_id,
            "timestamp": now,
            "source_ip": src,
            "target_ip": None,
            "user": None,
            "action": "QUERY",
            "status": "noerror",
            "log_type": "dns",
            "original_line": line,
            "parsed_at": now,
            "domain": domain
        }

        if remaining == 15:
            NOTIFICATIONS.insert(0, {
                "id": f"notif_{uuid.uuid4().hex[:8]}",
                "timestamp": now,
                "severity": "warning",
                "message": f"SUSPICIOUS: Repetitive sub-domain queries to leak-db.cybersec-sim.org from {src}.",
                "source": "dns"
            })
        return record

    return None

# --------------------------------------------------------------------------- #
# Background Worker Task
# --------------------------------------------------------------------------- #

async def simulation_worker():
    global RECORDS, REPORT, NOTIFICATIONS
    while True:
        speed = SETTINGS.get("simulation_speed", "normal")
        if speed == "off":
            await asyncio.sleep(1.0)
            continue

        interval = 2.0
        if speed == "slow":
            interval = 5.0
        elif speed == "fast":
            interval = 0.5

        await asyncio.sleep(interval)

        active_attack = SETTINGS.get("active_attack")
        new_record = None
        if active_attack:
            new_record = generate_attack_event(active_attack)
        else:
            new_record = generate_random_normal_event()

        if new_record:
            RECORDS.append(new_record)
            
            # Cap list size to prevent infinite memory usage
            if len(RECORDS) > 500:
                RECORDS = RECORDS[-500:]

            # Add warning/danger alerts to feed for failed statuses in normal traffic
            if not active_attack and new_record["status"] in ["blocked", "failed", "nxdomain"]:
                # 15% chance to push normal logs anomaly to the main notifications
                if random.random() < 0.2:
                    severity = "warning"
                    msg = f"Alert: Anomaly detected ({new_record['log_type'].upper()}). Action '{new_record['action']}' returned '{new_record['status']}'."
                    NOTIFICATIONS.insert(0, {
                        "id": f"notif_{uuid.uuid4().hex[:8]}",
                        "timestamp": new_record["timestamp"],
                        "severity": severity,
                        "message": msg,
                        "source": new_record["log_type"]
                    })

            # Recalculate the validator report
            REPORT = validate_records(RECORDS)

# --------------------------------------------------------------------------- #
# FastAPI Lifespan / Startup Events
# --------------------------------------------------------------------------- #

@app.on_event("startup")
async def startup_event():
    global RECORDS, REPORT, NOTIFICATIONS
    # Bootstrapping
    initial_records = run_pipeline()
    RECORDS.extend(initial_records)
    REPORT = validate_records(RECORDS)
    NOTIFICATIONS.append({
        "id": f"notif_{uuid.uuid4().hex[:8]}",
        "timestamp": current_timestamp(),
        "severity": "info",
        "message": "CipherFlow SOC Dashboard Backend started. Pipeline initialized.",
        "source": "system"
    })
    # Start simulation worker in the background
    asyncio.create_task(simulation_worker())

# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "CipherFlow API",
        "simulation_speed": SETTINGS["simulation_speed"],
        "active_attack": SETTINGS["active_attack"]
    }

@app.post("/api/run")
def run():
    """Manual run: rebuild pipeline using raw source files, resetting active state."""
    global RECORDS, REPORT, NOTIFICATIONS
    records = run_pipeline()
    RECORDS = list(records)
    REPORT = validate_records(RECORDS)
    NOTIFICATIONS.insert(0, {
        "id": f"notif_{uuid.uuid4().hex[:8]}",
        "timestamp": current_timestamp(),
        "severity": "info",
        "message": "Manual pipeline execution triggered. State reloaded.",
        "source": "system"
    })
    return {"processed": len(RECORDS), "quality_score_pct": REPORT["quality_score_pct"]}

@app.get("/api/records")
def records(
    log_type: str | None = Query(default=None, description="firewall | auth | dns"),
    limit: int = Query(default=50, le=500),
):
    data = list(RECORDS)
    if log_type:
        data = [r for r in data if r.get("log_type") == log_type]
    data.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return {"count": len(data), "records": data[:limit]}

@app.get("/api/stats")
def stats():
    data = list(RECORDS)
    by_type = Counter(r.get("log_type", "unknown") for r in data)
    by_status = Counter(r.get("status", "unknown") for r in data)

    bad_statuses = {"blocked", "dropped", "failed", "locked", "nxdomain", "servfail", "refused"}
    flagged = sum(1 for r in data if str(r.get("status", "")).lower() in bad_statuses)

    hourly = defaultdict(lambda: {"firewall": 0, "auth": 0, "dns": 0})
    for r in data:
        ts = r.get("timestamp")
        log_type = r.get("log_type")
        if not ts or log_type not in ("firewall", "auth", "dns"):
            continue
        try:
            hour = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:00")
        except ValueError:
            continue
        hourly[hour][log_type] += 1

    timeline = [{"hour": h, **counts} for h, counts in sorted(hourly.items())]

    # Calculate simulated EPS (Events Per Second)
    speed = SETTINGS.get("simulation_speed", "normal")
    eps = 0.0
    if speed == "fast":
        eps = 2.0
    elif speed == "normal":
        eps = 0.5
    elif speed == "slow":
        eps = 0.2
    
    if SETTINGS.get("active_attack"):
        eps *= 6.0

    return {
        "total_events": len(data),
        "flagged_events": flagged,
        "by_type": dict(by_type),
        "by_status": dict(by_status),
        "timeline": timeline,
        "eps": round(eps, 1)
    }

@app.get("/api/quality-report")
def quality_report():
    return REPORT

@app.get("/api/notifications")
def get_notifications():
    # Cap notifications list in endpoint response
    return NOTIFICATIONS[:40]

class SettingsUpdate(BaseModel):
    simulation_speed: str | None = None
    trigger_attack: str | None = None

@app.post("/api/settings")
def update_settings(update: SettingsUpdate):
    global SETTINGS, NOTIFICATIONS
    if update.simulation_speed is not None:
        if update.simulation_speed in ["off", "slow", "normal", "fast"]:
            SETTINGS["simulation_speed"] = update.simulation_speed
            NOTIFICATIONS.insert(0, {
                "id": f"notif_{uuid.uuid4().hex[:8]}",
                "timestamp": current_timestamp(),
                "severity": "info",
                "message": f"Simulation speed configured: {update.simulation_speed.upper()}",
                "source": "system"
            })

    if update.trigger_attack is not None:
        if update.trigger_attack in ["ddos", "brute_force", "dns_tunneling"]:
            SETTINGS["active_attack"] = update.trigger_attack
            if update.trigger_attack == "ddos":
                SETTINGS["attack_remaining"] = 25
            elif update.trigger_attack == "brute_force":
                SETTINGS["attack_remaining"] = 8
            elif update.trigger_attack == "dns_tunneling":
                SETTINGS["attack_remaining"] = 15

    return SETTINGS

@app.post("/api/reset")
def reset_simulation():
    global RECORDS, REPORT, NOTIFICATIONS, SETTINGS
    records = run_pipeline()
    RECORDS = list(records)
    REPORT = validate_records(RECORDS)
    SETTINGS = {
        "simulation_speed": "normal",
        "active_attack": None,
        "attack_remaining": 0
    }
    NOTIFICATIONS = [
        {
            "id": f"notif_{uuid.uuid4().hex[:8]}",
            "timestamp": current_timestamp(),
            "severity": "info",
            "message": "Simulation logs and config reset to base values.",
            "source": "system"
        }
    ]
    return {"status": "success", "settings": SETTINGS}

@app.get("/api/event/{event_id}")
def event(event_id: str):
    data = list(RECORDS)
    for r in data:
        if r.get("event_id") == event_id:
            return r
    raise HTTPException(status_code=404, detail="Event not found")
