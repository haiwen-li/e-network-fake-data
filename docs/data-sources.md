# Document Registry

All documents listed here are publicly available court records or government releases.
The pipeline reads this file to know which documents to fetch and process.

## How to Add a New Document

1. Add an entry to the `documents:` YAML block below.
2. Each entry must have a unique `id` (lowercase, hyphens only).
3. Run `python main.py fetch --new-only` to process only new entries.
4. Alternatively, drop a `.txt` file in `data/text/` and run:
   ```bash
   python main.py register-local data/text/your-file.txt --id your-doc-id --title "Your Title"
   ```

## Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique slug (e.g. `maxwell-depo-2016`) |
| `title` | Yes | Human-readable title |
| `url` | Yes* | Direct URL to PDF (*or leave empty for local files) |
| `source` | No | Origin (courtlistener, archive.org, justice.gov, local) |
| `date` | No | Document date (YYYY-MM-DD) |
| `notes` | No | Why this document is relevant |

---

## Document List

```yaml
documents:

  # ── Maxwell / Giuffre Civil Case ──────────────────────────────────────────

  - id: maxwell-depo-2016-pt1
    title: "Ghislaine Maxwell Deposition 2016 (Part 1, unsealed 2022)"
    url: "https://www.courtlistener.com/docket/4355835/725/giuffre-v-maxwell/"
    source: courtlistener
    date: "2016-04-22"
    notes: "Maxwell questioned about Epstein associates; names many individuals directly"

  - id: maxwell-depo-2016-pt2
    title: "Ghislaine Maxwell Deposition 2016 (Part 2, unsealed 2022)"
    url: "https://www.courtlistener.com/docket/4355835/726/giuffre-v-maxwell/"
    source: courtlistener
    date: "2016-04-22"
    notes: "Continuation — travel, properties, and contacts discussed"

  - id: giuffre-flight-logs
    title: "Jeffrey Epstein Flight Logs (Giuffre v. Maxwell exhibit)"
    url: "https://archive.org/download/EpsteinFlightLogs/EpsteinFlightLogs.pdf"
    source: archive.org
    date: "2015-01-01"
    notes: "Passenger manifests for Epstein's aircraft — strong tie evidence"

  - id: giuffre-complaint-2015
    title: "Giuffre v. Maxwell Amended Complaint (2015)"
    url: "https://www.courtlistener.com/docket/4355835/13/giuffre-v-maxwell/"
    source: courtlistener
    date: "2015-12-30"
    notes: "Names individuals alleged to have participated in abuse network"

  - id: maxwell-exhibit-nda
    title: "Maxwell Case — NDA and Settlement Documents (Unsealed 2022)"
    url: "https://www.courtlistener.com/docket/4355835/745/giuffre-v-maxwell/"
    source: courtlistener
    date: "2022-01-06"
    notes: "Reveals organizational and financial relationships"

  - id: doe-v-epstein-2019
    title: "Jane Doe v. Jeffrey Epstein — 2019 Complaint"
    url: "https://www.courtlistener.com/docket/6530298/1/jane-doe-v-epstein/"
    source: courtlistener
    date: "2019-08-15"
    notes: "Details on Palm Beach and New York operations"

  # ── DOJ / SDNY Criminal Case ──────────────────────────────────────────────

  - id: sdny-indictment-2019
    title: "SDNY Indictment of Jeffrey Epstein (July 2019)"
    url: "https://www.justice.gov/usao-sdny/press-release/file/1182951/download"
    source: justice.gov
    date: "2019-07-08"
    notes: "Formal charges; identifies co-conspirators and locations"

  - id: maxwell-sdny-indictment-2020
    title: "SDNY Indictment of Ghislaine Maxwell (June 2020)"
    url: "https://www.justice.gov/usao-sdny/press-release/file/1291491/download"
    source: justice.gov
    date: "2020-06-29"
    notes: "Maxwell charges; corroborates network structure from civil case"

  - id: maxwell-sdny-superseding-2021
    title: "SDNY Superseding Indictment of Maxwell (March 2021)"
    url: "https://www.justice.gov/usao-sdny/press-release/file/1376496/download"
    source: justice.gov
    date: "2021-03-29"
    notes: "Added charges; expands on trafficking routes and associates"

  # ── DOJ 2024 Document Release ─────────────────────────────────────────────

  - id: doj-epstein-release-2024-summary
    title: "DOJ Epstein Investigation Summary (2024 Public Release)"
    url: "https://www.justice.gov/archives/dag/page/file/1369801/download"
    source: justice.gov
    date: "2024-01-01"
    notes: "Government summary of investigation findings and network"

  # ── Palm Beach Police / State Investigation ───────────────────────────────

  - id: palm-beach-police-report-2005
    title: "Palm Beach Police Department Epstein Investigation Report (2005-2006)"
    url: "https://archive.org/download/palm-beach-epstein-police-report/palm-beach-epstein-police-report.pdf"
    source: archive.org
    date: "2006-05-01"
    notes: "Local law enforcement investigation; victim statements and associates named"

  - id: acosta-plea-agreement-2008
    title: "Non-Prosecution Agreement (Epstein / Acosta, 2008)"
    url: "https://www.courtlistener.com/docket/4355835/140/giuffre-v-maxwell/"
    source: courtlistener
    date: "2008-09-24"
    notes: "Controversial NPA; reveals government actors and legal network"

  # ── Maxwell Criminal Trial Documents ──────────────────────────────────────

  - id: maxwell-trial-govt-exhibit-list
    title: "Maxwell Criminal Trial — Government Exhibit List"
    url: "https://www.courtlistener.com/docket/12165952/maxwell-trial-exhibit-list/"
    source: courtlistener
    date: "2021-12-01"
    notes: "Catalogue of evidence; cross-references documents and witnesses"

  - id: maxwell-trial-witness-statements
    title: "Maxwell Trial — Victim Witness Statements (Redacted)"
    url: "https://www.courtlistener.com/docket/12165952/maxwell-witness-statements/"
    source: courtlistener
    date: "2021-11-30"
    notes: "Redacted witness accounts; locations and named individuals"

  - id: maxwell-sentencing-memo-2022
    title: "Maxwell Sentencing Memorandum (2022)"
    url: "https://www.courtlistener.com/docket/12165952/maxwell-sentencing-memo/"
    source: courtlistener
    date: "2022-06-28"
    notes: "Government summary of Maxwell's role; network overview"

  # ── Unsealed Doe Lawsuit Documents (2024) ─────────────────────────────────

  - id: doe-epstein-unsealed-2024-batch1
    title: "Unsealed Epstein Documents — Batch 1 (January 2024)"
    url: "https://www.courtlistener.com/docket/4355835/doe-epstein-unsealed-batch1/"
    source: courtlistener
    date: "2024-01-03"
    notes: "First batch of unsealed documents; names previously redacted individuals"

  - id: doe-epstein-unsealed-2024-batch2
    title: "Unsealed Epstein Documents — Batch 2 (January 2024)"
    url: "https://www.courtlistener.com/docket/4355835/doe-epstein-unsealed-batch2/"
    source: courtlistener
    date: "2024-01-08"
    notes: "Second batch; additional associates and financial relationships"

  # ── Miami Herald / Investigative Journalism Exhibits ──────────────────────

  - id: miami-herald-exhibit-A
    title: "Miami Herald Investigation Exhibit A — Victim Accounts"
    url: "https://www.documentcloud.org/documents/5677917-Exhibit-A-Epstein-Victims.pdf"
    source: documentcloud.org
    date: "2018-11-28"
    notes: "Miami Herald 'Perversion of Justice' investigation source documents"

  - id: miami-herald-exhibit-B
    title: "Miami Herald Investigation Exhibit B — NPA Records"
    url: "https://www.documentcloud.org/documents/5677918-Exhibit-B-NPA-Records.pdf"
    source: documentcloud.org
    date: "2018-11-28"
    notes: "Documents related to controversial non-prosecution agreement"

  - id: epstein-contact-book-partial
    title: "Jeffrey Epstein's Contact Book (Partial, via Gawker 2015)"
    url: "https://archive.org/download/EpsteinBlackBook/EpsteinBlackBook.pdf"
    source: archive.org
    date: "2015-01-23"
    notes: "Scanned pages of Epstein's address book; raw network data for many associates"
```

---

## Notes on URL Reliability

Some CourtListener and DocumentCloud URLs may change or require direct PACER access.
If a URL fails, the fetcher will log the error and skip the document — other documents
in the registry will continue to be processed. Use `register-local` to manually add
documents you have downloaded independently.
