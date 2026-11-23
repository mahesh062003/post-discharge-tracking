"""
Generates synthetic discharge summaries in the hospital's report layout.

The real summaries this pipeline was built against contain identifiable patient
information and are not distributable. These synthetic records reproduce the
layout exactly, so the extraction pipeline can be run and verified without
any real patient data.
"""

import os

import fitz

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

RECORDS = [
    {
        "patient_id": "SRH10492", "ip_no": "224517", "patient_name": "ANANYA RAGHAVAN",
        "gender_age": "FEMALE / 54", "mobile_no": "9876543210",
        "ward": "CARDIAC CARE", "bed": "C12", "doa": "04-11-2024", "dod": "11-11-2024",
        "address": "14 Nehru Street, Coimbatore, Tamil Nadu 641001",
        "reason": "Exertional chest pain with reduced effort tolerance over three weeks.",
        "doctor": "DR.VIKRAM SUNDARAM DNB",
    },
    {
        "patient_id": "SRH10518", "ip_no": "224603", "patient_name": "MOHAMMED IRFAN",
        "gender_age": "MALE / 61", "mobile_no": "9123456780",
        "ward": "GENERAL MEDICINE", "bed": "G07", "doa": "09-11-2024", "dod": "15-11-2024",
        "address": "88 Trichy Road, Singanallur, Coimbatore 641005",
        "reason": "Uncontrolled type 2 diabetes mellitus with recurrent hypoglycaemia.",
        "doctor": "DR.LAKSHMI NARAYANAN DM",
    },
    {
        "patient_id": "SRH10533", "ip_no": "224688", "patient_name": "PRIYA DHARSHINI",
        "gender_age": "FEMALE / 37", "mobile_no": "9988776655",
        "ward": "POST OP", "bed": "P03", "doa": "12-11-2024", "dod": "18-11-2024",
        "address": "5/2 Lake View Layout, Saibaba Colony, Coimbatore 641011",
        "reason": "Elective laparoscopic cholecystectomy for symptomatic gallstones.",
        "doctor": "DR.ARUN PRASAD FESC",
    },
]

TEMPLATE = """SRI RAMAKRISHNA HOSPITAL
DISCHARGE SUMMARY

PATIENT ID    {patient_id}
IP NO    {ip_no}
PATIENT NAME    {patient_name}
GENDER / AGE    {gender_age}
MOBILE NO    {mobile_no}
WARD    {ward}    BED    {bed}
D.O.A    {doa}
D.O.D    {dod}
PATIENT ADDRESS    {address}

REASON FOR ADMISSION : {reason}

PAST HISTORY
Nil contributory.

TREATMENT GIVEN
Managed as per unit protocol. Stable at discharge.

CONSULTANT
{doctor}
"""


def main():
    for record in RECORDS:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (56, 72), TEMPLATE.format(**record), fontsize=9, fontname="helv"
        )
        out_path = os.path.join(OUT_DIR, f"discharge_{record['patient_id']}.pdf")
        doc.save(out_path)
        doc.close()
        print(f"Wrote {os.path.basename(out_path)}")


if __name__ == "__main__":
    main()
