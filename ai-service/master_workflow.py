
from typing import TypedDict
from langgraph.graph import StateGraph, END

from summary_agent import summary_agent
from recovery_agent import recovery_agent


class WorkflowState(TypedDict, total=False):
    extracted_text: str
    patient_details: dict
    safety_notes: list
    recovery_tasks: list
    pending_confirmations: list
    status: str
    error: str


# Agent 1: Summary Analysis

def run_summary_agent(state: WorkflowState):

    extracted_text = state.get("extracted_text", "")

    if not isinstance(extracted_text, str) or not extracted_text.strip():
        return {
            "status": "error",
            "error": "No valid discharge summary text provided."
        }

    try:

        result = summary_agent.invoke({
            "extracted_text": extracted_text,
            "patient_details": {},
            "safety_notes": []
        })

        if not isinstance(result, dict):
            raise ValueError("Invalid Summary Agent response.")

        if result.get("error"):
            raise ValueError(result["error"])

        patient_details = result.get("patient_details")
        safety_notes = result.get("safety_notes")

        if not isinstance(patient_details, dict):
            raise ValueError("Invalid patient details response.")

        if not isinstance(safety_notes, list):
            raise ValueError("Invalid safety notes response.")

        required_fields = [
            "patient_name",
            "age",
            "discharge_date"
        ]

        for field in required_fields:

            if not isinstance(patient_details.get(field), str):
                raise ValueError(
                    f"Invalid patient detail field: {field}"
                )

        if not all(isinstance(note, str) for note in safety_notes):
            raise ValueError("Safety notes must contain only strings.")

        return {
            "patient_details": patient_details,
            "safety_notes": safety_notes
        }

    except Exception as error:

        print("Summary Agent workflow error:", repr(error))

        return {
            "status": "error",
            "error": "Summary Agent processing failed."
        }


# Agent 2: Recovery Planning

def run_recovery_agent(state: WorkflowState):

    if state.get("status") == "error":
        return {}

    extracted_text = state.get("extracted_text", "")

    try:

        result = recovery_agent.invoke({
            "extracted_text": extracted_text,
            "recovery_tasks": [],
            "pending_confirmations": []
        })

        if not isinstance(result, dict):
            raise ValueError("Invalid Recovery Agent response.")

        if result.get("error"):
            raise ValueError(result["error"])

        recovery_tasks = result.get("recovery_tasks")
        pending_confirmations = result.get("pending_confirmations")

        if not isinstance(recovery_tasks, list):
            raise ValueError("Invalid recovery tasks response.")

        if not isinstance(pending_confirmations, list):
            raise ValueError("Invalid pending confirmations response.")

        for task in recovery_tasks:

            if not isinstance(task, dict):
                raise ValueError("Invalid recovery task.")

            if not all(
                isinstance(task.get(field), str)
                for field in ["task", "source", "status"]
            ):
                raise ValueError("Invalid recovery task fields.")

            if task["status"] != "requires_verification":
                raise ValueError("Invalid recovery task status.")

        if not all(
            isinstance(item, str)
            for item in pending_confirmations
        ):
            raise ValueError("Pending confirmations must contain strings.")

        return {
            "recovery_tasks": recovery_tasks,
            "pending_confirmations": pending_confirmations
        }

    except Exception as error:

        print("Recovery Agent workflow error:", repr(error))

        return {
            "status": "error",
            "error": "Recovery Agent processing failed."
        }


# Final Result Aggregation

def aggregate_results(state: WorkflowState):

    if state.get("status") == "error":

        return {
            "status": "error",
            "error": state.get("error", "AI workflow failed."),
            "patient_details": state.get("patient_details", {}),
            "safety_notes": state.get("safety_notes", []),
            "recovery_tasks": state.get("recovery_tasks", []),
            "pending_confirmations": state.get(
                "pending_confirmations", []
            )
        }

    return {
        "status": "success",
        "patient_details": state.get("patient_details", {}),
        "safety_notes": state.get("safety_notes", []),
        "recovery_tasks": state.get("recovery_tasks", []),
        "pending_confirmations": state.get(
            "pending_confirmations", []
        )
    }


# Build Master LangGraph

builder = StateGraph(WorkflowState)

builder.add_node(
    "summary_agent",
    run_summary_agent
)

builder.add_node(
    "recovery_agent",
    run_recovery_agent
)

builder.add_node(
    "aggregate_results",
    aggregate_results
)

builder.set_entry_point("summary_agent")

builder.add_edge("summary_agent", "recovery_agent")

builder.add_edge("recovery_agent", "aggregate_results")

builder.add_edge("aggregate_results", END)

master_workflow = builder.compile()
