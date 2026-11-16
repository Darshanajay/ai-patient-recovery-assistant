from typing import TypedDict
from langgraph.graph import StateGraph, END


class AlertState(TypedDict, total=False):
    document_data: dict
    pending_confirmations: list
    safety_notes: list
    coordination_alerts: list


def coordinate_alerts(state: AlertState):
    data = state.get("document_data") or {}
    confirmations = list(state.get("pending_confirmations") or [])
    alerts = []
    for warning in data.get("warning_signs", []) or []:
        if isinstance(warning, dict):
            alerts.append({"type": "documented_warning_instruction", "details": warning.get("details", ""), "source": warning.get("source", ""), "status": "requires_clinician_review"})
    confirmations.extend(data.get("missing_or_unclear", []) or [])
    unique = list(dict.fromkeys(x.strip() for x in confirmations if isinstance(x, str) and x.strip()))
    return {"pending_confirmations": unique, "safety_notes": list(state.get("safety_notes") or []), "coordination_alerts": alerts}


builder = StateGraph(AlertState)
builder.add_node("coordinate_alerts", coordinate_alerts)
builder.set_entry_point("coordinate_alerts")
builder.add_edge("coordinate_alerts", END)
alert_caregiver_agent = builder.compile()
