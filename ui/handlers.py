"""Session handlers for the VisitPrep UI.

Plain functions that take the session state dict plus inputs and
return a new state dict. They never mutate their input and never
import gradio. Alerts come only from core.redflag, questions only
from core.interview, and the model calls only through ui.backend.
recompute_alerts is the only place a broad except Exception is
allowed, because the failure is shown to the user.
"""

from core import interview
from core import redflag
from core.llm import LLMError
from core.schema import (
    SEX_VALUES,
    Alert,
    QuestionAnswer,
    record_from_dict,
    record_to_dict,
)

import ui.backend as backend
from ui.state import bump

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
    """Step 2: go to step 3 (the merge happens in a later task)."""
    if state["step"] != 2:
        return state
    result = dict(state)
    result["question"] = None
    result["error"] = None
    result["step"] = 3
    return bump(result)


def append_chip(text: str, chip: str) -> str:
    """Append a chip phrase to the story text; never replaces it."""
    text = text or ""
    if not text:
        return chip
    if text.endswith("."):
        return text + "\n" + chip
    return text + " " + chip
