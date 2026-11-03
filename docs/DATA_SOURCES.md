# Data sources and interpretation

Last reviewed: 3 November 2026

## Primary source: ESA Space Debris User Portal

URL: https://sdup.esoc.esa.int/discosweb/statistics/  
Portal summary update: 2 November 2026

Headline indicators shown by the portal:
- About 47,280 objects regularly tracked and maintained in space-surveillance catalogues.
- More than 660 break-ups, explosions, collisions or anomalous events resulting in fragmentation.
- MASTER-8 reference population (02/2026): 68,450 objects larger than 10 cm, including approximately 11,300 active payloads.
- Approximately 1.5 million debris objects greater than 1 cm and up to 10 cm.
- Approximately 230 million debris objects greater than 1 mm and up to 1 cm.

### Source discrepancy

The same portal's detailed table reports 47,290, while the headline summary reports about 47,280. The dashboard displays the headline summary and retains this discrepancy. Do not silently reconcile the two values.

### Interpretation

Catalogue counts, modelled populations and cumulative fragmentation events are different measures. MASTER-8 figures are model estimates, not directly catalogued counts. "More than 660" is cumulative, not an annual rate.

## ESA Space Environment Report 2026

URL: https://www.esa.int/Space_Safety/Space_Debris/ESA_Space_Environment_Report_2026  
PDF: https://www.sdo.esoc.esa.int/publications/Space_Environment_Report_I10R0_20260501.pdf

Released 1 May 2026; data through end 2025. Publication date is not the data cut-off.

## Automated orbital and catalogue feeds

See [Feed assessment](FEED_ASSESSMENT.md) and [orbital archive notes](../data/orbital/README.md).

- **CelesTrak GP API:** required daily STATIONS OMM pilot. Orbital elements only; not collision alerts or manoeuvre records.
- **OrbitalWiki API:** optional daily catalogue-events and launch metadata snapshots. Its orbital elements are sourced from CelesTrak and are not ingested as a second independent orbital feed. ODbL attribution and upstream terms are recorded.
- **Orbital Watch Collision Watch:** public selected CDM-based conjunction reference, refreshed three times daily according to its page. Not automatically scraped; no stable documented public export/API contract was established.
- **SatNOGS DB:** candidate for radio/transmitter metadata under CC BY-SA 4.0.
- **ESA DISCOSweb / Space-Track:** require further account, terms, rate-limit and redistribution review before automation.

## Data labels

- **OBSERVED / CATALOGUED:** measured, tracked or listed in a surveillance catalogue. Include epoch, catalogue/source and definition.
- **MODELLED:** estimated from a statistical or physical model. Include model version, size threshold and reference population date.
- **DERIVED:** calculated from other values. Document formula, input records and uncertainty.
- **REPORTED:** published by an identified source but not independently verified by this project.

Every maintained dataset must retain source URL, retrieval time, reference date, definition, uncertainty and verification status. Missing months remain gaps; no interpolation by default.
