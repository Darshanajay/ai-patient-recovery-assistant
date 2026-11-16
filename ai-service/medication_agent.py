from typing import TypedDict
from langgraph.graph import StateGraph, END


class MedicationState(TypedDict, total=False):
    document_data: dict
    medication_plan: list
    medication_notes: list


def manage_medications(state: MedicationState):
    data = state.get("document_data") or {}
    medications = data.get("medications", []) or []
    plan = []
    for item in medications:
        if not isinstance(item, dict):
            continue
        plan.append({
            **{k: item.get(k, "") for k in ("name", "dosage", "frequency", "duration", "purpose")},
            "details": item.get("details", ""),
            "source": item.get("source", ""),
            "status": "requires_verification",
            "reminder_ready": False,
        })
    notes = [] if plan else ["No complete medication instructions were extracted. Confirm the current medication list with the treating healthcare team."]
    if plan:
        notes.append("Medication details are extracted from the discharge document but must be confirmed before reminders are activated.")
    return {"medication_plan": plan, "medication_notes": notes}


builder = StateGraph(MedicationState)
builder.add_node("manage_medications", manage_medications)
builder.set_entry_point("manage_medications")
builder.add_edge("manage_medications", END)
medication_agent = builder.compile()
