"""Compare core.extract.extract_record across the allowed models on the three fixture stories.

Run as: python scripts/compare_extract.py [model ...]
With no arguments every model in core.llm.ALLOWED_MODELS is compared.
The script never prints the API key, the config object or the model user message.
"""

import dataclasses
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import llm  # noqa: E402
from core.extract import extract_record  # noqa: E402
from core.fixtures import FIXTURE_STORIES  # noqa: E402


def _contains(text, word):
    return text is not None and word in text.lower()


CHECKS = {
    "fever_adult": (
        ("age is 34", lambda r: r.patient_age == 34),
        ("sex is null", lambda r: r.patient_sex is None),
        ("reporting_on_behalf is false", lambda r: r.reporting_on_behalf is False),
        (
            "allergies denied with empty list",
            lambda r: r.allergies_denied is True and r.allergies == [],
        ),
        (
            "a medicine name contains ginger",
            lambda r: any("ginger" in m.name.lower() for m in r.medicines),
        ),
        ("severity is null", lambda r: r.severity is None),
        ("onset contains yesterday", lambda r: _contains(r.onset, "yesterday")),
        ("medicines_denied is null", lambda r: r.medicines_denied is None),
        ("pregnant is null", lambda r: r.pregnant is None),
    ),
    "child_cough": (
        ("age is 7", lambda r: r.patient_age == 7),
        ("reporting_on_behalf is true", lambda r: r.reporting_on_behalf is True),
        ("sex is male", lambda r: r.patient_sex == "male"),
        ("duration contains five days", lambda r: _contains(r.duration, "five days")),
        (
            "medicines, allergies and medical history flags all null",
            lambda r: (
                r.medicines_denied is None
                and r.allergies_denied is None
                and r.medical_history_denied is None
            ),
        ),
        (
            "medicines and allergies are empty",
            lambda r: r.medicines == [] and r.allergies == [],
        ),
        (
            "a concern contains school",
            lambda r: any("school" in c.lower() for c in r.concerns),
        ),
        ("severity is null", lambda r: r.severity is None),
    ),
    "chest_pain": (
        ("age is 52", lambda r: r.patient_age == 52),
        ("sex is null", lambda r: r.patient_sex is None),
        ("reporting_on_behalf is false", lambda r: r.reporting_on_behalf is False),
        ("onset contains two days", lambda r: _contains(r.onset, "two days")),
        (
            "a medicine name contains amlodipine",
            lambda r: any("amlodipine" in m.name.lower() for m in r.medicines),
        ),
        (
            "a medical history item contains blood pressure",
            lambda r: any(
                "blood pressure" in h.lower() for h in r.medical_history
            ),
        ),
        (
            "a concern contains heart",
            lambda r: any("heart" in c.lower() for c in r.concerns),
        ),
        ("allergies_denied is null", lambda r: r.allergies_denied is None),
        ("severity is null", lambda r: r.severity is None),
    ),
}

_WORD_RE = re.compile(r"[a-z]+")


def new_words(record, story):
    texts = [
        value
        for value in (
            record.complaint,
            record.onset,
            record.duration,
            record.severity_note,
        )
        if value
    ]
    texts.extend(record.symptoms)
    texts.extend(record.medical_history)
    texts.extend(record.concerns)
    record_words = set()
    for text in texts:
        record_words.update(
            word for word in _WORD_RE.findall(text.lower()) if len(word) >= 4
        )
    story_words = set(_WORD_RE.findall(story.lower()))
    return sorted(record_words - story_words)


def main(argv):
    if argv:
        unknown = [name for name in argv if name not in llm.ALLOWED_MODELS]
        if unknown:
            print("Unknown model: " + ", ".join(unknown))
            print("Allowed models: " + ", ".join(llm.ALLOWED_MODELS))
            return 1
        models = tuple(argv)
    else:
        models = llm.ALLOWED_MODELS

    try:
        config = llm.load_config()
    except llm.ConfigError as error:
        print(str(error))
        return 1

    summary = {}
    for model in models:
        model_config = dataclasses.replace(config, model=model)
        passed_total = 0
        checks_total = 0
        errors = 0
        seconds_total = 0.0
        for name in FIXTURE_STORIES:
            story = FIXTURE_STORIES[name]
            checks = CHECKS[name]
            checks_total += len(checks)
            start = time.perf_counter()
            error = None
            record = None
            try:
                record = extract_record(story, config=model_config)
            except llm.LLMError as exc:
                error = exc
            seconds = time.perf_counter() - start
            seconds_total += seconds
            if error is not None:
                errors += 1
                line = [
                    model,
                    name,
                    type(error).__name__,
                    f"{seconds:.1f}",
                    f"0/{len(checks)}",
                    "-",
                    "-",
                    "-",
                ]
            else:
                passed = 0
                failed = []
                for label, predicate in checks:
                    if predicate(record):
                        passed += 1
                    else:
                        failed.append(label)
                passed_total += passed
                words = new_words(record, story)
                complaint = f'"{record.complaint}"' if record.complaint else "-"
                line = [
                    model,
                    name,
                    "OK",
                    f"{seconds:.1f}",
                    f"{passed}/{len(checks)}",
                    ", ".join(failed) if failed else "-",
                    ", ".join(words) if words else "-",
                    complaint,
                ]
            print(" | ".join(line))
        print(
            f"{model} | {passed_total}/{checks_total} | {errors} | {seconds_total:.1f}"
        )
        summary[model] = (passed_total, errors, seconds_total)

    best = min(
        summary, key=lambda m: (-summary[m][0], summary[m][1], summary[m][2])
    )
    print(
        "Best model: "
        f"{best} ({summary[best][0]}/{sum(len(v) for v in CHECKS.values())} "
        f"checks passed, {summary[best][1]} errors, {summary[best][2]:.1f}s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
