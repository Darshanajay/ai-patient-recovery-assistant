TEMPLATE_TEXT = """
PATIENT DISCHARGE SUMMARY
Patient Name: [Darshan DR]
Age / Sex: [20 / male]
Discharge Date: [07/11/2026]
Primary Diagnosis: [Condition / Procedure]
Medication 1: [Medication 1 – e.g., Amoxicillin 500mg]
Instructions: [1 tablet twice daily after meals for 5 days]
Activity & Rest: [e.g., Light walking allowed; avoid strenuous exercise.]
Wound / Site Care: [e.g., Keep dressing clean and dry.]
Diet & Hydration: [e.g., Soft diet for 48 hours.]
Warning Signs: [e.g., Fever or worsening pain.]
Next Appointment: [12/11/2026 at 60:30 PM]
Department / Doctor: [Specialty / Dr Example]
"""

COMPLETED_TEXT = """
PATIENT DISCHARGE SUMMARY
Hospital: Example Test Hospital
Patient Name
Aarav Samplepatient
Age / Sex
35 / Not specified
Discharge Date
12/11/2026
Primary Diagnosis: Example condition for parser testing only.
Brief Summary: Fictional sample summary for extraction tests only.
Medication Schedule
Medication Name
Dosage
Frequency
Duration
Purpose
TEST-MED-A
TEST-DOSE-A
TEST-FREQUENCY-A
TEST-DURATION-A
TEST-PURPOSE-A
TEST-MED-B
TEST-DOSE-B
TEST-FREQUENCY-B
TEST-DURATION-B
TEST-PURPOSE-B
Activity & Rest: Fictional activity field alpha for parser testing only.
Diet & Hydration: Fictional diet field alpha for parser testing only.
Warning Signs: Fictional warning field alpha for parser testing only.
5. FOLLOW-UP APPOINTMENT
Next Appointment Date & Time: 19/11/2026 at 10:30 AM.
Department / Doctor: Example Department / Dr. Example Clinician.
Location: Example Clinic, Room TEST-12.
6. AUTHORIZATION & ACKNOWLEDGMENT
Attending Physician: Dr. Example Clinician.
"""

INVALID_APPOINTMENT_TEXT = """
PATIENT DISCHARGE SUMMARY
Patient Name: Sample Patient
Age: 40
Discharge Date: 10/11/2026
5. FOLLOW-UP APPOINTMENT
Next Appointment Date & Time: 19/11/2026 at 60:30 PM.
"""
