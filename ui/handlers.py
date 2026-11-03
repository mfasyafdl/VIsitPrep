"""Session handlers for the VisitPrep UI.

Plain functions that take the session state dict plus inputs and
return a new state dict. They never mutate their input and never
import gradio. Alerts come only from core.redflag, questions only
from core.interview, and the model calls only through ui.backend.
recompute_alerts is the only place a broad except Exception is
allowed, because the failure is shown to the user.
"""

import copy

from core import interview
from core import redflag
from core.llm import LLMError
from core.schema import (
    SEX_VALUES,
    Alert,
    QuestionAnswer,
    SchemaError,
    record_from_dict,
    record_to_dict,
    recompute_missing_information,
)

import ui.backend as backend
from ui.state import bump, new_state

_MAX_QUESTIONS = 5

_NOT_READY = (
    "This part of VisitPrep is not finished yet. "
    "Your notes are kept. Please try again later."
)


def _alert_dicts(alerts) -> list[dict]:
    return [
        {"code": alert.code, "message": alert.message, "level": alert.level}
        for alert in alerts
    ]


def recompute_alerts(state: dict) -> dict:
    """Rescan all alert texts plus the record and replace the alerts.

    Dedup by code keeping the first; urgent alerts first, then by
    code. On any failure the previous alerts are kept and
    alerts_error is set, so the failure is visible to the user.
    """
    result = dict(state)
    try:
        alerts = list(redflag.scan_text(*state["alert_texts"]))
        if state["record"] is not None:
            alerts = alerts + list(
                redflag.check_alerts(record_from_dict(state["record"]))
            )
        seen = set()
        unique = []
        for alert in alerts:
            if alert.code in seen:
                continue
            seen.add(alert.code)
            unique.append(
                Alert(code=alert.code, message=alert.message, level=alert.level)
            )
        unique.sort(key=lambda a: (0 if a.level == "urgent" else 1, a.code))
        result["alerts"] = _alert_dicts(unique)
        result["alerts_error"] = False
    except Exception:
        result["alerts"] = list(state["alerts"])
        result["alerts_error"] = True
    return result


def _parse_age(age_text) -> tuple[int | None, str | None]:
    stripped = (age_text or "").strip()
    if not stripped:
        return None, None
    try:
        value = int(stripped)
    except ValueError:
        return None, stripped
    if 0 <= value <= 130:
        return value, stripped
    return None, stripped


def _next_question(record, asked, skipped) -> str | None:
    return interview.next_question(
        record,
        [QuestionAnswer(**qa) for qa in asked],
        [entry["question"] for entry in skipped],
    )


def on_continue(state: dict, story, age_text, sex) -> dict:
    """Step 1: store the story, check alerts, extract the record."""
    if state["step"] != 1:
        return state
    text = (story or "").strip()
    if not text:
        result = dict(state)
        result["error"] = "Please describe your symptoms first."
        return bump(result)
    age, age_stripped = _parse_age(age_text)
    details = {
        "patient_age": age,
        "patient_age_text": age_stripped,
        "patient_sex": sex if sex in SEX_VALUES else None,
    }
    result = dict(state)
    result["story"] = text
    result["details"] = details
    result["alert_texts"] = [text]
    result["error"] = None
    result = recompute_alerts(result)
    try:
        record = backend.extract(text, details)
    except LLMError as err:
        result["error"] = (
            str(err) + " Your text is kept. Press Continue to try again."
        )
        return bump(result)
    except NotImplementedError:
        result["error"] = _NOT_READY
        return bump(result)
    result["record"] = record_to_dict(record)
    result = recompute_alerts(result)
    if len(result["asked"]) + len(result["skipped"]) >= _MAX_QUESTIONS:
        result["question"] = None
        result["step"] = 3
        return bump(result)
    try:
        question = _next_question(record, result["asked"], result["skipped"])
    except NotImplementedError:
        result["error"] = _NOT_READY
        return bump(result)
    result["question"] = question
    result["step"] = 3 if question is None else 2
    result["error"] = None
    return bump(result)


def on_answer(state: dict, answer) -> dict:
    """Step 2: store the answer, check alerts, ask the next question."""
    if state["step"] != 2:
        return state
    text = (answer or "").strip()
    if not text:
        result = dict(state)
        result["error"] = "Type an answer, or press Skip this question."
        return bump(result)
    result = dict(state)
    result["asked"] = list(state["asked"]) + [
        {"question": state["question"], "answer": text}
    ]
    result["alert_texts"] = list(state["alert_texts"]) + [text]
    result["error"] = None
    result = recompute_alerts(result)
    if len(result["asked"]) + len(result["skipped"]) >= _MAX_QUESTIONS:
        result["question"] = None
        result["step"] = 3
        return bump(result)
    try:
        question = _next_question(
            record_from_dict(result["record"]), result["asked"], result["skipped"]
        )
    except NotImplementedError:
        result = dict(state)
        result["error"] = _NOT_READY
        return bump(result)
    result["question"] = question
    result["step"] = 3 if question is None else 2
    result["error"] = None
    return bump(result)


