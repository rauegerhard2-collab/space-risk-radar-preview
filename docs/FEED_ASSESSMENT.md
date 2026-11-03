# Orbital and event feed assessment

Reviewed: 3 November 2026

## CelesTrak GP API — primary orbital-element feed

Official documentation: https://celestrak.org/NORAD/documentation/gp-data-formats.php  
Usage policy: https://celestrak.org/usage-policy.php

CelesTrak publishes general perturbations/orbital element sets in CCSDS OMM-compatible JSON, CSV, XML and KVN. OMM is preferred for forward compatibility with catalog numbers beyond five digits. The automated pilot retrieves only the STATIONS group once daily and preserves the records unchanged with a UTC retrieval timestamp and per-object epoch.

**Decision:** required primary feed. This is a limited group, not a global catalogue, collision-warning feed or manoeuvre register.

## OrbitalWiki API — complementary catalogue events and launch metadata

Developer documentation: https://www.orbitalwiki.com/developers  
API quickstart: https://www.orbitalwiki.com/developers/quickstart  
Sources and licence register: https://www.orbitalwiki.com/sources  
Terms: https://www.orbitalwiki.com/terms

OrbitalWiki documents public, read-only endpoints for catalogue events and launch records that do not require an API key. The ingestion workflow now retrieves:
- `/api/v1/events` — catalogue changes such as first appearances, recorded re-entries and significant orbit changes.
- `/api/v1/launches` — launch metadata and associated catalogue object counts.

The API's orbital-elements endpoint is deliberately not ingested: OrbitalWiki says its elements are sourced from CelesTrak, so using both as orbital-element feeds would duplicate upstream data rather than provide an independent observation. OrbitalWiki is an early-access service; endpoint availability and schemas may change. The workflow validates that responses are non-empty JSON, preserves the raw payload and records source/time. Optional-feed failures are logged without invalidating the primary CelesTrak snapshot.

OrbitalWiki describes its reconciled database as ODbL-1.0 and identifies upstream source terms separately. Attribution is retained in each archived envelope. Its public catalogue is useful enrichment, not an independent space-surveillance sensor or operational safety source.

## Orbital Watch — public conjunction information, not yet an automated feed

Collision Watch: https://orbitalwatch.app/collision-watch

Orbital Watch publishes a public selected subset of conjunction information sourced from the Space-Track public CDM catalogue and states that it refreshes three times daily. It also explicitly warns that the public subset is not comprehensive because some operator data are not released and some probability values may be rounded.

**Decision:** include as a reviewed public reference and manual cross-check, but do not scrape its HTML. No stable, documented machine-readable export/API contract was established for this integration. Scraping a changing presentation page would risk silently changing field meanings, missing records or duplicating Space-Track CDMs. Revisit if the provider publishes a supported API or export schema.

## Other candidates

### SatNOGS DB
API documentation: https://docs.satnogs.org/projects/satnogs-db/en/latest/api.html  
Live API schema: https://db.satnogs.org/api/schema/docs/  
About / data terms: https://db.satnogs.org/about/

SatNOGS DB provides a public read API for community-maintained satellite and transmitter metadata. Its own documentation says API data are freely distributed under CC BY-SA; the project description identifies the data as volunteer-contributed. This is useful for radio-frequency/transponder enrichment, not a source of precise orbital ephemerides or conjunction warnings.

**Decision:** approved as a candidate for a separately labelled metadata layer, subject to a bounded read-only API integration test. Before enabling scheduled ingestion, verify pagination, response envelopes, object identifiers, update timestamps, practical response size and attribution requirements against the live schema. Preserve provider data separately from CelesTrak/OrbitalWiki; do not treat transmitter metadata as evidence that a satellite is operational or that a telecommunications service depends on it. No API write endpoints will be used.

### ESA DISCOSweb
Portal: https://discosweb.esoc.esa.int/  
ESA DISCOS is valuable for object identity, launch and spacecraft metadata. Registration and acceptance of current terms are required; ESA states that surveillance orbital/attitude ephemerides are not distributed through DISCOSweb. Source acknowledgement is required for derived works or redistribution. Not yet automated.

### Space-Track
Documentation: https://www.space-track.org/documentation  
Space-Track provides GP/OMM, catalogue, decay and CDM classes, with explicit rate limits and retrieval rules. CDM access and redistribution need a project-owned account, credentials handling and terms review. Credentials must never be committed to this public repository. A public Orbital Watch page is not a substitute for direct permission or a complete CDM archive.

## Collision-warning data limitations

Orbital elements alone are not collision warnings. A defensible conjunction product requires suitable ephemerides, covariance/uncertainty, close-approach time and distance, probability definition, screening coverage, object identity resolution and provenance. Operational warnings and executed manoeuvres may be restricted or unavailable publicly.

The project therefore keeps four layers separate:
1. Orbital element observations/catalogue records.
2. Derived propagated positions (with model, epoch and uncertainty).
3. Conjunction screening / warning messages.
4. Operator risk decisions and confirmed manoeuvres.

No layer may be inferred from another. A map based on a selected object group is not a global risk map.
