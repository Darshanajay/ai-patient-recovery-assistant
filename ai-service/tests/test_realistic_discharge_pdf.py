from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader

from document_understanding_agent import understand_document
from recovery_agent import create_recovery_plan
from medication_agent import manage_medications
from appointment_agent import manage_appointments
from diet_lifestyle_agent import organize_guidance
from alert_caregiver_agent import coordinate_alerts


def _realistic_pdf_text():
    pdf_path = Path(__file__).with_name("realistic_discharge_summary_test.pdf")
    return "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)


def test_realistic_pdf_extracts_all_expected_sections_without_ollama():
    text = _realistic_pdf_text()
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        result = understand_document({"extracted_text": text})

    data = result["document_data"]
    assert data["diagnosis"].startswith("Acute gastritis")
    assert len(data["medications"]) == 2
    assert data["medications"][0]["name"] == "Paracetamol (test entry)"
    assert data["medications"][0]["dosage"] == "500 mg"
    assert data["medications"][1]["name"] == "Pantoprazole (test entry)"
    assert len(data["appointments"]) == 1
    assert "21 November 2026" in data["appointments"][0]["details"]
    assert "9. DOCUMENT AUTHORIZATION" not in data["appointments"][0]["details"]
    assert len(data["diet_instructions"]) == 1
    assert len(data["activity_instructions"]) == 1
    assert len(data["warning_signs"]) == 1


def test_realistic_pdf_generates_reviewable_downstream_outputs():
    text = _realistic_pdf_text()
    with patch("document_understanding_agent.ollama.chat", side_effect=RuntimeError("offline")):
        document_result = understand_document({"extracted_text": text})
    data = document_result["document_data"]

    recovery = create_recovery_plan({"extracted_text": text, "document_data": data})
    medications = manage_medications({"document_data": data})
    appointments = manage_appointments({"document_data": data})
    lifestyle = organize_guidance({"document_data": data})
    alerts = coordinate_alerts({"document_data": data})

    assert len(recovery["recovery_tasks"]) == 2
    assert len(medications["medication_plan"]) == 2
    assert all(not item["reminder_ready"] for item in medications["medication_plan"])
    assert len(appointments["appointments"]) == 1
    assert appointments["appointments"][0]["calendar_ready"] is False
    assert len(lifestyle["diet_lifestyle_guidance"]["diet_instructions"]) == 1
    assert len(lifestyle["diet_lifestyle_guidance"]["activity_instructions"]) == 1
    assert len(alerts["coordination_alerts"]) == 1
    assert alerts["coordination_alerts"][0]["status"] == "requires_clinician_review"
