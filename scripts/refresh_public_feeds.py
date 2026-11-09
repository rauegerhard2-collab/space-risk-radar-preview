#!/usr/bin/env python3
"""Fetch and validate public orbital catalogue feeds for the staging branch.

The script never writes partial/empty responses over the last good snapshot.
It records retrieval timestamps separately from provider event/epoch timestamps.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "SpaceRiskRadar-public-research/1.0 (daily catalogue refresh)"
FEEDS = [
    {
        "key": "celestrak_stations",
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=STATIONS&FORMAT=JSON",
        "path": ROOT / "data/orbital/latest.json",
        "kind": "celestrak",
        "minimum": 5,
    },
    {
        "key": "orbitalwiki_events",
        "url": "https://www.orbitalwiki.com/api/v1/events",
        "path": ROOT / "data/orbital/orbitalwiki-events/latest.json",
        "kind": "orbitalwiki_events",
        "minimum": 1,
    },
    {
        "key": "orbitalwiki_launches",
        "url": "https://www.orbitalwiki.com/api/v1/launches",
        "path": ROOT / "data/orbital/orbitalwiki-launches/latest.json",
        "kind": "orbitalwiki_launches",
        "minimum": 1,
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_json(url: str):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"Fetch failed for {url}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Response from {url} was not valid UTF-8 JSON") from exc


def validate_and_wrap(feed: dict, payload, retrieved_at: str) -> tuple[dict, int]:
    kind = feed["kind"]
    if kind == "celestrak":
        if not isinstance(payload, list):
            raise RuntimeError("CelesTrak response is not a JSON array")
        rows = [row for row in payload if isinstance(row, dict)]
        if len(rows) < feed["minimum"]:
            raise RuntimeError(f"CelesTrak returned only {len(rows)} usable records")
        return {
            "dataset_id": "celestrak-stations-" + retrieved_at[:10],
            "retrieved_at": retrieved_at,
            "reference": "OMM epoch is per object; see each EPOCH field",
            "source": {
                "name": "CelesTrak General Perturbations (GP) API",
                "url": feed["url"],
                "format": "CCSDS OMM JSON",
                "group": "STATIONS",
                "attribution": "Orbital elements provided by CelesTrak; source must be credited.",
            },
            "record_count": len(rows),
            "objects": rows,
            "limitations": [
                "STATIONS is a selected group, not a global satellite or debris catalogue.",
                "Orbital elements are not conjunction warnings or confirmed manoeuvre records.",
                "Each object's EPOCH is distinct from this retrieval timestamp.",
            ],
        }, len(rows)

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise RuntimeError(f"{kind} response has an unexpected JSON envelope")
    rows = payload["data"]
    if len(rows) < feed["minimum"]:
        raise RuntimeError(f"{kind} returned only {len(rows)} records")
    if not all(isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{kind} contains non-object records")
    is_events = kind == "orbitalwiki_events"
    return {
        "dataset_id": kind.replace("_", "-") + "-" + retrieved_at[:10],
        "retrieved_at": retrieved_at,
        "source": {
            "name": "OrbitalWiki public read-only API",
            "url": feed["url"],
            "attribution": "OrbitalWiki; catalogue data under ODbL-1.0. Upstream sources retain their own terms.",
        },
        "record_type": (
            "catalogue change events; not conjunction warnings or manoeuvre records"
            if is_events else "launch catalogue metadata; not orbital ephemerides"
        ),
        "payload": payload,
        "limitations": [
            "OrbitalWiki is a complementary catalogue source, not an independent space-surveillance sensor.",
            "API catalogue history is limited; a prolonged polling gap may not be recoverable.",
            "Provider event timestamps and generated_at are not the same as this retrieval timestamp.",
        ],
    }, len(rows)


def main() -> int:
    source_log = ROOT / "data/source-log.jsonl"
    source_log.parent.mkdir(parents=True, exist_ok=True)
    log_entries = []
    failures = []
    for feed in FEEDS:
        retrieved_at = utc_now()
        try:
            payload = fetch_json(feed["url"])
            wrapped, count = validate_and_wrap(feed, payload, retrieved_at)
            feed["path"].parent.mkdir(parents=True, exist_ok=True)
            temp_path = feed["path"].with_suffix(feed["path"].suffix + ".tmp")
            temp_path.write_text(json.dumps(wrapped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            # Atomic replacement: last-known-good file survives a failed write.
            temp_path.replace(feed["path"])
            log_entries.append({
                "retrieved_at": retrieved_at,
                "source": wrapped["source"]["name"],
                "dataset": feed["key"],
                "record_count": count,
                "status": "success",
                "url": feed["url"],
            })
            print(f"OK {feed['key']}: {count} records")
        except (RuntimeError, OSError) as exc:
            failures.append(f"{feed['key']}: {exc}")
            log_entries.append({
                "retrieved_at": retrieved_at,
                "source": feed["key"],
                "dataset": feed["key"],
                "record_count": 0,
                "status": "error",
                "url": feed["url"],
                "note": str(exc),
            })
            print(f"ERROR {feed['key']}: {exc}", file=sys.stderr)

    if log_entries:
        with source_log.open("a", encoding="utf-8") as handle:
            for entry in log_entries:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if failures:
        print("One or more feeds failed; successful feeds remain staged, failed snapshots were preserved.", file=sys.stderr)
        # Fail the job visibly; partial successful files and source-log entries remain auditable.
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
