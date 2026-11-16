from typing import TypedDict
from langgraph.graph import StateGraph, END
from summary_agent import summary_agent
from document_understanding_agent import document_understanding_agent
from recovery_agent import recovery_agent
from medication_agent import medication_agent
from appointment_agent import appointment_agent
from diet_lifestyle_agent import diet_lifestyle_agent
from alert_caregiver_agent import alert_caregiver_agent


class WorkflowState(TypedDict, total=False):
    extracted_text: str
    patient_details: dict
    safety_notes: list
    document_data: dict
    recovery_tasks: list
    pending_confirmations: list
    medication_plan: list
    medication_notes: list
    appointments: list
    appointment_notes: list
    diet_lifestyle_guidance: dict
    diet_lifestyle_notes: list
    coordination_alerts: list
    status: str
    error: str


def _invoke(agent, payload):
    result = agent.invoke(payload)
    if not isinstance(result, dict) or result.get("error"):
        raise ValueError("Agent returned an invalid result")
    return result


def run_summary(state):
    try:
        return _invoke(summary_agent, {"extracted_text": state.get("extracted_text", "")})
    except Exception as exc:
        print("Summary agent failed:", repr(exc))
        return {"status": "error", "error": "Summary Agent processing failed."}


def run_document(state):
    if state.get("status") == "error": return {}
    try:
        return _invoke(document_understanding_agent, {"extracted_text": state.get("extracted_text", "")})
    except Exception as exc:
        print("Document agent failed:", repr(exc))
        return {"status": "error", "error": "Document Understanding Agent processing failed."}


def run_recovery(state):
    if state.get("status") == "error": return {}
    try:
        return _invoke(recovery_agent, {"extracted_text": state.get("extracted_text", ""), "document_data": state.get("document_data", {})})
    except Exception as exc:
        print("Recovery agent failed:", repr(exc))
        return {"status": "error", "error": "Recovery Agent processing failed."}


def run_data_agent(agent, state, label):
    if state.get("status") == "error": return {}
    try:
        return _invoke(agent, {"document_data": state.get("document_data", {})})
    except Exception as exc:
        print(label, "failed:", repr(exc))
        return {"status": "error", "error": f"{label} processing failed."}


def run_alerts(state):
    if state.get("status") == "error": return {}
    try:
        return _invoke(alert_caregiver_agent, {"document_data": state.get("document_data", {}), "pending_confirmations": state.get("pending_confirmations", []), "safety_notes": state.get("safety_notes", [])})
    except Exception as exc:
        print("Alert agent failed:", repr(exc))
        return {"status": "error", "error": "Alert & Caregiver Coordination Agent processing failed."}


def aggregate(state):
    fields = ("patient_details", "safety_notes", "document_data", "recovery_tasks", "pending_confirmations", "medication_plan", "medication_notes", "appointments", "appointment_notes", "diet_lifestyle_guidance", "diet_lifestyle_notes", "coordination_alerts")
    if state.get("status") == "error":
        return {"status": "error", "error": state.get("error", "AI workflow failed."), **{k: state.get(k, {}) if k in ("patient_details", "document_data", "diet_lifestyle_guidance") else state.get(k, []) for k in fields}}
    return {"status": "success", **{k: state.get(k, {}) if k in ("patient_details", "document_data", "diet_lifestyle_guidance") else state.get(k, []) for k in fields}}


builder = StateGraph(WorkflowState)
for name, fn in (("summary", run_summary), ("document", run_document), ("recovery", run_recovery), ("medication", lambda s: run_data_agent(medication_agent, s, "Medication Agent")), ("appointment", lambda s: run_data_agent(appointment_agent, s, "Appointment Agent")), ("diet_lifestyle", lambda s: run_data_agent(diet_lifestyle_agent, s, "Diet & Lifestyle Agent")), ("alerts", run_alerts), ("aggregate", aggregate)):
    builder.add_node(name, fn)
builder.set_entry_point("summary")
for a, b in (("summary", "document"), ("document", "recovery"), ("recovery", "medication"), ("medication", "appointment"), ("appointment", "diet_lifestyle"), ("diet_lifestyle", "alerts"), ("alerts", "aggregate")):
    builder.add_edge(a, b)
builder.add_edge("aggregate", END)
master_workflow = builder.compile()
