
from recovery_agent import recovery_agent

sample_text = """
SAMPLE HOSPITAL

Recovery instructions:
Follow the individualized recovery instructions
supplied by the treating healthcare team.

Follow-up:
Contact the hospital to confirm the appointment date
and time.

Medication:
Refer to the separate medication list verified
by the treating clinician.
"""

result = recovery_agent.invoke({
    "extracted_text": sample_text,
    "recovery_tasks": [],
    "pending_confirmations": []
})
print("\nRECOVERY TASKS:")
for task in result["recovery_tasks"]:
    print("Task:", task["task"])
    print("Status:", task["status"])
    print()

print("\nPENDING CONFIRMATIONS:")
for item in result["pending_confirmations"]:
    print("-", item)