def on_skip(state: dict) -> dict:
    """Step 2: record the skipped question, ask the next question."""
    if state["step"] != 2:
        return state
    position = len(state["asked"]) + len(state["skipped"]) + 1
    result = dict(state)
    result["skipped"] = list(state["skipped"]) + [
        {"question": state["question"], "position": position}
    ]
    result["error"] = None
    if len(result["asked"]) + len(result["skipped"]) >= _MAX_QUESTIONS:
        result["question"] = None
        result["step"] = 3
        return bump(result)
    try:
        question = _next_question(
            record_from_dict(result["record"]), result["asked"], result["skipped"]
        )
    except NotImplementedError:
        result = dict(state)
        result["error"] = _NOT_READY
        return bump(result)
    result["question"] = question
    result["step"] = 3 if question is None else 2
    result["error"] = None
    return bump(result)


def on_finish(state: dict) -> dict:
    """Step 2: go to step 3 (the merge happens in enter_review)."""
    if state["step"] != 2:
        return state
    result = dict(state)
    result["question"] = None
    result["error"] = None
    result["step"] = 3
    return bump(result)


# The seven review sections, in page order.
SECTIONS = ("problem", "timing", "medicines", "allergies", "history", "concerns", "about")

_SAVE_FAILED = "This could not be saved. Please check what you typed."
_CONFLICT = "Remove the items, or untick the box."


def enter_review(state: dict) -> dict:
    """Step 3: fold all answers into the record, exactly once."""
    if state["step"] != 3 or state["merged"]:
        return state
    result = dict(state)
    try:
        merged = backend.merge(
            record_from_dict(state["record"]),
            [QuestionAnswer(**qa) for qa in state["asked"]],
        )
    except LLMError as err:
        result["error"] = (
            str(err)
            + " Your answers are kept. "
            "You can still check and change your details below."
        )
    except NotImplementedError:
        result["error"] = _NOT_READY
    else:
        result["record"] = record_to_dict(merged)
        result["error"] = None
    result["merged"] = True
    result = recompute_alerts(result)
    return bump(result)


def open_editor(state: dict, section: str) -> dict:
    """Step 3: open one section editor; only one can be open."""
    if state["step"] != 3 or not state["merged"] or section not in SECTIONS:
        return state
    result = dict(state)
    result["editing"] = section
    result["error"] = None
    return bump(result)


def cancel_editor(state: dict) -> dict:
    """Step 3: close the open editor without saving."""
    if state["step"] != 3 or not state["merged"]:
        return state
    result = dict(state)
    result["editing"] = None
    result["error"] = None
    return bump(result)


def _medicine_line(medicine: dict) -> str:
    if medicine["frequency"]:
        return f"{medicine['name']}, {medicine['frequency']}"
    return medicine["name"]


def editor_values(record: dict, section: str) -> dict:
    """The values that prefill the editor of the given section."""
    if section == "problem":
        return {
            "complaint": record["complaint"] or "",
            "symptoms": "\n".join(record["symptoms"]),
        }
    if section == "timing":
        return {
            "onset": record["onset"] or "",
            "duration": record["duration"] or "",
            "severity": record["severity"] or "not-sure",
        }
    if section == "medicines":
        return {
            "lines": "\n".join(_medicine_line(m) for m in record["medicines"]),
            "none": record["medicines_denied"] is True,
        }
    if section == "allergies":
        return {
            "lines": "\n".join(record["allergies"]),
            "none": record["allergies_denied"] is True,
        }
    if section == "history":
        return {
            "lines": "\n".join(record["medical_history"]),
            "none": record["medical_history_denied"] is True,
        }
    if section == "concerns":
        return {"lines": "\n".join(record["concerns"])}
    if section == "about":
        age = record["patient_age_text"]
        if age is None and record["patient_age"] is not None:
            age = str(record["patient_age"])
        return {
            "age_text": age or "",
            "sex": record["patient_sex"],
        }
    raise ValueError(f"Unknown section: {section!r}")


