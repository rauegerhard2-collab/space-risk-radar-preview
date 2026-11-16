# Automated data refresh and publication

## Operating model

The Preview repository uses a two-stage process. Production is not connected to the Preview workflows.

1. **Daily staging (06:17 UTC):** CelesTrak ACTIVE is processed into a derived orbit-distribution summary. CelesTrak STATIONS OMM, OrbitalWiki catalogue events and OrbitalWiki launch metadata are fetched separately.
2. **Daily validation and logging:** the orbit-distribution self-test, JSON structure and minimum record counts are checked. Every actual retrieval has a UTC timestamp in data/source-log.jsonl; provider generation times and per-object orbital epochs remain separate. Failed attempts are logged, successful feeds can still be staged, and a failed or empty feed never replaces its last-known-good snapshot.
3. **Isolated staging branch:** daily snapshots and the retrieval log are committed to data-staging, not main. A failed feed is visible in the log and blocks the weekly publication gate.
4. **Weekly automatic publication (Monday 08:30 UTC):** the publication workflow copies only the staged data files into the Preview main branch after all four maintained feeds pass freshness, schema, timestamp and record-count checks. It does not require a pull-request merge. A failed gate leaves the published main data untouched. After a successful data commit, the workflow explicitly starts and verifies the Preview Pages deployment.
5. **Monthly quality review:** assess source freshness, coverage, polling gaps, data quality, failures, licensing and trend interpretation. ESA public statistics remain manually checked because their publication cadence is provider-controlled; the Orbital Radar iframe is independently maintained by its provider.

## Feeds and limitations

- **CelesTrak ACTIVE:** provider-defined subset used for approximate derived orbit-regime counts; not a complete catalogue, conjunction-warning feed or collision-risk product.
- **CelesTrak STATIONS:** selected station group only; not a global satellite or debris catalogue.
- **OrbitalWiki events and launches:** complementary catalogue metadata. Event history is limited; a long polling gap may not be recoverable. These are not independent orbital-surveillance observations.
- **ESA public environment metrics:** manually verified when the provider publishes updated material; not represented as a daily feed.
- **Orbital Radar embed:** external service; refresh cadence and availability are controlled by Orbital Radar.

## Publication gates and failure behavior

- The latest logged attempt for each maintained feed must be successful and within 48 hours of publication.
- The source-log retrieval timestamp must match the timestamp in the corresponding snapshot.
- JSON must parse, expected arrays and objects must be present, and record counts must agree between the snapshot and source log.
- The ACTIVE orbit distribution must pass the local classification and epoch-quality self-test; orbit-class counts must sum to the quality-approved record count.
- A failed feed is logged. Its previous snapshot is retained. The weekly publisher refuses to copy any data to main while the latest attempt for any maintained feed is failed, missing, stale or inconsistent.
- The footer's date is populated from the actual ACTIVE snapshot retrieval timestamp. The “Status aktualisieren” button only reloads the published source log; it does not start a feed retrieval or workflow.

## Schedule

| Process | Cadence | UTC |
|---|---:|---:|
| Data staging | Daily | 06:17 |
| Validated Preview publication | Weekly, Monday | 08:30 |
| Source/quality assessment | Monthly | Manual review |

GitHub scheduled workflows are best-effort and may start later than the cron minute. Stored retrieval timestamps, not the schedule time or footer date alone, are authoritative. This dashboard is a public-information and situational-awareness aid, not an operational conjunction assessment or collision-avoidance system.
