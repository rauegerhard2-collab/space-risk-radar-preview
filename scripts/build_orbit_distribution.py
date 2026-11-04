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
    print(f"Self-test passed: {len(cases)} classification cases")


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
    counts = {
        "leo": 0,
        "meo": 0,
        "geo_like": 0,
        "heo_or_crossing": 0,
        "above_geo": 0,
        "unclassified": 0,
    }
    epochs = []
    for record in records:
        counts[classify(record)] += 1
        epoch = parse_time(record.get("EPOCH"))
        if epoch:
            epochs.append(epoch.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"))
    return {
        "schema_version": 1,
        "source": "CelesTrak GP/OMM ACTIVE group",
        "source_url": URL,
        "retrieved_at_utc": retrieved_at.isoformat().replace("+00:00", "Z"),
        "source_epoch_min_utc": min(epochs) if epochs else None,
        "source_epoch_max_utc": max(epochs) if epochs else None,
        "scope": "Records returned by the CelesTrak ACTIVE group only; not a complete global catalogue.",
        "record_count": len(records),
        "classified_count": len(records) - counts["unclassified"],
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
            "These are derived orbit-regime counts, not collision warnings, manoeuvres, or service-impact indicators.",
            "Mean elements and broad altitude boundaries support approximate classification only.",
            "Objects can change regime; counts depend on source epoch and group membership.",
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
