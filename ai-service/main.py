
from io import BytesIO
from typing import TypedDict

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from langgraph.graph import StateGraph, END

from summary_agent import summary_agent
from master_workflow import master_workflow


app = FastAPI(title="Patient Recovery AI Service")


# CORS Configuration

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Legacy Demo Workflow

class RecoveryState(TypedDict):
    patient_name: str
    discharge_summary: str
    extracted_information: str


def discharge_summary_agent(state: RecoveryState):

    summary = state["discharge_summary"]

    return {
        "extracted_information": (
            "Discharge summary received for processing: " + summary
        )
    }


graph_builder = StateGraph(RecoveryState)

graph_builder.add_node(
    "discharge_agent",
    discharge_summary_agent
)

graph_builder.set_entry_point("discharge_agent")

graph_builder.add_edge("discharge_agent", END)

recovery_graph = graph_builder.compile()


# Health Check

@app.get("/health")
def health_check():

    return {
        "status": "UP",
        "service": "AI Service"
    }


# Legacy Demo Endpoint

@app.post("/process-summary")
def process_summary():

    result = recovery_graph.invoke({
        "patient_name": "Demo Patient",
        "discharge_summary": (
            "Patient discharged. Follow the doctor's instructions."
        ),
        "extracted_information": ""
    })

    return result


# Main PDF Upload and AI Analysis Endpoint

@app.post("/upload-summary")
async def upload_summary(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    pdf_content = await file.read()

    if not pdf_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty"
        )

    if len(pdf_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="PDF must be smaller than 10 MB"
        )

    try:

        reader = PdfReader(BytesIO(pdf_content))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Encrypted PDFs are not supported"
            )

        extracted_text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in PDF"
            )

        # Execute Master LangGraph Workflow

        workflow_result = master_workflow.invoke({
            "extracted_text": extracted_text
        })

        # Validate workflow result

        if not isinstance(workflow_result, dict):
            raise ValueError("Invalid Master Workflow response")

        if workflow_result.get("status") != "success":

            raise HTTPException(
                status_code=500,
                detail=workflow_result.get(
                    "error",
                    "AI workflow processing failed"
                )
            )

        return {
            "status": "success",
            "message": "PDF extracted and analyzed successfully",
            "patient_details": workflow_result.get(
                "patient_details", {}
            ),
            "safety_notes": workflow_result.get(
                "safety_notes", []
            ),
            "recovery_tasks": workflow_result.get(
                "recovery_tasks", []
            ),
            "pending_confirmations": workflow_result.get(
                "pending_confirmations", []
            )
        }

    except HTTPException:
        raise

    except Exception as error:

        print("ERROR DETAILS:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="PDF processing failed"
        )


# Direct Summary Analysis Endpoint

class SummaryRequest(BaseModel):
    extracted_text: str


@app.post("/analyze-summary")
def analyze_discharge_summary(request: SummaryRequest):

    if not request.extracted_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Discharge summary text cannot be empty"
        )

    try:

        result = summary_agent.invoke({
            "extracted_text": request.extracted_text,
            "patient_details": {},
            "safety_notes": []
        })

        if not isinstance(result, dict):
            raise ValueError("Invalid Summary Agent response")

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail="Summary Agent processing failed"
            )

        patient_details = result.get("patient_details")
        safety_notes = result.get("safety_notes")

        if not isinstance(patient_details, dict):
            raise ValueError("Invalid patient details response")

        if not isinstance(safety_notes, list):
            raise ValueError("Invalid safety notes response")

        return {
            "status": "success",
            "patient_details": patient_details,
            "safety_notes": safety_notes
        }

    except HTTPException:
        raise

    except Exception as error:

        print("Summary Analysis ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Summary analysis failed"
        )
