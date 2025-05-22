# sender.py – persistent-socket traffic generator (quiet edition)
import os, socket, time, random, threading, logging
from collections import defaultdict
from config import config

# ── logging -------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [sender] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("sender")

# simple per-key rate-limiter (one message / 30 s)
_last = defaultdict(float)
def rate_warn(key: str, msg: str):
    now = time.time()
    if now - _last[key] > 30:
        log.warning(msg)
        _last[key] = now

# ── environment ----------------------------------------------------------------
RECEIVER_DNS  = os.getenv("RECEIVER_SERVICE", "traffic-receiver.dev.svc.cluster.local")
RECEIVER_PORT = int(os.getenv("RECEIVER_PORT", "9999"))
POD_NAME      = os.getenv("POD_NAME") or socket.gethostname()
MSG_PER_TICK  = int(os.getenv("MESSAGES_PER_CONNECTION", "20"))

# ── helpers --------------------------------------------------------------------
def resolve_ips() -> list[str]:
    try:
        return socket.gethostbyname_ex(RECEIVER_DNS)[2]
    except Exception as exc:
        rate_warn("dns", f"DNS failure for {RECEIVER_DNS}: {exc}")
        return []

# ── worker ---------------------------------------------------------------------
def worker(ip: str) -> None:
    while True:
        if config.get()["stopped"]:
            time.sleep(0.5)
            continue

        try:
            with socket.create_connection((ip, RECEIVER_PORT), timeout=2) as sock:
                while not config.get()["stopped"]:
                    rate = config.get()["rate_ms"] / 1000.0
                    for _ in range(MSG_PER_TICK):
                        sock.sendall(f"[{POD_NAME}] {int(time.time())}\n".encode())
                    time.sleep(rate)
        except Exception as exc:
            rate_warn(ip, f"TCP error to {ip}: {exc}")
            time.sleep(0.5)

# ── main loop ------------------------------------------------------------------
def traffic_loop() -> None:
    log.info("traffic-loop online on %s", POD_NAME)
    started: set[str] = set()

    while True:
        for ip in resolve_ips():
            if ip not in started:
                threading.Thread(target=worker, args=(ip,), daemon=True).start()
                started.add(ip)

        # prune workers for pods that disappeared
        gone = started - set(resolve_ips())
        if gone:
            log.info("receivers left cluster: %s", ", ".join(gone))
            started -= gone

        time.sleep(5)
