"""
Discharge-summary extraction pipeline.

Reads discharge summary PDFs, parses the patient and admission fields out of
the hospital's report layout, derives a follow-up date, and loads the records
into MongoDB for the tracking application to consume.

Configuration comes from the environment (see .env.example) so that no path,
credential or default ever lives in source.
"""

import glob
import os
import re
import sys
from datetime import datetime, timedelta

import fitz  # PyMuPDF
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGO_DB", "discharge_summaries")
COLLECTION_NAME = os.environ.get("MONGO_COLLECTION", "discharge_summaries")
PDF_DIR = os.environ.get("DISCHARGE_PDF_DIR")
FOLLOWUP_DAYS = int(os.environ.get("FOLLOWUP_DAYS", "14"))
DATE_FORMAT = "%d-%m-%Y"

# Field -> pattern. Grouped here so the report layout can be adjusted in one
# place rather than threaded through the parsing logic.
PATTERNS = {
    "patient_id": r"PATIENT ID\s+([A-Za-z0-9]+)",
    "ip_no": r"IP NO\s+(\d+)",
    "patient_name": r"PATIENT NAME\s+(.+?)(?=\nGENDER / AGE|\n)",
    "gender_age": r"GENDER / AGE\s+(.+?)(?=\nMOBILE NO|\n)",
    "mobile_no": r"MOBILE NO\s+(\d+)",
    "admission_date": r"D\.O\.A\s+(\d{2}-\d{2}-\d{4})",
    "discharge_date": r"D\.O\.D\s+(\d{2}-\d{2}-\d{4})",
    "patient_address": r"PATIENT ADDRESS\s+(.+?)(?=\n[A-Z]+|\n)",
    "reason_for_admission": r"REASON FOR ADMISSION\s*:\s*(.+?)(?=\nPAST HISTORY|\n$)",
    "doctor_name": r"DR\.(.*?)\s*(?:DNB|DM|FESC|FSCAI|USA)",
}

# Ward and bed arrive in a single line, so they need their own two-group match.
WARD_BED_PATTERN = r"WARD\s+([A-Za-z\s-]+)\s+BED\s+([A-Za-z0-9]+)"


def connect_to_mongo():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME][COLLECTION_NAME]


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as exc:
        print(f"Error extracting text from {pdf_path}: {exc}")
    return text


def calculate_followup_date(discharge_date_str):
    """The follow-up appointment falls FOLLOWUP_DAYS after discharge."""
    try:
        discharge_date = datetime.strptime(discharge_date_str, DATE_FORMAT)
        return (discharge_date + timedelta(days=FOLLOWUP_DAYS)).strftime(DATE_FORMAT)
    except ValueError as exc:
        print(f"Error calculating follow-up date: {exc}")
        return None


def parse_patient_details_from_text(text):
    details = {field: None for field in PATTERNS}
    details.update({"ward": None, "bed": None, "followup_date": None})

    for field, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            details[field] = match.group(1).strip().replace("\n", " ")

    ward_bed = re.search(WARD_BED_PATTERN, text)
    if ward_bed:
        details["ward"] = ward_bed.group(1).strip()
        details["bed"] = ward_bed.group(2).strip()

    if details["discharge_date"]:
        details["followup_date"] = calculate_followup_date(details["discharge_date"])

    return details


def process_pdf_directory(directory_path):
    pdf_files = sorted(glob.glob(os.path.join(directory_path, "*.pdf")))
    if not pdf_files:
        print(f"No PDFs found in {directory_path}")
        return

    collection = connect_to_mongo()
    inserted = skipped = 0

    for pdf_file in pdf_files:
        details = parse_patient_details_from_text(extract_text_from_pdf(pdf_file))

        if not details.get("patient_id"):
            print(f"Skipping {os.path.basename(pdf_file)} - no patient ID found")
            skipped += 1
            continue

        # Idempotent load: re-running the pipeline updates rather than duplicates.
        collection.update_one(
            {"patient_id": details["patient_id"]}, {"$set": details}, upsert=True
        )
        inserted += 1
        print(f"Loaded {details['patient_id']} from {os.path.basename(pdf_file)}")

    print(f"\nDone. {inserted} loaded, {skipped} skipped.")


if __name__ == "__main__":
    if not PDF_DIR:
        sys.exit("DISCHARGE_PDF_DIR is not set. Copy .env.example and set it.")
    process_pdf_directory(PDF_DIR)
