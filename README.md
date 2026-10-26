# Body Composition Report Studio

Local FastAPI application that creates **clearly labeled generated** DEXA-style and InBody-style body composition summaries. It does **not** produce original scanner reports or invent unmeasured device values.

## Install and run (macOS / Linux)

```bash
cd bodycomp_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000.

## Features

- Two report styles, manual entry, instant browser preview
- PDF download and CSV import/export (first row)
- Calculated fat mass, fat-free mass, BMI
- Optional instrument-specific metrics are only shown when supplied
- Generated-report disclosure on every PDF

## Limitations / roadmap

This is an original *inspired* template, not an exact manufacturer layout. For higher fidelity, provide redacted sample printouts and build separate per-model templates (e.g., InBody 570 vs 770; different DEXA vendors). The app does not measure composition or calculate bone density, visceral fat, or regional composition from body fat percentage. It has no authentication, so run it locally rather than exposing it publicly. No data is persisted server-side. CSV files should be treated as sensitive personal data.

## Test

```bash
pytest -q
```

## Multi-date tracking workflow

1. Select DEXA-style or InBody-style and enter a measurement date, weight, body-fat percentage, and any actual device-specific measurements.
2. Click **Add / update dated entry**. Click **Next date** to move to another entry, or edit an existing entry from the history list.
3. Review the on-screen graphs and dated measurements table. Export **Download full PDF + graphs** or **Export all CSV**. Import an exported CSV to restore history.

Entries are stored in the current browser's local storage (not a shared server database). Export CSV regularly for backup. The PDF includes longitudinal trends, summary tables, and device-specific measurement tables. One person's data per history; no duplicate dates. Missing device measurements remain blank. The generated PDF is labeled as not device-verified.


## Expanded InBody fields (v3)
The InBody form now includes composition, segmental lean/fat, fluid balance, weight control, score, phase angle, and a raw impedance matrix (five segments at six frequencies). All fields are optional unless they are part of the basic weight/body-fat record. The exact set and available impedance frequencies vary by device model. The history PDF includes a complete field/value archive for each date; absent values are labeled Not provided. The browser shows all dated measurements in a wide table and graphs optional numeric metrics with at least two observations.

The app does **not** synthesize InBody Score, phase angle, impedance, visceral fat, segmental data, or any other proprietary instrument output. Enter actual instrument values when available. This is not an official InBody report.

## Version 4 improvements

- Guided section-by-section measurement entry, with a Show All option.
- Measurement-level provenance (measured / estimated / calculated) for optional inputs.
- Notes and device model per dated entry.
- Live consistency checks for body water totals, ECW/TBW, and outlying values.
- JSON backup/restore in addition to CSV export/import.
- Longitudinal PDF archive includes measurement provenance and review warnings.

Data is saved in the browser's localStorage. Back up to JSON/CSV regularly. The application does not perform scans or recreate instrument-derived metrics. Device model is descriptive and does not yet change field availability. No authentication or encrypted at-rest database is included, so run locally and avoid using it as a clinical record system.

## Offline-first measurements

Edit **`data/measurements.json`** before starting the local server. The file is the
authoritative source for all 15 demonstration entries. Each object in `entries`
represents one dated scan. You can edit `name`, `scan_date`, `weight_lb`,
`body_fat_pct`, `skeletal_muscle_lb`, `visceral_fat_level`, segmental
measurements, and other supported fields.

```bash
git pull origin main
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 and refresh after editing the JSON file.
The application validates the file and replaces stale browser history with its
contents at startup. Browser form edits do **not** write back to disk; edit the
JSON file to persist changes. To start with no previous demonstration entries,
replace the `entries` array with your own valid dated scans (at least one).
Keep `schema_version` at 1. All provided demonstration values are synthetic,
not actual instrument readings.

## Optional generated-report notices

Edit `data/report_config.json` offline before starting the server:

```json
{
  "show_generated_header_notice": false,
  "show_generated_footer_notice": false
}
```

These switches hide the two generic **generated-report** lines on reports
that do not contain synthetic measurements. They do **not** suppress
"SYNTHETIC DEMONSTRATION" or "SYNTHETIC DEMO - NOT REAL SCAN RESULTS"
on fictional demonstration reports, which must remain clearly identified.
The configuration is read whenever the PDF is generated.
