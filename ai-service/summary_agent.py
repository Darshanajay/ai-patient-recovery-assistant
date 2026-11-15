
import json
import ollama

from typing import TypedDict
from langgraph.graph import StateGraph, END


class SummaryState(TypedDict):
    extracted_text: str
    patient_details: dict
    safety_notes: list
    error: str


def analyze_summary(state: SummaryState):

    extracted_text = state.get("extracted_text", "")

    if not isinstance(extracted_text, str) or not extracted_text.strip():
        return {
            "error": "No valid discharge summary text provided."
        }

    prompt = f"""
You are a discharge-summary information extraction assistant.

Analyze this fictional or test discharge summary.

Extract ONLY information explicitly available in the document.

Return valid JSON:

{{
    "patient_name": "Name",
    "age": "Age",
    "discharge_date": "Date",
    "safety_notes": []
}}

STRICT RULES:

- Never invent patient information.
- Missing information must be "Not found".
- Preserve age and date as written.
- Do not calculate or assume missing values.
- Do not generate medical advice.
- Do not suggest medicines, doses or treatments.
- Add safety notes only when explicitly supported by the document.
- Mention clinician verification when medication instructions
  are incomplete or explicitly require verification.
- Do not repeat safety notes.
- Keep safety_notes as plain text strings.
- Return valid JSON only.

DOCUMENT:

{extracted_text}
"""

    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            format="json",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = json.loads(
            response["message"]["content"]
        )

        if not isinstance(result, dict):
            raise ValueError("AI response must be a JSON object.")

        # Validate patient details.
        patient_details = {}

        for field in ["patient_name", "age", "discharge_date"]:

            value = result.get(field, "Not found")

            if not isinstance(value, str):
                value = "Not found"

            value = value.strip()

            if value.lower() in ["", "null", "none", "unknown"]:
                value = "Not found"

            patient_details[field] = value

        # Validate and clean safety notes.
        safety_notes = result.get("safety_notes", [])

        if not isinstance(safety_notes, list):
            raise ValueError("Safety notes must be a list.")

        clean_notes = []
        seen = set()

        for note in safety_notes:

            if not isinstance(note, str):
                continue

            note = note.strip()

            if not note or note.lower() in seen:
                continue

            seen.add(note.lower())
            clean_notes.append(note)

        print("\n========== RAW SUMMARY AI RESPONSE ==========")
        print(json.dumps(result, indent=4))
        print("=============================================")

        return {
            "patient_details": patient_details,
            "safety_notes": clean_notes
        }

    except Exception as error:

        print("Summary AI response error:", repr(error))

        return {
            "error": "Summary Agent processing failed."
        }


# Build LangGraph workflow.

graph = StateGraph(SummaryState)

graph.add_node("analyze_summary", analyze_summary)

graph.set_entry_point("analyze_summary")

graph.add_edge("analyze_summary", END)

summary_agent = graph.compile()
