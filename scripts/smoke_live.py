"""Live smoke test of one VisitPrep session on the chest_pain fixture story.

Run as: python scripts/smoke_live.py [model]
With no arguments the configured model is used; the optional argument must be
one of core.llm.ALLOWED_MODELS and replaces the configured model.
The script makes real model calls and never prints the API key, the config
object or a request body.
"""

import dataclasses
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import llm  # noqa: E402
from core.extract import extract_record  # noqa: E402
from core.fixtures import FIXTURE_STORIES  # noqa: E402
from core.interview import (  # noqa: E402
    QUESTIONS_SELF,
    merge_answers,
    next_question,
)
from core.redflag import check_alerts, scan_text  # noqa: E402
from core.schema import QuestionAnswer  # noqa: E402
from core.summarize import generate_summary  # noqa: E402

ANSWERS = {
    "severity": "Moderate, I think.",
    "onset": "Two days ago.",
    "duration": "It comes and goes, for two days.",
    "medicines": "Only amlodipine.",
    "allergies": "No allergies.",
    "medical_history": "High blood pressure.",
    "age": "52.",
    "sex": "Female.",
    "concerns": "Is it my heart?",
}

FIELD_BY_QUESTION = {question: field for field, question in QUESTIONS_SELF.items()}


def _dedup_by_code(alerts):
    seen = set()
    result = []
    for alert in alerts:
        if alert.code not in seen:
            seen.add(alert.code)
            result.append(alert)
    return result


def main() -> int:
    try:
        config = llm.load_config()
    except llm.ConfigError as error:
        print(str(error))
        return 1

    if len(sys.argv) > 1:
        model = sys.argv[1]
        if model not in llm.ALLOWED_MODELS:
            print("Unknown model. Allowed models: " + ", ".join(llm.ALLOWED_MODELS))
            return 1
        config = dataclasses.replace(config, model=model)

    story = FIXTURE_STORIES["chest_pain"]
    model_seconds = 0.0

    alerts = scan_text(story)
    print("story alerts: " + ", ".join(alert.code for alert in alerts))

    start = time.perf_counter()
    try:
        record = extract_record(story, config=config)
    except llm.LLMError as error:
        print(f"extract failed: {type(error).__name__}: {error}")
        return 1
    elapsed = time.perf_counter() - start
    model_seconds += elapsed
    print(f"extract: {elapsed:.1f}s")

    asked: list[QuestionAnswer] = []
    for _ in range(3):
        question = next_question(record, asked, [])
        if question is None:
            break
        field = FIELD_BY_QUESTION.get(question)
        if field is None:
            break
        answer = ANSWERS[field]
        asked.append(QuestionAnswer(question, answer))
        print("Q: " + question)
        print("A: " + answer)

    start = time.perf_counter()
    try:
        record = merge_answers(record, asked, config=config)
    except llm.LLMError as error:
        print(f"merge failed: {type(error).__name__}: {error}")
        return 1
    elapsed = time.perf_counter() - start
    model_seconds += elapsed
    print(f"merge: {elapsed:.1f}s")

    answers = [item.answer for item in asked]
    alerts = _dedup_by_code(scan_text(story, *answers) + check_alerts(record))
    print(
        "alerts: "
        + ", ".join(f"{alert.code} ({alert.level})" for alert in alerts)
    )

    start = time.perf_counter()
    try:
        summary = generate_summary(record, asked, config=config)
    except llm.LLMError as error:
        print(f"summary failed: {type(error).__name__}: {error}")
        return 1
    elapsed = time.perf_counter() - start
    model_seconds += elapsed
    print(f"summary: {elapsed:.1f}s")
    print(summary.doctor_card)
    print(f"Script ({len(summary.patient_script.split())} words):")
    print(summary.patient_script)
    for index, question in enumerate(summary.priority_questions, 1):
        print(f"{index}. {question}")
    print(f"total model time: {model_seconds:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