def _text_or_none(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def _list_from_lines(value) -> list[str]:
    return [line.strip() for line in str(value or "").split("\n") if line.strip()]


def _medicine_parts(line: str) -> tuple[str, str | None]:
    if "," in line:
        name, frequency = line.split(",", 1)
        return name.strip(), frequency.strip() or None
    return line.strip(), None


def _merge_medicines(old: list, lines: list[str]) -> list[dict]:
    existing = {
        medicine["name"].casefold().strip(): medicine for medicine in old
    }
    merged = []
    for line in lines:
        name, frequency = _medicine_parts(line)
        match = existing.get(name.casefold().strip())
        if match is None:
            merged.append(
                {
                    "name": name,
                    "medicine_type": "unknown",
                    "dose": None,
                    "frequency": frequency,
                    "duration": None,
                    "notes": None,
                }
            )
        else:
            merged.append(
                {
                    "name": match["name"],
                    "medicine_type": match["medicine_type"],
                    "dose": match["dose"],
                    "frequency": frequency or match["frequency"],
                    "duration": match["duration"],
                    "notes": match["notes"],
                }
            )
    return merged


def _section_texts(section: str, data: dict) -> list:
    """The text values the given section now holds (nulls possible)."""
    if section == "problem":
        texts = [data["complaint"]]
        texts.extend(data["symptoms"])
        return texts
    if section == "timing":
        return [data["onset"], data["duration"]]
    if section == "medicines":
        return [medicine["name"] for medicine in data["medicines"]]
    if section == "allergies":
        return list(data["allergies"])
    if section == "history":
        return list(data["medical_history"])
    if section == "concerns":
        return list(data["concerns"])
    if section == "about":
        return [data["patient_age_text"]]
    return []


def _apply_section(data: dict, section: str, values: dict) -> list | None:
    """Apply one editor to the new record dict in place.

    Returns the section's text values, or None when the "none" box is
    ticked together with at least one item.
    """
    if section == "problem":
        data["complaint"] = _text_or_none(values.get("complaint"))
        data["symptoms"] = _list_from_lines(values.get("symptoms"))
        return _section_texts(section, data)
    if section == "timing":
        data["onset"] = _text_or_none(values.get("onset"))
        data["duration"] = _text_or_none(values.get("duration"))
        severity = values.get("severity")
        data["severity"] = None if severity in (None, "not-sure") else severity
        return _section_texts(section, data)
    if section == "medicines":
        items = _list_from_lines(values.get("lines"))
        denied = values.get("none") is True
        if denied and items:
            return None
        data["medicines"] = _merge_medicines(data["medicines"], items)
        data["medicines_denied"] = True if denied else None
        return _section_texts(section, data)
    if section in ("allergies", "history"):
        items = _list_from_lines(values.get("lines"))
        denied = values.get("none") is True
        if denied and items:
            return None
        key = "allergies" if section == "allergies" else "medical_history"
        data[key] = items
        data[key + "_denied"] = True if denied else None
        return _section_texts(section, data)
    if section == "concerns":
        data["concerns"] = _list_from_lines(values.get("lines"))
        return _section_texts(section, data)
    if section == "about":
        age, age_text = _parse_age(values.get("age_text"))
        data["patient_age"] = age
        data["patient_age_text"] = age_text
        sex = values.get("sex")
        data["patient_sex"] = sex if sex in SEX_VALUES else None
        return _section_texts(section, data)
    raise ValueError(f"Unknown section: {section!r}")


def save_section(state: dict, section: str, values: dict) -> dict:
    """Step 3: save the open editor into a new record."""
    if (
        state["step"] != 3
        or not state["merged"]
        or section not in SECTIONS
        or state["editing"] != section
    ):
        return state
    data = copy.deepcopy(state["record"])
    new_texts = _apply_section(data, section, values)
    if new_texts is None:
        result = dict(state)
        result["error"] = _CONFLICT
        return bump(result)
    try:
        record = record_from_dict(data)
    except SchemaError:
        result = dict(state)
        result["error"] = _SAVE_FAILED
        return bump(result)
    record = recompute_missing_information(record)
    existing = list(state["alert_texts"])
    result = dict(state)
    result["record"] = record_to_dict(record)
    result["alert_texts"] = existing + [
        text for text in new_texts if text and text not in existing
    ]
    result["editing"] = None
    result["error"] = None
    result["summary"] = None
    result["pdf_path"] = None
    result = recompute_alerts(result)
    return bump(result)


def on_summarize(state: dict) -> dict:
    """Step 3: generate the visit note, exactly once."""
    if state["step"] != 3 or not state["merged"]:
        return state
    if state["editing"] is not None:
        result = dict(state)
        result["error"] = "Save or cancel your change first."
        return bump(result)
    result = dict(state)
    try:
        summary = backend.summarize(
            record_from_dict(state["record"]),
            [QuestionAnswer(**qa) for qa in state["asked"]],
            state["story"],
        )
    except LLMError as err:
        result["error"] = (
            str(err)
            + " Your details are kept. Press Write my summary to try again."
        )
        return bump(result)
    except NotImplementedError:
        result["error"] = _NOT_READY
        return bump(result)
    result["summary"] = {
        "doctor_card": summary.doctor_card,
        "patient_script": summary.patient_script,
        "priority_questions": list(summary.priority_questions),
    }
    result["error"] = None
    result["step"] = 4
    return bump(result)


def on_change_details(state: dict) -> dict:
    """Step 4: go back to step 3 without running the merge again."""
    if state["step"] != 4:
        return state
    result = dict(state)
    result["step"] = 3
    result["summary"] = None
    result["pdf_path"] = None
    result["editing"] = None
    result["error"] = None
    return bump(result)


def on_reset(state: dict) -> dict:
    """Any step: a fresh session state."""
    return new_state()


def append_chip(text: str, chip: str) -> str:
    """Append a chip phrase to the story text; never replaces it."""
    text = text or ""
    if not text:
        return chip
    if text.endswith("."):
        return text + "\n" + chip
    return text + " " + chip
