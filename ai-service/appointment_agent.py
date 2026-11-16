from typing import TypedDict
from langgraph.graph import StateGraph, END


class AppointmentState(TypedDict, total=False):
    document_data: dict
    appointments: list
    appointment_notes: list


def manage_appointments(state: AppointmentState):
    items = (state.get("document_data") or {}).get("appointments", []) or []
    appointments = [{"details": x.get("details", ""), "source": x.get("source", ""), "status": "requires_verification", "calendar_ready": False} for x in items if isinstance(x, dict)]
    notes = [] if appointments else ["No specific follow-up appointment details were extracted. Confirm the appointment with the hospital or treating provider."]
    if appointments:
        notes.append("Appointment details are extracted but need patient or clinic confirmation before calendar scheduling.")
    return {"appointments": appointments, "appointment_notes": notes}


builder = StateGraph(AppointmentState)
builder.add_node("manage_appointments", manage_appointments)
builder.set_entry_point("manage_appointments")
builder.add_edge("manage_appointments", END)
appointment_agent = builder.compile()
