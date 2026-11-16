"""Build reviewable recovery tasks only from validated extracted fields."""
from typing import TypedDict
from langgraph.graph import StateGraph, END
from document_validation import template_confirmation_messages


class RecoveryState(TypedDict, total=False):
    extracted_text: str
    document_data: dict
    recovery_tasks: list
    pending_confirmations: list
    error: str


def create_recovery_plan(state: RecoveryState):
    raw = state.get("extracted_text", "")
    data = state.get("document_data") or {}
    tasks = []
    seen = set()
    for category in ("activity_instructions", "diet_instructions"):
        for item in data.get(category, []) or []:
            if not isinstance(item, dict):
                continue
            details = str(item.get("details", "")).strip()
            source = str(item.get("source", "")).strip()
            if not details or not source or details.casefold() in seen:
                continue
            seen.add(details.casefold())
            tasks.append({"task": details, "source": source, "status": "requires_verification"})
    pending = list(data.get("missing_or_unclear", []) or [])
    pending.extend(template_confirmation_messages(raw))
    pending = list(dict.fromkeys(x.strip() for x in pending if isinstance(x, str) and x.strip()))
    return {"recovery_tasks": tasks, "pending_confirmations": pending}


builder = StateGraph(RecoveryState)
builder.add_node("create_recovery_plan", create_recovery_plan)
builder.set_entry_point("create_recovery_plan")
builder.add_edge("create_recovery_plan", END)
recovery_agent = builder.compile()
