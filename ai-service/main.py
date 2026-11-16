from io import BytesIO
from typing import TypedDict
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from langgraph.graph import StateGraph, END
from summary_agent import summary_agent
from master_workflow import master_workflow

app = FastAPI(title="Patient Recovery AI Service")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health_check():
    return {"status": "UP", "service": "AI Service"}


class RecoveryState(TypedDict):
    patient_name: str
    discharge_summary: str
    extracted_information: str


def discharge_summary_agent(state: RecoveryState):
    return {"extracted_information": "Discharge summary received for processing: " + state["discharge_summary"]}


graph_builder = StateGraph(RecoveryState)
graph_builder.add_node("discharge_agent", discharge_summary_agent)
graph_builder.set_entry_point("discharge_agent")
graph_builder.add_edge("discharge_agent", END)
recovery_graph = graph_builder.compile()


@app.post("/process-summary")
def process_summary():
    return recovery_graph.invoke({
        "patient_name": "Demo Patient",
        "discharge_summary": "Patient discharged. Follow the doctor's instructions.",
        "extracted_information": "",
    })


@app.post("/upload-summary")
async def upload_summary(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF must be smaller than 10 MB")
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise HTTPException(status_code=400, detail="Encrypted PDFs are not supported")
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in PDF")
        result = master_workflow.invoke({"extracted_text": extracted_text})
        if not isinstance(result, dict) or result.get("status") != "success":
            raise HTTPException(status_code=500, detail=(result or {}).get("error", "AI workflow processing failed"))
        return {"status": "success", "message": "PDF extracted and analyzed successfully", **{key: result.get(key, {} if key in ("patient_details", "document_data", "diet_lifestyle_guidance") else []) for key in ("patient_details", "safety_notes", "recovery_tasks", "pending_confirmations", "document_data", "medication_plan", "medication_notes", "appointments", "appointment_notes", "diet_lifestyle_guidance", "diet_lifestyle_notes", "coordination_alerts")}}
    except HTTPException:
        raise
    except Exception as exc:
        print("PDF processing error:", repr(exc))
        raise HTTPException(status_code=500, detail="PDF processing failed")


class SummaryRequest(BaseModel):
    extracted_text: str


@app.post("/analyze-summary")
def analyze_discharge_summary(request: SummaryRequest):
    if not request.extracted_text.strip():
        raise HTTPException(status_code=400, detail="Discharge summary text cannot be empty")
    result = summary_agent.invoke({"extracted_text": request.extracted_text})
    if result.get("error"):
        raise HTTPException(status_code=500, detail="Summary Agent processing failed")
    return {"status": "success", "patient_details": result.get("patient_details", {}), "safety_notes": result.get("safety_notes", [])}
