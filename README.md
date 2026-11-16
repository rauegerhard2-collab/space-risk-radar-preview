# Space Risk Radar

Independent public information project for understanding the orbital environment.

**Live site:** https://rauegerhard2-collab.github.io/space-risk-radar/  
**Repository:** https://github.com/rauegerhard2-collab/space-risk-radar

## Project status

The interactive v1.2 dashboard is under review in draft PR #2. The public `main` branch and Pages site remain unchanged until explicit approval and merge.

## Scope

- Publicly documented orbital-environment indicators
- Catalogue snapshots and modelled debris-population estimates
- Fragmentation and re-entry context
- Public collision-avoidance information, where evidence is available
- Source transparency, data quality labels and explicit gaps

The project is independent and does not represent Deutsche Telekom AG, ESA or another organization.

## Data principles

1. Keep observed/catalogued values separate from modelled estimates.
2. Preserve each source's reference date, retrieval time and definition.
3. Do not interpolate missing months or manufacture event records.
4. Distinguish conjunction warnings, operator risk assessments and executed avoidance manoeuvres.
5. Record source URLs, attribution and retrieval dates for every maintained dataset.
6. Make uncertainty, coverage gaps and source dependencies visible.

## Automated data retrieval

Daily retrieval is staged on the isolated `data-staging` branch. A weekly publication workflow validates freshness, JSON structure, timestamps and record counts before copying only the data files to Preview `main` and deploying Preview Pages. Failed or stale feeds block publication and retain their last-known-good snapshots. The production repository remains separate until an explicit release decision.

- CelesTrak ACTIVE orbit distribution is refreshed daily as a derived summary.
- CelesTrak STATIONS OMM is a selected station-group snapshot, not a global catalogue.
- OrbitalWiki catalogue events and launch metadata are complementary enrichment feeds.
- ESA public statistics are manually checked when the provider publishes updates.
- Orbital Radar Collision Watch remains an externally maintained reference and is not treated as a feed.
- OrbitalWiki's elements endpoint is excluded because it republishes CelesTrak-derived orbital elements.
- SatNOGS DB, ESA DISCOSweb and Space-Track remain candidates subject to data-type, access, licensing and redistribution review.

See [automated refresh and publication](docs/AUTOMATED_DATA_REFRESH.md), [feed assessment](docs/FEED_ASSESSMENT.md) and [data sources](docs/DATA_SOURCES.md).

## Development

Changes are developed on feature branches. The public site is updated only after review and an explicit release decision.
