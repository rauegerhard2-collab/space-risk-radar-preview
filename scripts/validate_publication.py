#!/usr/bin/env python3
"""Validate the staged public data set before weekly publication."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

FEEDS = {
    "celestrak_active": {
        "path": "data/orbit-distribution/latest.json",
        "time_key": "retrieved_at_utc",
        "count_key": "raw_record_count",
        "minimum": 1000,
        "kind": "active",
    },
    "celestrak_stations": {
        "path": "data/orbital/latest.json",
        "time_key": "retrieved_at",
        "count_key": "record_count",
        "minimum": 5,
        "kind": "stations",
    },
    "orbitalwiki_events": {
        "path": "data/orbital/orbitalwiki-events/latest.json",
        "time_key": "retrieved_at",
        "count_key": "payload.data",
        "minimum": 1,
        "kind": "events",
    },
    "orbitalwiki_launches": {
        "path": "data/orbital/orbitalwiki-launches/latest.json",
        "time_key": "retrieved_at",
        "count_key": "payload.data",
        "minimum": 1,
        "kind": "launches",
    },
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label}: timestamp missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"{label}: invalid timestamp {value!r}: {exc}")
    if parsed.tzinfo is None:
        fail(f"{label}: timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def load_json(path: Path):
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"Missing or empty file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def get_count(snapshot: dict, kind: str) -> int:
    if kind == "active":
        count = snapshot.get("raw_record_count")
    elif kind == "stations":
        objects = snapshot.get("objects")
        if not isinstance(objects, list) or not all(isinstance(x, dict) for x in objects):
            fail("CelesTrak STATIONS objects must be a non-empty array of objects")
        count = len(objects)
        if snapshot.get("record_count") != count:
            fail("CelesTrak STATIONS record_count does not match objects length")
    else:
        payload = snapshot.get("payload")
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not all(isinstance(x, dict) for x in rows):
            fail(f"{kind}: payload.data must be an array of objects")
        count = len(rows)
        if payload.get("count") is not None and payload.get("count") != count:
            fail(f"{kind}: payload.count does not match payload.data length")
    if not isinstance(count, int) or count < 0:
        fail(f"{kind}: invalid record count")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-age-hours", type=float, default=48)
    args = parser.parse_args()
    root = Path(args.root)
    now = datetime.now(timezone.utc)
    if args.max_age_hours <= 0:
        fail("--max-age-hours must be positive")

    log_path = root / "data/source-log.jsonl"
    if not log_path.is_file() or log_path.stat().st_size == 0:
        fail("data/source-log.jsonl is missing or empty")
    entries = []
    for number, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"source-log.jsonl line {number} is invalid JSON: {exc}")
        if not isinstance(entry, dict):
            fail(f"source-log.jsonl line {number} is not a JSON object")
        entries.append(entry)

    latest = {}
    for entry in entries:
        dataset = entry.get("dataset")
        if dataset in FEEDS:
            latest[dataset] = entry

    max_age = timedelta(hours=args.max_age_hours)
    for dataset, spec in FEEDS.items():
        entry = latest.get(dataset)
        if entry is None:
            fail(f"{dataset}: no source-log entry")
        if entry.get("status") != "success":
            fail(f"{dataset}: latest logged attempt is {entry.get('status')!r}; publication blocked")

        log_time = parse_time(entry.get("retrieved_at"), f"{dataset} source log")
        age = now - log_time
        if age < timedelta(minutes=-10):
            fail(f"{dataset}: source-log timestamp is more than 10 minutes in the future")
        if age > max_age:
            fail(f"{dataset}: latest successful retrieval is older than {args.max_age_hours:g} hours")

        snapshot_path = root / spec["path"]
        snapshot = load_json(snapshot_path)
        if not isinstance(snapshot, dict):
            fail(f"{dataset}: snapshot root must be a JSON object")
        snapshot_time = parse_time(snapshot.get(spec["time_key"]), f"{dataset} snapshot")
        if abs((snapshot_time - log_time).total_seconds()) > 1:
            fail(f"{dataset}: source-log and snapshot retrieval timestamps do not match")

        count = get_count(snapshot, spec["kind"])
        if count < spec["minimum"]:
            fail(f"{dataset}: only {count} records; minimum is {spec['minimum']}")
        logged_count = entry.get("record_count")
        if logged_count != count:
            fail(f"{dataset}: source-log record_count {logged_count!r} does not match snapshot count {count}")

        if spec["kind"] == "active":
            counts = snapshot.get("counts")
            quality = snapshot.get("quality")
            if not isinstance(counts, dict) or not isinstance(quality, dict):
                fail("celestrak_active: counts or quality metadata missing")
            if any(not isinstance(v, int) or v < 0 for v in counts.values()):
                fail("celestrak_active: invalid orbit-class count")
            if sum(counts.values()) != snapshot.get("record_count"):
                fail("celestrak_active: orbit-class counts do not sum to record_count")
            if not isinstance(snapshot.get("record_count"), int) or snapshot["record_count"] <= 0:
                fail("celestrak_active: no quality-approved records")
            if snapshot["record_count"] > snapshot.get("raw_record_count", 0):
                fail("celestrak_active: quality-approved count exceeds raw count")
            epoch_min = parse_time(snapshot.get("source_epoch_min_utc"), "ACTIVE minimum source epoch")
            epoch_max = parse_time(snapshot.get("source_epoch_max_utc"), "ACTIVE maximum source epoch")
            if epoch_min > epoch_max:
                fail("celestrak_active: source epoch range is inverted")
            if epoch_max > snapshot_time + timedelta(hours=6):
                fail("celestrak_active: quality-approved source epoch is too far in the future")

        print(f"OK {dataset}: {count} records; retrieved {snapshot_time.isoformat()}")

    print("Publication validation passed for all four maintained feeds.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"PUBLICATION BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(1)
