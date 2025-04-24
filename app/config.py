# config.py  ──────────────────────────────────────────────────────────────
# Central, thread‑safe runtime state for the traffic generator.

import threading
import time


class TrafficConfig:
    """Hold current packet rate, burst status and global stop flag."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.rate_ms: int = 20            # default pace
        self.burst_mode: bool = False
        self.burst_end_time: float = 0.0
        self.pre_burst_rate: int | None = None
        self.stopped: bool = False

    # ── public mutators ──────────────────────────────────────────────────

    def set_rate(self, ms: int) -> None:
        """Permanent rate change, cancels any ongoing burst."""
        with self.lock:
            if self.burst_mode:
                self._clear_burst_locked()
                print("⚠️  Manual override — burst cancelled.")

            self.rate_ms = ms
            self.stopped = False
            print(f"✅ Traffic rate set to {ms} ms and resumed.")

    def start_burst(self, rate: int, duration_s: int) -> None:
        """Run a temporary burst at *rate* for *duration_s* seconds."""
        with self.lock:
            if not self.burst_mode:
                self.pre_burst_rate = self.rate_ms          # remember baseline
            self.rate_ms = rate
            self.burst_mode = True
            self.burst_end_time = time.time() + duration_s
            self.stopped = False
            print(f"🚀 Burst: {rate} ms for {duration_s}s")

    def stop(self) -> None:
        """Pause all sending threads until further notice."""
        with self.lock:
            self.stopped = True
            self._clear_burst_locked()
            self.rate_ms = 20                              # idle default
            print("⏸️  Traffic stopped by user.")

    # ── internal helpers ────────────────────────────────────────────────

    def _clear_burst_locked(self) -> None:
        """Reset burst fields.  Caller must already hold the lock."""
        self.burst_mode = False
        self.burst_end_time = 0.0
        self.pre_burst_rate = None

    # ── accessor used by sender threads & UI ────────────────────────────

    def get(self) -> dict:
        """
        Return a snapshot of current state.
        Fast path: if .stopped is True we avoid extra time calculations.
        """
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

            # handle burst expiry first
            if self.burst_mode and now > self.burst_end_time:
                print(f"🛑 Burst ended – reverting to {self.pre_burst_rate or 20} ms")
                self.rate_ms = self.pre_burst_rate or 20
                self._clear_burst_locked()

            burst_remaining = (
                max(0, int(self.burst_end_time - now)) if self.burst_mode else 0
            )

            snapshot = {
                "rate_ms": self.rate_ms,
                "burst_mode": self.burst_mode,
                "burst_until": int(self.burst_end_time),
                "burst_remaining": burst_remaining,
                "stopped": False,
            }

        # Uncomment for verbose live trace (commented by default to reduce spam)
        # print(
        #     f"⚙️  cfg rate={snapshot['rate_ms']} ms  "
        #     f"burst={snapshot['burst_mode']}  "
        #     f"remain={snapshot['burst_remaining']}s"
        # )

        return snapshot


# Single shared instance imported everywhere
config = TrafficConfig()
