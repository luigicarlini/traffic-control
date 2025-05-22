# config.py  ──────────────────────────────────────────────────────────────
# Thread-safe runtime state for the traffic-generator, now with quiet logging.

import threading
import time
import logging
import os

# ── logging --------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()          # DEBUG/INFO/…
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [cfg] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("cfg")


class TrafficConfig:
    """Holds current packet rate, burst status and global stop flag."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.rate_ms: int = 20
        self.burst_mode: bool = False
        self.burst_end_time: float = 0.0
        self.pre_burst_rate: int | None = None
        self.stopped: bool = False

    # ── public mutators ──────────────────────────────────────────────────

    def set_rate(self, ms: int) -> None:
        """Permanent rate change; cancels any running burst."""
        with self.lock:
            if self.burst_mode:
                self._clear_burst_locked()
                log.warning("Manual rate override cancelled burst.")
            self.rate_ms = ms
            self.stopped = False
            log.info("Traffic rate set to %s ms", ms)

    def start_burst(self, rate: int, duration_s: int) -> None:
        """Start (or extend) a burst at *rate* for *duration_s* seconds."""
        with self.lock:
            if not self.burst_mode:
                self.pre_burst_rate = self.rate_ms
            self.rate_ms = rate
            self.burst_mode = True
            self.burst_end_time = time.time() + duration_s
            self.stopped = False
            log.info("Burst %s ms for %s s started", rate, duration_s)

    def stop(self) -> None:
        """Pause all sending threads until further notice."""
        with self.lock:
            self.stopped = True
            self._clear_burst_locked()
            self.rate_ms = 20
            log.info("Traffic stopped by user")

    # ── internal helpers ────────────────────────────────────────────────

    def _clear_burst_locked(self) -> None:
        """Reset burst fields (caller already holds lock)."""
        self.burst_mode = False
        self.burst_end_time = 0.0
        self.pre_burst_rate = None

    # ── accessor used by sender threads & UI ────────────────────────────

    def get(self) -> dict:
        """Return a snapshot of current state (cheap fast-path when stopped)."""
        with self.lock:
            if self.stopped:
                return {
                    "rate_ms": self.rate_ms,
                    "burst_mode": False,
                    "burst_until": 0,
                    "burst_remaining": 0,
                    "stopped": True,
                }

            now = time.time()

            # Burst expiry
            if self.burst_mode and now > self.burst_end_time:
                self.rate_ms = self.pre_burst_rate or 20
                self._clear_burst_locked()
                log.info("Burst ended – rate reverted to %s ms", self.rate_ms)

            burst_remaining = (
                max(0, int(self.burst_end_time - now)) if self.burst_mode else 0
            )

            return {
                "rate_ms": self.rate_ms,
                "burst_mode": self.burst_mode,
                "burst_until": int(self.burst_end_time),
                "burst_remaining": burst_remaining,
                "stopped": False,
            }


# Single shared instance
config = TrafficConfig()
