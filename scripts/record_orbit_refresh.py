#!/usr/bin/env python3
"""Record the actual CelesTrak ACTIVE snapshot retrieval, or a failed attempt."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/orbit-distribution/latest.json"
LOG = ROOT / "data/source-log.jsonl"
URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=JSON"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    outcome = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    existing.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if outcome == "success":
        if not SNAPSHOT.is_file() or SNAPSHOT.stat().st_size == 0:
            print("ACTIVE snapshot missing after successful refresh step", file=sys.stderr)
            return 1
        try:
            snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            retrieved_at = snapshot["retrieved_at_utc"]
            count = snapshot["raw_record_count"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"ACTIVE snapshot could not be read: {exc}", file=sys.stderr)
            return 1
        if any(
            row.get("dataset") == "celestrak_active"
            and row.get("retrieved_at") == retrieved_at
            and row.get("status") == "success"
            for row in existing
        ):
            print("ACTIVE retrieval already present in source log; no duplicate entry added.")
            return 0
        entry = {
            "retrieved_at": retrieved_at,
            "source": "CelesTrak GP/OMM ACTIVE group",
            "dataset": "celestrak_active",
            "record_count": count,
            "status": "success",
            "url": URL,
            "note": "Derived orbit-distribution input; raw records are processed in memory and are not published.",
        }
    elif outcome == "failure":
        entry = {
            "retrieved_at": now_utc(),
            "source": "CelesTrak GP/OMM ACTIVE group",
            "dataset": "celestrak_active",
            "record_count": 0,
            "status": "error",
            "url": URL,
            "note": "ACTIVE refresh failed; last-known-good orbit-distribution snapshot was not replaced.",
        }
    else:
        print(f"ACTIVE refresh outcome was {outcome}; no retrieval record added.")
        return 0

    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Recorded ACTIVE {entry['status']} at {entry['retrieved_at']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
