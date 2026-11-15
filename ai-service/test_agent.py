
from summary_agent import summary_agent

sample_text = """
SAMPLE HOSPITAL
Patient name: Alex Demo
Age: 45 years
Discharge date: 14 November 2026

Medication names, doses must be verified.
The application must not diagnose.
"""

result = summary_agent.invoke({
    "extracted_text": sample_text,
    "patient_details": {},
    "safety_notes": []
})

print("\nPATIENT DETAILS:")
print(result["patient_details"])

print("\nSAFETY NOTES:")
for note in result["safety_notes"]:
    print("-", note)
