# Orbit distribution pilot — technical note

Status: proposed implementation on `feature/orbit-distribution-pilot`; not yet merged or published into the preview dashboard.

## Goal

Add a reproducible, low-volume statistical view of orbital regimes using one declared public orbital-element source. The pilot uses CelesTrak's GP/OMM `ACTIVE` group and publishes only derived aggregate counts, not the raw catalogue response.

## What it does

- Requests CelesTrak OMM-compatible JSON from the documented `GROUP=ACTIVE` query.
- Derives approximate perigee/apogee altitude from mean motion and eccentricity.
- Groups returned records into LEO, MEO, GEO-like, high-eccentricity/crossing, above-GEO, and unclassified categories.
- Records retrieval time, the min/max source epochs, record counts, method, caveats, and source attribution.
- Keeps raw source records in memory only; only the derived summary is written to `data/orbit-distribution/latest.json`.
- Has a 20-hour refresh guard to prevent repeated manual runs from repeatedly requesting the large group.
- Includes offline classification tests. The scheduled job runs once daily.

## Important interpretation limits

This is a distribution of the **CelesTrak ACTIVE group**, not the entire space-object catalogue, not all debris, and not a collision-risk map. Group membership is provider-defined. The GEO-like rule is a broad approximation. Counts are derived from mean orbital elements and do not prove actual satellite operational status, service dependency, conjunction risk, or avoidance manoeuvres.

The dashboard should not present these as "all objects in orbit". Recommended label: **"Orbit regime — CelesTrak ACTIVE group (derived snapshot)"**.

## Data-use safeguards

- Follow the current CelesTrak usage policy and format documentation.
- Request the large group no more than once per scheduled daily run; the local refresh guard also skips recent successful snapshots.
- Stop on HTTP errors; no retry loop.
- Do not store or republish the raw catalogue payload in this public repository.
- Preserve attribution, source URL, retrieval time, and object epoch coverage.
- Re-check provider terms before changing scope or increasing request frequency.

This is technical documentation, not legal advice. A public endpoint does not by itself guarantee permission for every downstream use.

## Validation and release gates

1. Offline tests and Python compilation pass.
2. A manual workflow run obtains a non-empty valid response and writes only the derived summary.
3. Review count totals, unclassified rate, epochs, and source terms.
4. Integrate a chart into the preview UI only after data output is reviewed.
5. Keep production v1.1 untouched; do not merge this pilot without explicit approval.
