# Orbit distribution pilot — data quality and classification limits

Status: implemented in the public preview on the quality-gate branch; release through PR review only. Production repository remains untouched.

## Scope and source

The chart summarizes records returned by CelesTrak's public GP/OMM `ACTIVE` group. This is a provider-defined subset, not a complete catalogue of active spacecraft, all tracked objects, or orbital debris. The raw response is processed in memory and is not committed to the public repository; only aggregate statistics and quality metadata are published.

## Source-epoch anomaly: resolution

The previous snapshot was retrieved at `2026-11-04T05:58:25Z` but reported a maximum element epoch of `2026-11-05T12:48:42Z`, about 30 hours later than retrieval. That is a data-quality inconsistency for a snapshot described as current. The stored aggregate does not contain object-level raw records, so the individual offending record IDs cannot be reconstructed retrospectively from the public snapshot. It would be misleading to claim that the upstream cause has been conclusively identified.

The safe operational resolution is to prevent future-dated elements from influencing the chart:
- Use the UTC retrieval timestamp as the reference.
- Exclude records with no parseable `EPOCH`.
- Exclude records whose `EPOCH` is more than 6 hours after retrieval. The six-hour tolerance is an engineering guard for modest clock skew, not a claim that future epochs are physically valid.
- Preserve the raw maximum epoch and publish exclusion counts so the anomaly remains auditable without republishing raw records.
- Retain elements older than 30 days but expose their count as stale; a later policy may exclude them if the resulting coverage remains adequate.
- Refuse to publish a snapshot if no records pass the epoch gate.
- Run offline tests for future, missing, and valid epochs.

This resolves the dashboard's exposure to future-dated elements, but does not prove why CelesTrak returned them. If the anomaly recurs, record the retrieval timestamp, aggregate counts and raw maximum, then seek provider clarification. Do not store the full response in the public repository just to investigate it.

## Quality metrics

The summary now distinguishes:
- `raw_record_count`: number of records returned by the provider.
- `record_count`: number of records passing the epoch gate and included in category counts.
- `excluded_future_epoch_count`: future-dated records excluded.
- `missing_or_invalid_epoch_count`: records without a parseable epoch excluded.
- `stale_epoch_count`: included records with epochs more than 30 days old.
- `source_epoch_min_utc` and `source_epoch_max_utc`: range used for the chart.
- `raw_source_epoch_max_utc`: maximum parsed epoch seen in the raw response, including excluded records.

Category totals must equal `record_count`. `classified_count` must not exceed `record_count`.

## Classification limitations

Perigee and apogee are approximated from mean motion and eccentricity using a two-body relationship. These broad buckets are not a high-precision orbit propagator, mission-purpose classification, conjunction analysis or collision probability:
- LEO: calculated apogee below 2,000 km.
- GEO-like: mean motion 0.9–1.1 revolutions/day and eccentricity no greater than 0.1; a broad proxy only.
- HEO/crossing: eccentricity at least 0.25, or perigee below 2,000 km while apogee reaches/exceeds 2,000 km.
- MEO: perigee at least 2,000 km and apogee below 35,786 km, excluding the earlier categories.
- Above GEO: perigee at least 35,786 km.
- Unclassified: elements are absent or do not fit these simplified rules.

Boundaries are heuristic and can create category discontinuities. Mean elements are time-tagged and can age; membership in the provider's ACTIVE group can change. A record count is not necessarily a count of unique physical objects unless object identifiers and duplicate policy are explicitly validated. No category count says anything by itself about collision warnings, manoeuvres, debris completeness, satellite service dependencies or DTAG impact.

## Release gates

1. Offline tests and Python compilation pass.
2. New summary has valid timestamps, non-empty epoch-qualified records and category totals that reconcile.
3. Exclusion and stale counts are visible in the dashboard.
4. The scheduled/manual update workflow succeeds and the published JSON is inspected.
5. Only after review is this branch merged to preview `main`. Production v1.1 remains unchanged.
