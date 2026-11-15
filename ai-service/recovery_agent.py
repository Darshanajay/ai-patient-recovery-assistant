
import json
import ollama

from typing import TypedDict
from langgraph.graph import StateGraph, END


class RecoveryState(TypedDict, total=False):
    extracted_text: str
    recovery_tasks: list
    pending_confirmations: list
    error: str


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def clean_pending_confirmations(confirmations):

    cleaned = []
    seen = set()

    if not isinstance(confirmations, list):
        return cleaned

    for item in confirmations:

        if isinstance(item, dict):
            item = (
                item.get("confirmation")
                or item.get("question")
                or item.get("item")
                or item.get("description")
                or item.get("task")
                or ""
            )

        if not isinstance(item, str):
            continue

        item = " ".join(item.split()).strip()

        if not item:
            continue

        key = item.lower()

        if key not in seen:
            seen.add(key)
            cleaned.append(item)

    return cleaned


def contains_incomplete_reference(text: str):

    text = normalize_text(text)

    incomplete_phrases = [
        "plan is missing",
        "plan is unavailable",
        "plan is not available",
        "plan is not included",
        "plan is maintained separately",
        "plan is provided separately",
        "detailed plan is missing",
        "instructions are missing",
        "instructions are not provided",
        "instructions are not included",
        "instructions are unavailable",
        "not reproduced here",
        "must be confirmed",
        "request the complete written instructions",
        "obtain the complete written instructions",
        "neither document is attached",
        "not attached to this sample",
    ]

    return any(
        phrase in text
        for phrase in incomplete_phrases
    )


def validate_recovery_tasks(tasks, extracted_text):

    validated_tasks = []
    document = normalize_text(extracted_text)
    seen = set()

    if not isinstance(tasks, list):
        return validated_tasks

    generic_phrases = [
        "follow the care plan",
        "use the written recovery plan",
        "follow recovery instructions",
        "continue recovery according to the care plan",
    ]

    for item in tasks:

        if not isinstance(item, dict):
            continue

        task = item.get("task", "")
        source = item.get("source", "")

        if not isinstance(task, str):
            continue

        if not isinstance(source, str):
            continue

        task = " ".join(task.split()).strip()
        source = " ".join(source.split()).strip()

        if not task or not source:
            continue

        normalized_source = normalize_text(source)
        normalized_task = normalize_text(task)

        # Supporting source must exist in the document.
        if normalized_source not in document:
            continue

        # Reject incomplete references.
        if contains_incomplete_reference(source):
            continue

        # Reject generic instructions.
        if any(
            phrase in normalized_task
            for phrase in generic_phrases
        ):
            continue

        # Require sufficient supporting text.
        if len(normalized_source.split()) < 10:
            continue

        # Remove duplicate tasks.
        if normalized_task in seen:
            continue

        seen.add(normalized_task)

        validated_tasks.append({
            "task": task,
            "source": source,
            "status": "requires_verification"
        })

    return validated_tasks


def detect_missing_medication_information(extracted_text):

    text = normalize_text(extracted_text)

    missing_medication_phrases = [
        "medication information is incomplete",
        "medication list is not included",
        "medication list is not attached",
        "medication list is missing",
        "medication details are missing",
        "medication details are not provided",
        "medication instructions are not provided",
        "no medication names",
        "medication names, doses",
        "separate medication list",
        "separate medication reconciliation sheet",
        "medication reconciliation sheet is not included",
        "medication reconciliation sheet is not attached",
        "medication reconciliation sheet is referenced",
        "medication record needs confirmation",
        "medication record should be verified",
        "final medication reconciliation record",
        "verify the final medication reconciliation record",
    ]

    return any(
        phrase in text
        for phrase in missing_medication_phrases
    )


