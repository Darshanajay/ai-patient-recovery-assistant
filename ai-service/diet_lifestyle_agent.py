from typing import TypedDict
from langgraph.graph import StateGraph, END


class DietLifestyleState(TypedDict, total=False):
    document_data: dict
    diet_lifestyle_guidance: dict
    diet_lifestyle_notes: list


def organize_guidance(state: DietLifestyleState):
    data = state.get("document_data") or {}
    diet = data.get("diet_instructions", []) or []
    activity = data.get("activity_instructions", []) or []
    guidance = {
        "diet_instructions": [{**x, "status": "requires_verification"} for x in diet if isinstance(x, dict)],
        "activity_instructions": [{**x, "status": "requires_verification"} for x in activity if isinstance(x, dict)],
    }
    notes = []
    if not guidance["diet_instructions"]:
        notes.append("No specific dietary instruction was extracted. Do not assume dietary restrictions; ask the treating team if clarification is needed.")
    if not guidance["activity_instructions"]:
        notes.append("No specific activity instruction was extracted. Follow the treating team's advice rather than generating an activity plan.")
    return {"diet_lifestyle_guidance": guidance, "diet_lifestyle_notes": notes}


builder = StateGraph(DietLifestyleState)
builder.add_node("organize_guidance", organize_guidance)
builder.set_entry_point("organize_guidance")
builder.add_edge("organize_guidance", END)
diet_lifestyle_agent = builder.compile()
