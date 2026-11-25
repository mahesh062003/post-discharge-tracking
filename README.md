# Discharge Summary Extraction Pipeline

Turns hospital discharge summary PDFs into structured patient records with
scheduled follow-up dates, ready for a tracking system to consume.

Discharge summaries are produced as PDFs and follow-ups tracked by hand, which
makes a missed appointment invisible until the patient returns. This pipeline
reads the summaries a hospital already produces, extracts the patient and
admission details, derives the follow-up date, and loads the records into
MongoDB.

---

## What it extracts

Thirteen fields per summary:

```
patient_id   ip_no        patient_name    gender_age   mobile_no
ward         bed          admission_date  discharge_date
patient_address           reason_for_admission         doctor_name
followup_date  (derived)
```

Three details that mattered in practice:

- **The layout is positional, not labelled.** `WARD` and `BED` share a line, and
  `PATIENT NAME` runs until the next all-caps label. Patterns use lookaheads
  against the *following* label rather than fixed offsets, so a summary that
  wraps a long address across two lines still parses.
- **Follow-up dates are derived.** Summaries carry a discharge date but no
  follow-up date; the review falls a fixed interval afterwards, which the
  pipeline computes rather than asking staff to enter.
- **Loads are idempotent.** Records upsert on `patient_id`, so re-running over
  an already-ingested directory updates rather than duplicates.

A summary with no recoverable `patient_id` is skipped and reported, never
inserted as a partial record.

---

## Usage

```bash
cd pipeline
pip install -r requirements.txt

cp ../.env.example ../.env     # set MONGO_URI and DISCHARGE_PDF_DIR
python extract.py
```

Connection string, database and collection names, input directory and the
follow-up interval all come from the environment.

## Sample data

Real discharge summaries contain identifiable patient information and are not
distributable. `sample_data/generate_sample.py` generates synthetic summaries
in the same layout, so the pipeline can be run and verified by anyone:

```bash
python sample_data/generate_sample.py   # writes 3 synthetic PDFs
python pipeline/extract.py              # ingests them
```

All thirteen fields extract from all three generated records, with follow-up
dates correctly derived.

## Stack

Python · PyMuPDF · MongoDB (PyMongo)

---

## Use

© 2026 Mahesh Veeraiah R. All rights reserved.

Published for review and assessment. Not licensed for reuse, redistribution or
modification — please get in touch about any other use.
