# Automated data refresh and publication

## Operating model

The Preview repository uses a two-stage process. Production is not connected to these workflows.

1. **Daily staging (06:17 UTC):** CelesTrak STATIONS OMM, OrbitalWiki catalogue events and OrbitalWiki launch metadata are fetched. The existing CelesTrak ACTIVE orbit-distribution calculation is also run.
2. **Validation:** JSON shape and minimum record counts are checked. Each snapshot records its retrieval time separately from provider event times or per-object orbital epochs. Failed feeds leave their last-known-good snapshot untouched and produce an explicit failed workflow/source-log entry.
3. **Isolated staging branch:** daily data are committed to `data-staging`, not `main`. This does not deploy the website.
4. **Weekly review (Monday 08:30 UTC):** a pull request from `data-staging` to `main` is opened for review. Only merging that PR publishes the refreshed snapshots to the Preview Pages site.
5. **Monthly review:** assess source freshness, coverage, data quality, failures and trend interpretation. ESA public statistics remain manually checked because their publication cadence is provider-controlled; the Orbital Radar iframe is independently maintained by its provider.

## Feeds and limitations

- **CelesTrak STATIONS:** selected station group only; not a global catalogue, conjunction-warning feed or manoeuvre register.
- **CelesTrak ACTIVE orbit distribution:** provider-defined ACTIVE subset; approximate derived orbit-regime counts, not collision risk.
- **OrbitalWiki events and launches:** complementary catalogue metadata. Event history is limited; a long polling gap may not be recoverable. Not independent orbital surveillance.
- **ESA public environment metrics:** manually verified, not represented as a daily feed.
- **Orbital Radar embed:** external service; refresh cadence and availability are controlled by Orbital Radar.

## Safety and integrity controls

- A failed or empty response cannot replace the latest good snapshot.
- Each successful snapshot carries a UTC retrieval timestamp; provider timestamps are preserved as supplied.
- Each feed failure is logged with status and reason.
- Raw CelesTrak orbital records are retained only for the documented STATIONS group. No credentials are required or stored.
- This dashboard is a public-information and situational-awareness aid, not an operational collision-avoidance or conjunction-warning service.

## Schedule

| Process | Cadence | UTC |
|---|---:|---:|
| Data staging | Daily | 06:17 |
| Review PR | Weekly, Monday | 08:30 |
| Source/quality assessment | Monthly | Manual review |

GitHub scheduled workflows are best-effort and may start later than the cron minute. The timestamps stored in each data file are the authoritative retrieval times.
