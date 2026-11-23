# Post-Discharge Patient Tracking & Appointment Scheduling

A system for Sri Ramakrishna Hospital that turns discharge summary PDFs into
tracked patient records with scheduled follow-up appointments, so that patients
discharged from inpatient care are not lost between discharge and review.

Discharge summaries were produced as PDFs and follow-ups were tracked manually,
which meant a missed follow-up was invisible until the patient returned — often
late. This system reads the summaries the hospital already produces, extracts
the patient and admission details, derives the follow-up date, and loads the
records into a database that a web application then surfaces to admin staff.

---

## My contribution

This was a team project. **I was responsible for the requirements and solution
design, and for the extraction pipeline** — the work in `design/` and
`pipeline/` in this repository.

| Area | Owner |
|---|---|
| Requirements, system architecture, module workflows | **me** |
| Discharge-summary extraction pipeline (`pipeline/extract.py`) | **me** |
| MongoDB schema design for the extracted records | **me** |
| MERN web application (Express API, React admin dashboard) | [Akkhilesh R P](https://github.com/akkhileshrp) |

The application implementation lives in Akkhilesh's repository:
[`akkhileshrp/sriramakrishnahospital`](https://github.com/akkhileshrp/sriramakrishnahospital).
This repository holds my own contribution and the design artefacts behind it.

---

## The extraction pipeline

The hospital's discharge summaries are text-layer PDFs in a fixed report
layout. `pipeline/extract.py` reads them with PyMuPDF and parses thirteen
fields out of the report body:

```
patient_id   ip_no       patient_name   gender_age   mobile_no
ward         bed         admission_date discharge_date
patient_address          reason_for_admission        doctor_name
followup_date  (derived)
```

Three details that mattered in practice:

- **The layout is positional, not labelled.** `WARD` and `BED` share a single
  line, and `PATIENT NAME` runs until the next all-caps field label — so the
  patterns use lookaheads against the *following* label rather than fixed
  offsets. A summary that wraps a long address onto two lines still parses.
- **Follow-up is derived, not recorded.** The summaries carry a discharge date
  but no follow-up date; the hospital's rule is a review fourteen days after
  discharge. The pipeline computes it (`FOLLOWUP_DAYS`, configurable) rather
  than requiring staff to enter it.
- **The load is idempotent.** Records upsert on `patient_id`, so re-running the
  pipeline over a directory that has already been ingested updates the existing
  records instead of duplicating patients.

A summary with no recoverable `patient_id` is skipped and reported rather than
inserted as a partial record.

---

## Running it

```bash
cd pipeline
pip install -r requirements.txt

cp ../.env.example ../.env     # then set MONGO_URI and DISCHARGE_PDF_DIR
python extract.py
```

Configuration is read from the environment — connection string, database and
collection names, input directory, and the follow-up interval. Nothing is
hardcoded.

### Sample data

**The real discharge summaries are not in this repository and will not be.**
They contain identifiable patient information — names, mobile numbers, home
addresses and admission diagnoses — belonging to real patients of a real
hospital. Publishing them would be a privacy breach regardless of the project
being complete.

`sample_data/generate_sample.py` instead generates synthetic summaries that
reproduce the report layout exactly, so the pipeline can be run and verified
by anyone:

```bash
python sample_data/generate_sample.py   # writes 3 synthetic PDFs
python pipeline/extract.py              # ingests them
```

Verified against the generated samples: all thirteen fields extract from all
three records, with follow-up dates correctly derived.

---

## Design artefacts

| File | What it covers |
|---|---|
| `design/project-initiation-document.pdf` | Problem statement, scope, stakeholders |
| `design/system-architecture.docx` | Component architecture and data flow |
| `design/module-workflows.docx` | Per-module workflows |
| `design/system-specification.docx` | Functional specification |
| `design/modules-overview.pdf` | Consolidated module overview |
| `design/presentation.pptx` | Project presentation |

---

## Stack

**Pipeline** — Python, PyMuPDF, MongoDB (PyMongo)
**Application** (Akkhilesh) — Express, Mongoose, React, Vite, Tailwind, JWT auth
