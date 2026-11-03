"""Tests for the PDF builder in ui/export_pdf.py.

Text is checked with pypdf extraction; folders use tmp_path; all data is
neutral fictional content. No network.
"""

import os
import re
import time
from copy import deepcopy
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from ui.export_pdf import (
    FONT_PATH,
    PDF_NAME,
    build_pdf,
    cleanup_old_exports,
    new_session_dir,
    note_date,
    remove_pdf,
)


def _summary(**overrides) -> dict:
    data = {
        "doctor_card": (
            "Patient: 52, female\n"
            'Problem: "A tight pain in my chest that comes and goes."\n'
            "Medicines: amlodipine\n"
            "Allergies: Not given"
        ),
        "patient_script": (
            "I am 52. For two days I have had a tight pain in my chest "
            "that comes and goes."
        ),
        "priority_questions": [
            "What could be causing this pain?",
            "Should I come back sooner?",
        ],
    }
    data.update(overrides)
    return data


def _alerts() -> list[dict]:
    return [
        {
            "code": "high_fever",
            "message": (
                "You reported a high fever. Please make sure to tell your "
                "doctor about this during the visit."
            ),
            "level": "attention",
        },
        {
            "code": "chest_pain",
            "message": (
                "You reported chest pain or tightness. In Indonesia, "
                "emergency medical services can be reached on 119. Please "
                "seek medical care now or tell the doctor immediately."
            ),
            "level": "urgent",
        },
    ]


def _pages(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [
        re.sub(r"\s+", " ", page.extract_text() or "") for page in reader.pages
    ]


def test_note_date_format():
    assert note_date(date(2026, 11, 3)) == "3 November 2026"
    assert note_date(date(2026, 12, 25)) == "25 December 2026"


def test_output_path_and_pdf_signature(tmp_path):
    path = build_pdf(_summary(), [], tmp_path, prepared_on=date(2026, 11, 3))
    assert path == tmp_path / "visitprep-visit-note.pdf"
    with open(path, "rb") as handle:
        assert handle.read(4) == b"%PDF"


def test_extracted_text_contains_expected_strings(tmp_path):
    path = build_pdf(_summary(), [], tmp_path, prepared_on=date(2026, 11, 3))
    text = "\n".join(_pages(path))
    for expected in (
        "Visit note",
        "3 November 2026",
        "Not a diagnosis.",
        "For the doctor",
        "What to say",
        "Questions to ask",
        "1. ",
        "2. ",
    ):
        assert expected in text


def test_special_characters_in_doctor_card(tmp_path):
    card = "Allergies: Caf\u00e9 au lait; na\u00efve remedy; temperature 38.5\u00b0C \u2014 maybe"
    path = build_pdf(
        _summary(doctor_card=card), [], tmp_path, prepared_on=date(2026, 11, 3)
    )
    text = "\n".join(_pages(path))
    assert "Caf\u00e9" in text
    assert "na\u00efve" in text


def test_script_is_printed_literally(tmp_path):
    script = "<script>alert(1)</script>"
    path = build_pdf(
        _summary(patient_script=script), [], tmp_path, prepared_on=date(2026, 11, 3)
    )
    text = "\n".join(_pages(path))
    assert script in text


def test_long_script_spans_multiple_pages(tmp_path):
    script = " ".join(f"word{i}" for i in range(1500))
    path = build_pdf(
        _summary(patient_script=script), [], tmp_path, prepared_on=date(2026, 11, 3)
    )
    pages = _pages(path)
    assert len(pages) >= 2
    assert "Page 1 of " in pages[0]
    assert "VisitPrep \u00b7 not a diagnosis" in pages[-1]


def test_alerts_urgent_first_and_messages_verbatim(tmp_path):
    alerts = _alerts()  # given as [attention, urgent]
    path = build_pdf(_summary(), alerts, tmp_path, prepared_on=date(2026, 11, 3))
    text = "\n".join(_pages(path))
    assert text.index("Get medical help now") < text.index(
        "Tell your doctor about this"
    )
    for alert in alerts:
        assert alert["message"] in text


def test_no_alerts_no_band_headings(tmp_path):
    path = build_pdf(_summary(), [], tmp_path, prepared_on=date(2026, 11, 3))
    text = "\n".join(_pages(path))
    assert "Get medical help now" not in text
    assert "Tell your doctor about this" not in text


def test_no_questions_no_heading(tmp_path):
    path = build_pdf(
        _summary(priority_questions=[]), [], tmp_path, prepared_on=date(2026, 11, 3)
    )
    text = "\n".join(_pages(path))
    assert "Questions to ask" not in text


def test_build_twice_leaves_one_file(tmp_path):
    path1 = build_pdf(_summary(), [], tmp_path, prepared_on=date(2026, 11, 3))
    path2 = build_pdf(_summary(), [], tmp_path, prepared_on=date(2026, 11, 4))
    assert path1 == path2
    assert list(tmp_path.iterdir()) == [path1]


def test_inputs_not_mutated(tmp_path):
    summary = _summary()
    alerts = _alerts()
    summary_before = deepcopy(summary)
    alerts_before = deepcopy(alerts)
    build_pdf(summary, alerts, tmp_path, prepared_on=date(2026, 11, 3))
    assert summary == summary_before
    assert alerts == alerts_before


def test_new_session_dir_and_remove_pdf():
    dir_a = new_session_dir()
    dir_b = new_session_dir()
    assert dir_a != dir_b
    assert dir_b.exists()
    path = build_pdf(_summary(), [], dir_a, prepared_on=date(2026, 11, 3))
    remove_pdf(path)
    assert not path.exists()
    assert not dir_a.exists()
    assert dir_b.exists()
    remove_pdf(None)
    remove_pdf(dir_a / PDF_NAME)


def test_cleanup_old_exports(tmp_path):
    old = tmp_path / "visitprep_old"
    old.mkdir()
    (old / "stale.pdf").write_bytes(b"%PDF-1.4 stale")
    fresh = tmp_path / "visitprep_new"
    fresh.mkdir()
    foreign = tmp_path / "other_old"
    foreign.mkdir()
    stale_time = time.time() - 2 * 60 * 60
    os.utime(old, (stale_time, stale_time))
    os.utime(foreign, (stale_time, stale_time))
    deleted = cleanup_old_exports(root=tmp_path)
    assert deleted == 1
    assert not old.exists()
    assert fresh.exists()
    assert foreign.exists()


def test_font_files_exist():
    assert FONT_PATH.is_file()
    assert (FONT_PATH.parent / "OFL.txt").is_file()
