import sys
from unittest.mock import patch

from fixtures import TEMPLATE_TEXT, COMPLETED_TEXT, INVALID_APPOINTMENT_TEXT
from document_validation import normalized_analysis_text, template_confirmation_messages, has_valid_12_hour_times
from summary_agent import analyze_summary
from document_understanding_agent import understand_document
from recovery_agent import create_recovery_plan
from medication_agent import manage_medications
from appointment_agent import manage_appointments
from diet_lifestyle_agent import organize_guidance
from alert_caregiver_agent import coordinate_alerts
from master_workflow import master_workflow


def test_template_content_is_removed_and_confirmed():
    cleaned = normalized_analysis_text(TEMPLATE_TEXT)
    assert "Amoxicillin" not in cleaned
    assert "Light walking" not in cleaned
    assert "60:30 PM" not in cleaned
    messages = template_confirmation_messages(TEMPLATE_TEXT)
    assert "Primary diagnosis is not filled in." in messages
    assert "Medication details are not filled in." in messages
    assert any("example instructions" in x for x in messages)


def test_summary_extracts_completed_header_fields():
    result = analyze_summary({"extracted_text": COMPLETED_TEXT})
    assert result["patient_details"] == {
        "patient_name": "Aarav Samplepatient",
        "age": "35 / Not specified",
        "discharge_date": "12/11/2026",
    }
    assert result["safety_notes"] == []


def test_summary_does_not_extract_bracketed_template_values():
    result = analyze_summary({"extracted_text": TEMPLATE_TEXT})
    assert result["patient_details"]["patient_name"] == "Not found"
    assert result["patient_details"]["age"] == "Not found"
    assert result["patient_details"]["discharge_date"] == "Not found"


def test_complete_document_extracts_all_supported_fields_without_ollama():
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        result = understand_document({"extracted_text": COMPLETED_TEXT})
    data = result["document_data"]
    assert data["diagnosis"] == "Example condition for parser testing only."
    assert len(data["medications"]) == 2
    assert data["medications"][0]["name"] == "TEST-MED-A"
    assert len(data["appointments"]) == 1
    assert len(data["activity_instructions"]) == 1
    assert len(data["diet_instructions"]) == 1
    assert len(data["warning_signs"]) == 1


def test_template_does_not_yield_patient_specific_instructions():
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        result = understand_document({"extracted_text": TEMPLATE_TEXT})
    data = result["document_data"]
    assert data["diagnosis"] == "Not found"
    assert data["medications"] == []
    assert data["appointments"] == []
    assert data["activity_instructions"] == []
    assert data["diet_instructions"] == []
    assert data["warning_signs"] == []


def test_invalid_appointment_time_is_rejected():
    assert not has_valid_12_hour_times("19/11/2026 at 60:30 PM")
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        result = understand_document({"extracted_text": INVALID_APPOINTMENT_TEXT})
    assert result["document_data"]["appointments"] == []


def test_recovery_tasks_are_built_only_from_extracted_activity_and_diet():
    data = {"activity_instructions": [{"details": "Activity text", "source": "Activity source"}],
            "diet_instructions": [{"details": "Diet text", "source": "Diet source"}],
            "warning_signs": [{"details": "Warning", "source": "Warning source"}]}
    result = create_recovery_plan({"extracted_text": "", "document_data": data})
    assert [x["task"] for x in result["recovery_tasks"]] == ["Activity text", "Diet text"]
    assert all(x["status"] == "requires_verification" for x in result["recovery_tasks"])


def test_medication_agent_keeps_fields_and_requires_verification():
    result = manage_medications({"document_data": {"medications": [{"name": "TEST-MED-A", "dosage": "TEST-DOSE-A", "details": "test", "source": "TEST-MED-A"}]}})
    assert result["medication_plan"][0]["name"] == "TEST-MED-A"
    assert result["medication_plan"][0]["reminder_ready"] is False
    assert result["medication_plan"][0]["status"] == "requires_verification"


def test_appointment_agent_never_marks_calendar_ready():
    result = manage_appointments({"document_data": {"appointments": [{"details": "Date/time", "source": "Date/time"}]}})
    assert result["appointments"][0]["calendar_ready"] is False
    assert result["appointments"][0]["status"] == "requires_verification"


def test_warning_signs_are_review_alerts_not_diagnoses():
    result = coordinate_alerts({"document_data": {"warning_signs": [{"details": "Documented warning", "source": "Source"}]}})
    assert result["coordination_alerts"][0]["status"] == "requires_clinician_review"
    assert result["coordination_alerts"][0]["type"] == "documented_warning_instruction"


def test_full_workflow_contract_offline():
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        result = master_workflow.invoke({"extracted_text": COMPLETED_TEXT})
    assert result["status"] == "success"
    assert result["patient_details"]["patient_name"] == "Aarav Samplepatient"
    assert len(result["document_data"]["medications"]) == 2
    assert len(result["medication_plan"]) == 2
    assert len(result["appointments"]) == 1
    assert len(result["recovery_tasks"]) == 2
    assert len(result["coordination_alerts"]) == 1


def test_empty_input_returns_error():
    result = analyze_summary({"extracted_text": "   "})
    assert result.get("error")


def test_medication_table_columns_are_mapped_to_correct_rows():
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        result = understand_document({"extracted_text": COMPLETED_TEXT})
    first = result["document_data"]["medications"][0]
    assert first["name"] == "TEST-MED-A"
    assert first["dosage"] == "TEST-DOSE-A"
    assert first["frequency"] == "TEST-FREQUENCY-A"
    assert first["duration"] == "TEST-DURATION-A"
    assert first["purpose"] == "TEST-PURPOSE-A"


def test_upload_summary_api_with_synthetic_pdf():
    from fastapi.testclient import TestClient
    from main import app
    from pathlib import Path
    pdf_path = Path(__file__).with_name("synthetic_discharge_summary_test.pdf")
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        response = TestClient(app).post(
            "/upload-summary",
            files={"file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["patient_details"]["patient_name"] == "Aarav Samplepatient"
    assert len(body["document_data"]["medications"]) == 2
    assert len(body["appointments"]) == 1


def test_upload_summary_rejects_non_pdf():
    from fastapi.testclient import TestClient
    from main import app
    response = TestClient(app).post(
        "/upload-summary",
        files={"file": ("not-a-pdf.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
