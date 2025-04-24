# sender.py – persistent‑socket traffic generator
import os
import socket
import time
import random
import threading

from config import config

# ── environment ----------------------------------------------------------------
RECEIVER_DNS   = os.getenv("RECEIVER_SERVICE",
                           "traffic-receiver.dev.svc.cluster.local")
RECEIVER_PORT  = int(os.getenv("RECEIVER_PORT", "9999"))
POD_NAME       = os.getenv("POD_NAME") or socket.gethostname()
MSG_PER_TICK   = int(os.getenv("MESSAGES_PER_CONNECTION", "20"))

# ── helpers --------------------------------------------------------------------
def resolve_ips() -> list[str]:
    """Return the list of pod IPs behind the (headless) service."""
    try:
        return socket.gethostbyname_ex(RECEIVER_DNS)[2]
    except Exception as exc:
        print(f"[❌ DNS] {exc}")
        return []

# ── worker ---------------------------------------------------------------------
def worker(ip: str) -> None:
    """
    Dedicated thread for one receiver‑pod.
    Keeps a socket open; adapts instantly to rate / stop changes.
    """
    while True:
        # Pause if traffic is globally stopped
        if config.get()["stopped"]:
            time.sleep(0.5)
            continue

        try:
            with socket.create_connection((ip, RECEIVER_PORT), timeout=2) as sock:
                while not config.get()["stopped"]:
                    rate_sec = config.get()["rate_ms"] / 1000.0
                    for _ in range(MSG_PER_TICK):
                        sock.sendall(f"[{POD_NAME}] {int(time.time())}\n".encode())
                    time.sleep(rate_sec)      # picks up new rate next loop
        except Exception as exc:
            print(f"[❌ TCP {ip}] {exc}")
            time.sleep(0.5)                  # brief back‑off before reconnect

# ── main loop ------------------------------------------------------------------
def traffic_loop() -> None:
    """Spawns/maintains one worker thread per receiver pod."""
    print(f"☘️  traffic‑loop online from {POD_NAME}")
    started: set[str] = set()

    while True:
        # resolve every few seconds to pick up new / replaced pods
        for ip in resolve_ips():
            if ip not in started:
                threading.Thread(target=worker, args=(ip,), daemon=True).start()
                started.add(ip)

        # prune workers for pods that disappeared (rare)
        gone = started - set(resolve_ips())
        if gone:
            print(f"[ℹ️] receivers left cluster: {', '.join(gone)}")
            started -= gone

        time.sleep(5)   # DNS refresh interval
