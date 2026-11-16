"""Extract patient header fields without generating clinical advice."""
from typing import TypedDict
import re
from langgraph.graph import StateGraph, END
from document_validation import normalized_analysis_text, clean_string, is_blank_or_placeholder


class SummaryState(TypedDict, total=False):
    extracted_text: str
    patient_details: dict
    safety_notes: list
    error: str


def _field(text: str, labels: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pattern = re.compile(rf"^(?:{labels})\s*:?\s*(.*)$", re.IGNORECASE)
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        value = clean_string(match.group(1))
        if not value and i + 1 < len(lines):
            candidate = clean_string(lines[i + 1])
            if not re.match(r"^(?:patient\s*name|age(?:\s*/\s*sex)?|discharge\s*date|admission\s*date|primary\s*diagnosis|attending\s*physician)\s*:?$", candidate, re.IGNORECASE):
                value = candidate
        if value and not is_blank_or_placeholder(value):
            return value
    return "Not found"


def analyze_summary(state: SummaryState):
    raw = state.get("extracted_text", "")
    if not isinstance(raw, str) or not raw.strip():
        return {"error": "No valid discharge summary text provided."}
    text = normalized_analysis_text(raw)
    details = {
        "patient_name": _field(text, r"patient\s*name"),
        "age": _field(text, r"age(?:\s*/\s*sex)?|age\s+sex"),
        "discharge_date": _field(text, r"discharge\s*date"),
    }
    # Safety notes are not inferred here. Documented warning-sign fields are
    # handled separately and remain marked for clinician review.
    return {"patient_details": details, "safety_notes": []}


builder = StateGraph(SummaryState)
builder.add_node("analyze_summary", analyze_summary)
builder.set_entry_point("analyze_summary")
builder.add_edge("analyze_summary", END)
summary_agent = builder.compile()
