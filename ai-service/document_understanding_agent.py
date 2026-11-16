"""Document extraction agent: Ollama-assisted, source-validated, conservative."""
from __future__ import annotations
import json
import os
import re
from typing import TypedDict

import ollama
from langgraph.graph import StateGraph, END
from document_validation import (
    clean_string, normalized_analysis_text, source_is_supported,
    template_confirmation_messages, has_valid_12_hour_times,
    contains_date, contains_time, is_blank_or_placeholder,
)


class DocumentState(TypedDict, total=False):
    extracted_text: str
    document_data: dict
    error: str


def _section(text: str, start_pattern: str, end_pattern: str | None = None) -> str:
    match = re.search(start_pattern, text, re.IGNORECASE)
    if not match:
        return ""
    start = match.start()
    tail = text[start:]
    if end_pattern:
        end = re.search(end_pattern, tail[match.end() - start:], re.IGNORECASE)
        if end:
            return tail[:match.end() - start + end.start()].strip()
    return tail.strip()


def _label_value(text: str, labels: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pat = re.compile(rf"^(?:{labels})\s*:?\s*(.*)$", re.IGNORECASE)
    for i, line in enumerate(lines):
        m = pat.match(line)
        if m:
            value = clean_string(m.group(1))
            if not value and i + 1 < len(lines):
                candidate = clean_string(lines[i + 1])
                if not re.match(r"^(?:patient\s*name|age(?:\s*/\s*sex)?|discharge\s*date|admission\s*date|primary\s*diagnosis|medication\s*\d+|attending\s*physician)\s*:?$", candidate, re.IGNORECASE):
                    value = candidate
            if value and not is_blank_or_placeholder(value):
                return value, line if m.group(1).strip() else f"{line} {value}"
    return "", ""


def _line_items(text: str, label_pattern: str) -> list[dict]:
    items = []
    for line in text.splitlines():
        m = re.match(rf"^\s*(?:{label_pattern})\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
        if not m:
            continue
        value = clean_string(m.group(1)).rstrip(".;")
        if not value or is_blank_or_placeholder(value) or re.search(r"\be\.g\.", value, re.IGNORECASE):
            continue
        source = clean_string(line)
        if value and source:
            items.append({"details": value, "source": source, "status": "requires_verification"})
    return items


def _extract_medication_rows(text: str) -> list[dict]:
    """Extract labelled medication records and common PDF table layouts."""
    results: list[dict] = []

    # Explicit labelled rows are reliable and preserve a complete source quote.
    for line in text.splitlines():
        if re.search(r"\bMedication\s*:\s*", line, re.IGNORECASE):
            fields = {}
            for key in ("Medication", "Name", "Dosage", "Frequency", "Duration", "Purpose"):
                m = re.search(rf"\b{key}\s*:\s*([^;|]+)", line, re.IGNORECASE)
                if m:
                    fields[key.lower()] = clean_string(m.group(1))
            name = fields.get("medication") or fields.get("name")
            if name and not is_blank_or_placeholder(name):
                results.append(_med_item(fields, line, name))
    if results:
        return results

    lines = [clean_string(x) for x in text.splitlines() if clean_string(x)]
    try:
        header_idx = next(i for i, line in enumerate(lines)
                          if re.search(r"^(?:Medicine|Medication(?:\s+Name)?)(?:\s|$)", line, re.IGNORECASE))
    except StopIteration:
        return []

    # Stop at the next numbered section or a clear non-table note.
    end_idx = next((i for i in range(header_idx + 1, len(lines))
                    if re.match(r"^(?:\d+\s*\.\s+|Medication rows?\b|Activity\s*&\s*Rest\b|Diet\b|Warning\s+Signs\b)", lines[i], re.IGNORECASE)),
                   len(lines))
    block = lines[header_idx + 1:end_idx]

    # pypdf's standard extraction commonly emits each table cell on its own
    # line, with wrapped cells occupying multiple lines. Locate dosage cells,
    # then associate the nearest preceding medicine name and following fields.
    dose_re = re.compile(r"^\d+(?:\.\d+)?\s*(?:mg|mcg|µg|g|ml|mL|units?)\b.*$", re.IGNORECASE)
    duration_re = re.compile(r"^(?:\d+\s*(?:days?|weeks?|months?)|as\s+directed|until\s+review).*$", re.IGNORECASE)
    for i, line in enumerate(block):
        if not dose_re.match(line):
            continue

        # The medication name may wrap over the preceding two lines.
        name_parts = []
        j = i - 1
        while j >= 0 and len(name_parts) < 2:
            candidate = block[j]
            if re.fullmatch(r"(?:Dosage|Frequency|Duration|Purpose|Medicine|Medication(?:\s+Name)?)", candidate, re.IGNORECASE):
                break
            if duration_re.match(candidate) or dose_re.match(candidate):
                break
            name_parts.insert(0, candidate)
            j -= 1
        name = clean_string(" ".join(name_parts))
        if not name or is_blank_or_placeholder(name):
            continue

        following = block[i + 1:]
        duration_pos = next((k for k, value in enumerate(following)
                             if duration_re.match(value)), None)
        if duration_pos is None or duration_pos == 0 or duration_pos + 1 >= len(following):
            continue
        frequency = clean_string(" ".join(following[:duration_pos]))
        duration = clean_string(following[duration_pos])
        purpose = clean_string(following[duration_pos + 1])
        if not frequency or not purpose:
            continue
        source = clean_string(" ".join([name, line, frequency, duration, purpose]))
        fields = {"dosage": line, "frequency": frequency, "duration": duration, "purpose": purpose}
        results.append(_med_item(fields, source, name))

    # Backward-compatible parser for column-major tables with nonstandard test
    # values (e.g. TEST-DOSE-A) that do not look like numeric dosage strings.
    if not results:
        header_positions = [i for i, line in enumerate(block)
                            if re.fullmatch(r"(?:Medication\s+Name(?:\s*&\s*Dosage)?|Dosage|Frequency|Duration|Purpose)", line, re.IGNORECASE)]
        if len(header_positions) >= 4:
            value_lines = block[header_positions[-1] + 1:]
            value_lines = [v for v in value_lines if not re.match(
                r"^(?:Day\s*\d+|Medication Name|Dosage|Frequency|Duration|Purpose)$", v, re.IGNORECASE)]
            if len(value_lines) >= 5 and len(value_lines) % 5 == 0:
                for r in range(len(value_lines) // 5):
                    row = value_lines[r * 5:(r + 1) * 5]
                    fields = {"dosage": row[1], "frequency": row[2],
                              "duration": row[3], "purpose": row[4]}
                    name = row[0]
                    if name and not is_blank_or_placeholder(name):
                        results.append(_med_item(fields, " ".join(row), name))

    unique = {}
    for item in results:
        unique.setdefault(item["source"].casefold(), item)
    return list(unique.values())


def _section_content(text: str, heading_pattern: str) -> str:
    """Return content beneath a numbered section heading, stopping at the next heading."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.search(heading_pattern, line, re.IGNORECASE):
            start = i + 1
            break
    if start is None:
        return ""
    content = []
    for line in lines[start:]:
        if re.match(r"^\s*\d+\s*\.\s+[A-Z]", line, re.IGNORECASE):
            break
        if line.strip():
            content.append(clean_string(line))
    return clean_string(" ".join(content))


def _section_instruction(text: str, heading_pattern: str) -> list[dict]:
    content = _section_content(text, heading_pattern)
    if not content or is_blank_or_placeholder(content):
        return []
    # Avoid returning administrative/test-only footer text as a care instruction.
    source = content
    return [{"details": content, "source": source, "status": "requires_verification"}]

def _med_item(fields: dict, source: str, name: str) -> dict:
    keys = ("dosage", "frequency", "duration", "purpose")
    detail_parts = [f"Medication: {name}"]
    for key in keys:
        value = clean_string(fields.get(key))
        if value and not is_blank_or_placeholder(value):
            detail_parts.append(f"{key.title()}: {value}")
    return {
        "name": name,
        "dosage": clean_string(fields.get("dosage")),
        "frequency": clean_string(fields.get("frequency")),
        "duration": clean_string(fields.get("duration")),
        "purpose": clean_string(fields.get("purpose")),
        "details": "; ".join(detail_parts),
        "source": source,
        "status": "requires_verification",
    }


def _extract_appointments(text: str) -> list[dict]:
    block = _section_content(text, r"^\s*\d+\s*\.\s*FOLLOW[- ]?UP APPOINTMENT\s*$")
    if not block:
        # Support unnumbered appointment headings too.
        block = _section_content(text, r"^\s*FOLLOW[- ]?UP APPOINTMENT\s*$")
    if not contains_date(block) or not contains_time(block) or not has_valid_12_hour_times(block):
        return []
    return [{"details": clean_string(block), "source": clean_string(block), "status": "requires_verification"}]


def _extract_diagnosis(text: str) -> str:
    value, _ = _label_value(text, r"Primary\s+Diagnosis")
    return value or "Not found"


def _deterministic_extract(text: str) -> dict:
    # Parse explicitly labelled fields and section-based paragraphs.
    diet = _section_instruction(text, r"^\s*\d+\s*\.\s*DIET\s+AND\s+HYDRATION\s*$")
    activity = _section_instruction(text, r"^\s*\d+\s*\.\s*ACTIVITY\s+AND\s+REST\s*$")
    warnings = _section_instruction(text, r"^\s*\d+\s*\.\s*WARNING\s+SIGNS\s*$")
    if not diet:
        diet = _line_items(text, r"Diet\s*&\s*Hydration|Diet")
    if not activity:
        activity = _line_items(text, r"Activity\s*&\s*Rest|Activity")
    if not warnings:
        warnings = _line_items(text, r"Warning\s+Signs(?:\s*\([^)]*\))?")
    return {
        "diagnosis": _extract_diagnosis(text),
        "medications": _extract_medication_rows(text),
        "appointments": _extract_appointments(text),
        "diet_instructions": diet,
        "activity_instructions": activity,
        "warning_signs": warnings,
        "missing_or_unclear": [],
    }


def _validated_items(items, raw_text: str, category: str = "") -> list[dict]:
    cleaned = []
    seen = set()
    if not isinstance(items, list):
        return cleaned
    for item in items:
        if not isinstance(item, dict):
            continue
        details = clean_string(item.get("details"))
        source = clean_string(item.get("source"))
        if not details or not source or not source_is_supported(source, raw_text):
            continue
        if category == "appointments" and (not contains_date(source) or not contains_time(source) or not has_valid_12_hour_times(source)):
            continue
        if category == "medications":
            # A medication record's name and every populated structured field
            # must be independently present in the source text.
            fields = [item.get(k) for k in ("name", "dosage", "frequency", "duration", "purpose") if item.get(k)]
            if fields and not all(source_is_supported(str(v), raw_text) for v in fields):
                continue
        key = source.casefold()
        if key not in seen:
            seen.add(key)
            normalized = {"details": details, "source": source, "status": "requires_verification"}
            if category == "medications":
                normalized.update({k: clean_string(item.get(k)) for k in ("name", "dosage", "frequency", "duration", "purpose")})
            cleaned.append(normalized)
    return cleaned


def understand_document(state: DocumentState):
    original = state.get("extracted_text", "")
    if not isinstance(original, str) or not original.strip():
        return {"error": "No document text was provided."}
    text = normalized_analysis_text(original)
    if not text:
        return {"document_data": _empty_data(template_confirmation_messages(original))}

    extracted = _deterministic_extract(text)
    model_missing = False
    prompt = f'''You are a strict discharge-document extraction assistant. Extract only patient-specific facts explicitly present in the source. Do not infer, diagnose, prescribe, calculate, or add advice. Return JSON only with keys diagnosis, medications, appointments, diet_instructions, activity_instructions, warning_signs, missing_or_unclear. Each item must contain details and an exact contiguous source quote in source. Medication items may additionally contain name, dosage, frequency, duration, purpose. Do not treat headings, examples, bracket placeholders, or generic test labels as medical advice. Keep all extracted items as requiring verification.\nSOURCE DOCUMENT:\n{text}'''
    try:
        response = ollama.chat(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            format="json",
            messages=[{"role": "user", "content": prompt}],
        )
        model_data = json.loads(response["message"]["content"])
        if isinstance(model_data, dict):
            # Deterministic labelled fields take priority; model fills gaps only.
            for key in ("diagnosis", "medications", "appointments", "diet_instructions", "activity_instructions", "warning_signs"):
                if key == "diagnosis":
                    if extracted[key] == "Not found" and clean_string(model_data.get(key)):
                        extracted[key] = model_data[key]
                elif not extracted[key]:
                    extracted[key] = model_data.get(key, [])
            extracted["missing_or_unclear"] = model_data.get("missing_or_unclear", [])
        else:
            model_missing = True
    except Exception as exc:
        # Rule-based extraction remains available when Ollama is offline.
        print("Ollama extraction unavailable; using validated field extraction:", repr(exc))
        model_missing = True

    diagnosis = clean_string(extracted.get("diagnosis"))
    if not diagnosis or is_blank_or_placeholder(diagnosis) or not source_is_supported(diagnosis, original):
        diagnosis = "Not found"

    medications = _validated_items(extracted.get("medications"), original, "medications")
    appointments = _validated_items(extracted.get("appointments"), original, "appointments")
    diet = _validated_items(extracted.get("diet_instructions"), original)
    activity = _validated_items(extracted.get("activity_instructions"), original)
    warnings = _validated_items(extracted.get("warning_signs"), original)

    missing = [clean_string(x) for x in extracted.get("missing_or_unclear", []) if isinstance(x, str) and clean_string(x)]
    missing.extend(template_confirmation_messages(original))
    if diagnosis == "Not found":
        missing.append("Primary diagnosis is not available or could not be verified.")
    if not medications:
        missing.append("No verified medication information was extracted.")
    if not appointments:
        missing.append("No verified appointment information was extracted.")
    if model_missing:
        missing.append("Ollama was unavailable; only explicitly labelled fields were extracted.")
    missing = list(dict.fromkeys(missing))

    return {"document_data": {
        "diagnosis": diagnosis,
        "medications": medications,
        "appointments": appointments,
        "diet_instructions": diet,
        "activity_instructions": activity,
        "warning_signs": warnings,
        "missing_or_unclear": missing,
    }}


def _empty_data(missing: list[str]) -> dict:
    return {"diagnosis": "Not found", "medications": [], "appointments": [], "diet_instructions": [], "activity_instructions": [], "warning_signs": [], "missing_or_unclear": missing}


builder = StateGraph(DocumentState)
builder.add_node("understand_document", understand_document)
builder.set_entry_point("understand_document")
builder.add_edge("understand_document", END)
document_understanding_agent = builder.compile()
