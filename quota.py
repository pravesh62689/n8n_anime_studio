"""
quota.py — tracks YOUR real daily ZeroGPU usage, locally.

The thing that actually limits Tier-1 generation isn't any specific
Hugging Face Space — it's your account's daily GPU-seconds allowance
(~3.5 min/day free with a token, ~2 min/day anonymous, resetting ~24h
after first use). That quota is identical no matter which Space or fork
you call. This module tracks estimated spend against that ceiling so the
Visual Router can decide "do we have room for a hero clip today?" instead
of finding out mid-render via a 429.

This is deliberately a plain local JSON file, not a database table —
it's single-machine, single-process state, and doesn't need to be more
than that.
"""
import json
import os
import datetime
from pathlib import Path
from typing import Optional


def _today() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


class QuotaTracker:
    def __init__(self, state_file: Optional[str] = None,
                 daily_quota_seconds: Optional[int] = None,
                 estimated_cost_per_clip: Optional[int] = None):
        self.state_file = Path(state_file or os.environ.get("HF_QUOTA_STATE_FILE", "hf_quota_state.json"))
        self.daily_quota_seconds = daily_quota_seconds or int(
            os.environ.get("HF_DAILY_QUOTA_SECONDS", 190))
        self.estimated_cost_per_clip = estimated_cost_per_clip or int(
            os.environ.get("HF_ESTIMATED_COST_PER_CLIP_SECONDS", 70))
        self._state = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                if data.get("date") == _today():
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"date": _today(), "seconds_used": 0, "calls_today": 0}

    def _save(self) -> None:
        self.state_file.write_text(json.dumps(self._state))

    def remaining_seconds(self) -> int:
        if self._state.get("date") != _today():
            self._state = {"date": _today(), "seconds_used": 0, "calls_today": 0}
        return max(0, self.daily_quota_seconds - self._state["seconds_used"])

    def can_afford(self, estimated_cost: Optional[int] = None) -> bool:
        cost = estimated_cost if estimated_cost is not None else self.estimated_cost_per_clip
        return self.remaining_seconds() >= cost

    def record_usage(self, actual_or_estimated_seconds: Optional[int] = None) -> None:
        cost = actual_or_estimated_seconds if actual_or_estimated_seconds is not None else self.estimated_cost_per_clip
        if self._state.get("date") != _today():
            self._state = {"date": _today(), "seconds_used": 0, "calls_today": 0}
        self._state["seconds_used"] += cost
        self._state["calls_today"] += 1
        self._save()

    def status(self) -> dict:
        return {
            "date": self._state.get("date"),
            "seconds_used": self._state.get("seconds_used", 0),
            "seconds_remaining": self.remaining_seconds(),
            "calls_today": self._state.get("calls_today", 0),
        }


if __name__ == "__main__":
    q = QuotaTracker()
    print("Current quota status:", q.status())
    print("Can afford one more clip?", q.can_afford())
