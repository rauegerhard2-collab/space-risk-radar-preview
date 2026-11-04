#!/usr/bin/env python3
"""Build a compact orbit-regime summary from CelesTrak's public ACTIVE GP group.

Raw catalogue records are processed in memory and are not republished by this script.
This is a distribution of records in CelesTrak's ACTIVE group, not a census of all
catalogued objects and not a collision-risk product.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=JSON"
OUT = Path("data/orbit-distribution/latest.json")
MU_EARTH_KM3_S2 = 398600.4418
EARTH_RADIUS_KM = 6378.137
DAY_SECONDS = 86400
MIN_REFRESH_HOURS = 20
FUTURE_EPOCH_TOLERANCE_HOURS = 6
STALE_EPOCH_DAYS = 30


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def altitude_bounds(record: dict) -> tuple[float, float] | None:
    try:
        mean_motion = float(record["MEAN_MOTION"])
        eccentricity = float(record["ECCENTRICITY"])
        if not (mean_motion > 0 and 0 <= eccentricity < 1):
            return None
        angular_rate = mean_motion * 2 * math.pi / DAY_SECONDS
        semi_major_axis = (MU_EARTH_KM3_S2 / angular_rate**2) ** (1 / 3)
        perigee = semi_major_axis * (1 - eccentricity) - EARTH_RADIUS_KM
        apogee = semi_major_axis * (1 + eccentricity) - EARTH_RADIUS_KM
        return perigee, apogee
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def classify(record: dict) -> str:
    bounds = altitude_bounds(record)
    if bounds is None:
        return "unclassified"
    perigee, apogee = bounds
    try:
        motion = float(record["MEAN_MOTION"])
        eccentricity = float(record["ECCENTRICITY"])
    except (KeyError, TypeError, ValueError):
        return "unclassified"

    # Approximate regime labels are intentionally broad and documented.
    if 0.9 <= motion <= 1.1 and eccentricity <= 0.1:
        return "geo_like"
    if apogee < 2000:
        return "leo"
    if eccentricity >= 0.25 or (perigee < 2000 <= apogee):
        return "heo_or_crossing"
    if perigee >= 2000 and apogee < 35786:
        return "meo"
    if perigee >= 35786:
        return "above_geo"
    return "unclassified"


def self_test() -> None:
    cases = [
        ({"MEAN_MOTION": 15.5, "ECCENTRICITY": 0.001}, "leo"),
        ({"MEAN_MOTION": 2.0, "ECCENTRICITY": 0.01}, "meo"),
        ({"MEAN_MOTION": 1.0027, "ECCENTRICITY": 0.001}, "geo_like"),
        ({"MEAN_MOTION": 2.0, "ECCENTRICITY": 0.7}, "heo_or_crossing"),
        ({}, "unclassified"),
    ]
    for record, expected in cases:
        actual = classify(record)
        if actual != expected:
            raise AssertionError(f"{record}: expected {expected}, got {actual}")

    now = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
    quality_test = build_summary([
        {"MEAN_MOTION": 15.5, "ECCENTRICITY": 0.001, "EPOCH": "2026-11-04T11:00:00Z"},
        {"MEAN_MOTION": 15.5, "ECCENTRICITY": 0.001, "EPOCH": "2026-11-05T12:00:00Z"},
        {"MEAN_MOTION": 15.5, "ECCENTRICITY": 0.001, "EPOCH": None},
    ], now)
    assert quality_test["record_count"] == 1
    assert quality_test["quality"]["excluded_future_epoch_count"] == 1
    assert quality_test["quality"]["missing_or_invalid_epoch_count"] == 1
    assert sum(quality_test["counts"].values()) == quality_test["record_count"]
    print(f"Self-test passed: {len(cases)} classification cases plus epoch-quality gates")


def retrieve_records() -> list[dict]:
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "SpaceRiskRadar-orbit-distribution/0.1 (public research dashboard)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"CelesTrak returned HTTP {exc.code}; stop and review provider guidance. "
            "Do not retry in a loop."
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"CelesTrak request failed: {exc}") from exc

    try:
        records = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("CelesTrak response was not valid UTF-8 JSON") from exc
    if not isinstance(records, list) or not records:
        raise RuntimeError("CelesTrak response was empty or had an unexpected schema")
    return [r for r in records if isinstance(r, dict)]


def build_summary(records: list[dict], retrieved_at: datetime) -> dict:
    # A source epoch is the time the orbital elements describe, not the retrieval time.
    # A record materially dated in the future cannot be safely used in this snapshot.
    cutoff = retrieved_at.timestamp() + FUTURE_EPOCH_TOLERANCE_HOURS * 3600
    valid_records = []
    parsed_epochs: list[datetime] = []
    raw_epochs: list[datetime] = []
    future_epoch_count = 0
    missing_epoch_count = 0
    stale_epoch_count = 0

    for record in records:
        epoch = parse_time(record.get("EPOCH"))
        if epoch is None:
            missing_epoch_count += 1
            continue
        epoch = epoch.astimezone(timezone.utc)
        raw_epochs.append(epoch)
        if epoch.timestamp() > cutoff:
            future_epoch_count += 1
            continue
        valid_records.append(record)
        parsed_epochs.append(epoch)
        if (retrieved_at - epoch).total_seconds() > STALE_EPOCH_DAYS * DAY_SECONDS:
            stale_epoch_count += 1

    if not valid_records:
        raise RuntimeError(
            "No records passed the epoch-quality gate; refusing to publish an empty or future-dated snapshot."
        )

    counts = {
        "leo": 0,
        "meo": 0,
        "geo_like": 0,
        "heo_or_crossing": 0,
        "above_geo": 0,
        "unclassified": 0,
    }
    for record in valid_records:
        counts[classify(record)] += 1

    return {
        "schema_version": 1,
        "source": "CelesTrak GP/OMM ACTIVE group",
        "source_url": URL,
        "retrieved_at_utc": retrieved_at.isoformat().replace("+00:00", "Z"),
        "source_epoch_min_utc": min(parsed_epochs).isoformat().replace("+00:00", "Z"),
        "source_epoch_max_utc": max(parsed_epochs).isoformat().replace("+00:00", "Z"),
        "raw_source_epoch_max_utc": max(raw_epochs).isoformat().replace("+00:00", "Z") if raw_epochs else None,
        "scope": "Records returned by the CelesTrak ACTIVE group that pass the source-epoch quality gate; not a complete global catalogue.",
        "raw_record_count": len(records),
        "record_count": len(valid_records),
        "classified_count": len(valid_records) - counts["unclassified"],
        "quality": {
            "future_epoch_tolerance_hours": FUTURE_EPOCH_TOLERANCE_HOURS,
            "stale_epoch_threshold_days": STALE_EPOCH_DAYS,
            "excluded_future_epoch_count": future_epoch_count,
            "missing_or_invalid_epoch_count": missing_epoch_count,
            "stale_epoch_count": stale_epoch_count,
            "epoch_gate": "Records with no parseable EPOCH or an EPOCH more than 6 hours after retrieval are excluded from the distribution.",
        },
        "classification_method": {
            "leo": "apogee altitude < 2,000 km",
            "meo": "perigee altitude >= 2,000 km and apogee altitude < 35,786 km, excluding GEO-like and high-eccentricity cases",
            "geo_like": "mean motion 0.9–1.1 revolutions/day and eccentricity <= 0.1; approximate, not a precise GEO determination",
            "heo_or_crossing": "eccentricity >= 0.25 or perigee < 2,000 km with apogee >= 2,000 km",
            "above_geo": "perigee altitude >= 35,786 km",
            "unclassified": "required or physically plausible orbital elements unavailable",
        },
        "counts": counts,
        "limitations": [
            "The ACTIVE group is a provider-defined subset, not all catalogued objects.",
            "Records without a parseable epoch and records more than 6 hours future-dated are excluded from the distribution and counted in quality metadata.",
            "Records older than 30 days are retained but flagged by stale_epoch_count; old elements may not represent current orbit state.",
            "These are derived orbit-regime counts, not collision warnings, manoeuvres, or service-impact indicators.",
            "Mean elements and broad altitude boundaries support approximate classification only; this is not a precise propagator or conjunction analysis.",
            "The GEO-like rule is a broad proxy based on mean motion and eccentricity, not an operational orbital-regime determination.",
            "Objects can change regime; counts depend on source epoch, source coverage, and provider group membership.",
            "Raw source records are processed in memory and are not written to the public repository.",
        ],
        "attribution": "Source: CelesTrak. Derived summary produced by Space Risk Radar. See CelesTrak usage policy and GP format documentation.",
        "references": [
            "https://celestrak.org/usage-policy.php",
            "https://celestrak.org/NORAD/documentation/gp-data-formats.php",
        ],
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="run local classification tests without network access")
    parser.add_argument("--output", default=str(OUT), help="summary JSON output path")
    args = parser.parse_args()
    if args.check:
        self_test()
        return 0

    output = Path(args.output)
    now = datetime.now(timezone.utc)
    if output.exists():
        try:
            previous = json.loads(output.read_text(encoding="utf-8"))
            last = parse_time(previous.get("retrieved_at_utc"))
            if last and (now - last).total_seconds() < MIN_REFRESH_HOURS * 3600:
                print(f"Skipping fetch: last successful retrieval was {last.isoformat()} (minimum interval {MIN_REFRESH_HOURS} h).")
                return 0
        except (OSError, json.JSONDecodeError, AttributeError):
            pass

    records = retrieve_records()
    summary = build_summary(records, now)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote derived summary for {len(records)} ACTIVE-group records to {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