def detect_missing_recovery_plan(extracted_text):

    text = normalize_text(extracted_text)

    missing_plan_phrases = [
        "recovery plan is missing",
        "recovery plan is unavailable",
        "recovery plan is not available",
        "recovery plan is not included",
        "recovery plan is provided separately",
        "recovery plan is maintained separately",
        "written recovery plan",
        "complete written recovery plan",
        "obtain the written recovery plan",
        "obtain the complete written recovery plan",
        "written plan must be confirmed",
        "detailed recovery plan is missing",
        "recovery instructions are not included",
        "recovery instructions are unavailable",
    ]

    return any(
        phrase in text
        for phrase in missing_plan_phrases
    )


def create_recovery_plan(state: RecoveryState):

    extracted_text = state.get("extracted_text", "")

    if not isinstance(extracted_text, str) or not extracted_text.strip():

        return {
            "error": "No valid discharge summary text provided."
        }

    prompt = f"""
You are an information extraction agent for a student software project.

Analyze this fictional discharge summary:

{extracted_text}

YOUR TASK:

Identify clearly documented recovery instructions and
information that requires confirmation.

STRICT RULES:

1. Extract only clear and specific instructions explicitly
   documented in the discharge summary.

2. Do not convert general statements into actionable tasks.

3. If a recovery plan is missing, incomplete, unavailable,
   or maintained separately, do not create a recovery task
   from that reference.

4. Put missing or incomplete information into pending_confirmations.

5. If medication information is missing, request confirmation
   of the clinician-authorized medication list.

6. If appointment details are missing, request confirmation
   of the appointment details.

7. Never invent medication names, doses, treatments,
   activities, dietary instructions, or medical advice.

8. Every recovery task must contain supporting source text.

9. Every extracted task must have status:
   "requires_verification".

10. Never mark tasks as medically verified or approved.

11. If no clear recovery task exists, return an empty
    recovery_tasks array.

12. Return pending confirmations as plain text strings,
    not dictionaries.

Return valid JSON only:

{{
    "recovery_tasks": [
        {{
            "task": "Explicit documented instruction",
            "source": "Supporting text from the document",
            "status": "requires_verification"
        }}
    ],
    "pending_confirmations": [
        "Information requiring confirmation"
    ]
}}
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

        raw_response = response["message"]["content"]

        result = json.loads(raw_response)

        if not isinstance(result, dict):
            raise ValueError("Invalid AI response")

        if not isinstance(result.get("recovery_tasks", []), list):
            raise ValueError("Recovery tasks must be a list.")

        if not isinstance(result.get("pending_confirmations", []), list):
            raise ValueError("Pending confirmations must be a list.")

    except Exception as error:

        print("Recovery AI response error:", repr(error))

        return {
            "error": "Recovery Agent processing failed."
        }

    print("\n========== RAW RECOVERY AI RESPONSE ==========")
    print(json.dumps(result, indent=4))
    print("==============================================")

    # Validate recovery tasks.
    recovery_tasks = validate_recovery_tasks(
        result.get("recovery_tasks", []),
        extracted_text
    )

    # Clean pending confirmations.
    pending_confirmations = clean_pending_confirmations(
        result.get("pending_confirmations", [])
    )

    # Add medication confirmation when explicitly missing.
    if detect_missing_medication_information(extracted_text):

        pending_confirmations.append(
            "Obtain the clinician-authorized medication list."
        )

    # Add written recovery plan confirmation when explicitly missing.
    if detect_missing_recovery_plan(extracted_text):

        pending_confirmations.append(
            "Obtain the complete written recovery plan from the treating healthcare team."
        )

    # Remove duplicate confirmations.
    pending_confirmations = clean_pending_confirmations(
        pending_confirmations
    )

    return {
        "recovery_tasks": recovery_tasks,
        "pending_confirmations": pending_confirmations
    }


# Build LangGraph workflow.

builder = StateGraph(RecoveryState)

builder.add_node(
    "create_recovery_plan",
    create_recovery_plan
)

builder.set_entry_point("create_recovery_plan")

builder.add_edge(
    "create_recovery_plan",
    END
)

recovery_agent = builder.compile()
