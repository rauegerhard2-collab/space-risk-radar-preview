# Source access and reuse review

Reviewed: 2026-11-03  
Purpose: identify public or permission-based sources for orbital distribution, conjunction-warning statistics, and manoeuvre activity. This is a technical screening, not legal advice or a guarantee that every downstream use is permitted.

## Decision summary

| Source | Data useful for | Access / reuse status | Decision |
|---|---|---|---|
| CelesTrak GP/OMM | Orbital distribution, current catalogue snapshots | Public queries; explicit usage policy and rate limits apply. OMM JSON/CSV/XML supported. | Use cautiously; cache snapshots and comply with usage policy. Do not poll large groups repeatedly. |
| CelesTrak historical GP archives | Historical orbital-element snapshots | Public request workflow for unclassified objects; request limits apply. Historical element sets are not conjunction warnings. | Candidate for orbit-distribution history after feasibility and attribution review. |
| OrbitalWiki API | Catalogue events, reentries, launches and orbital elements | Public endpoints documented without API key for selected routes. OrbitalWiki describes its reconciled database as ODbL-1.0; upstream source terms remain applicable. | Continue current events/launches feeds. Any bulk elements use must include attribution and ODbL compliance review; not independent of CelesTrak. |
| Orbital Watch Collision Watch | Selected public conjunction information | Public page, but no stable documented public API/export contract established by this review. Partial coverage. | Manual reference only. Do not scrape page or present as global total. Ask provider about an approved export/API. |
| Space-Track.org | Satellite catalogue and potentially CDM-related data | Registration and terms apply; dataset availability and redistribution rights vary. | Await account/access and exact terms. Do not ingest or redistribute restricted data without permission. |
| ESA DISCOSweb | Object identity, launch and spacecraft metadata | Registration/terms apply; access to some datasets may be restricted. ESA's general terms do not override third-party rights. | Await terms/account review; use only permitted fields and preserve attribution. Not a conjunction or manoeuvre feed. |
| ILRS / IDS mission manoeuvre histories | Confirmed mission-specific manoeuvre records | Public histories for selected missions; explicitly not comprehensive across all satellites. | Integrate as a clearly scoped selected-missions dataset if source file formats and reuse notices are checked. |
| SatNOGS DB | Community-maintained satellite/transmitter metadata | Public API; project documentation states CC BY-SA terms. | Candidate for a separate radio/transmitter metadata layer only; not orbit or collision evidence. Check current API schema and attribution before scheduled ingestion. |
| NASA TLE API | Orbital elements | Public API description says data are updated from CelesTrak. | Do not ingest as an independent source; duplicates upstream data. |
| maneuver-detect research code/data | Algorithmic identification of orbit changes | Public research code/data candidate; verify repository licence, dataset provenance, and reproducibility before use. | Candidate for an explicitly labelled derived/algorithmic layer, not confirmed collision-avoidance manoeuvres. |

## Product requirements for new feeds

Each source adapter must record:
- source name and canonical URL;
- licence/terms and review date;
- retrieval time (UTC) and source reference epoch;
- schema/version and record count;
- object/event identifiers and deduplication key;
- whether records are observed, catalogued, modelled, reported or derived;
- known coverage, latency, and missingness;
- whether redistribution of raw records is permitted.

## Statistical definitions

### Orbit distribution
Use one declared catalogue snapshot and calculate orbital regime from documented orbital elements. Publish the classification boundaries and treatment of eccentric orbits. Keep source catalogue membership and operational-status classification separate. A catalogue snapshot is not a complete census of all objects in orbit.

### Conjunction warnings
Count unique conjunction events only if the feed supplies stable event/object-pair identifiers and a defined time window. Distinguish messages, unique conjunctions, re-screenings, and high-risk alerts. Do not add records from overlapping providers until overlap can be deduplicated. Show the covered provider/object subset and its update window.

### Manoeuvre activity
Keep separate counts for (1) operator/mission-confirmed manoeuvres, (2) public reported avoidance manoeuvres, and (3) algorithmically inferred orbit changes. Do not label a detected orbit change as collision avoidance without independent evidence.

## Open questions for DLR / providers

1. Which CDM or conjunction dataset is accessible for research/public-interest use, and with what historical depth?
2. Are raw records allowed to be retained in a public GitHub repository, or may only derived statistics be published?
3. Are there rate limits, attribution requirements, non-commercial restrictions, or publication approval requirements?
4. Is a global or regional manoeuvre dataset available, and are manoeuvre purpose and confidence fields included?
5. Can a licence or written permission be supplied that explicitly covers public redistribution and derivative visualisations?

## Sources checked

- CelesTrak GP formats: https://celestrak.org/NORAD/documentation/gp-data-formats.php
- CelesTrak usage policy: https://celestrak.org/usage-policy.php
- CelesTrak historical archive requests: https://www.celestrak.org/NORAD/archives/request.php?FORMAT=xml
- OrbitalWiki developer API: https://www.orbitalwiki.com/developers
- OrbitalWiki terms: https://www.orbitalwiki.com/terms
- Orbital Watch Collision Watch: https://orbitalwatch.app/collision-watch
- Space-Track: https://www.space-track.org/
- ESA DISCOSweb: https://discosweb.esoc.esa.int/
- ILRS manoeuvre histories: https://ilrs.gsfc.nasa.gov/data_and_products/predictions/maneuver.html
- SatNOGS DB: https://db.satnogs.org/about/
- NASA Open APIs / TLE API: https://api.nasa.gov/

## Status

No restricted dataset was added. This document records source screening and safe integration criteria. New raw data feeds should be enabled only after the source's current terms, coverage, schema, and redistribution rights are confirmed.
