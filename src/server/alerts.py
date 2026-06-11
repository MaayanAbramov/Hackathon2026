"""
alerts.py
---------
Drop this file next to server.py.

Usage in server.py:
    from alerts import start_alert_loop

    start_alert_loop(
        telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
        patients_col=db._col(),
        chat_ids_fn=db.get_all_chat_ids,
    )
"""

import time
import threading
import requests
from datetime import datetime, timezone

SEVERITY_BUDGETS = {
    "critical": 10,
    "severe":   30,
    "moderate": 60,
    "mild":     120,
    "low":      150,
}

def _get_overdue(col, threshold=0.75):
    now = datetime.now(timezone.utc)
    alerts = []
    for patient in col.find({}, {"_id": 0}):
        for dest in patient.get("diagnosis", []):
            if dest.get("status") != "pending":
                continue
            budget = SEVERITY_BUDGETS.get(dest.get("severity"))
            added_at = dest.get("added_at")
            if not budget or not added_at:
                continue
            elapsed = (now - added_at).total_seconds() / 60
            pct = elapsed / budget
            if pct >= threshold:
                alerts.append({
                    "patient_id": patient["patient_id"],
                    "name": patient.get("name"),
                    "destination": dest["destination"],
                    "severity": dest["severity"],
                    "elapsed_min": round(elapsed, 1),
                    "budget_min": budget,
                    "pct": round(pct * 100, 1),
                })
    return alerts

def _broadcast(token, chat_ids_fn, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for chat_id in chat_ids_fn():
        try:
            requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        except Exception as e:
            print(f"[alerts] failed to send to {chat_id}: {e}")

def _loop(token, patients_col, chat_ids_fn, threshold, interval_sec):
    while True:
        try:
            for a in _get_overdue(patients_col, threshold):
                msg = (
                    f"⚠️ ALERT: {a['name']} ({a['patient_id']})\n"
                    f"Destination: {a['destination']}\n"
                    f"Severity: {a['severity'].upper()}\n"
                    f"Elapsed: {a['elapsed_min']} / {a['budget_min']} min ({a['pct']}%)"
                )
                _broadcast(token, chat_ids_fn, msg)
        except Exception as e:
            print(f"[alerts] error: {e}")
        time.sleep(interval_sec)

def start_alert_loop(telegram_token, patients_col, chat_ids_fn, threshold=0.75, interval_sec=60):
    t = threading.Thread(
        target=_loop,
        args=(telegram_token, patients_col, chat_ids_fn, threshold, interval_sec),
        daemon=True,
    )
    t.start()