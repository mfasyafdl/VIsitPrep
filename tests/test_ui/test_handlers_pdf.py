"""Tests for the PDF handler in ui/handlers.py.

make_pdf builds the note once per summary; save_section,
on_change_details and on_reset remove the file when the note is no
longer current. The real build_pdf is used where a file must exist;
new_session_dir and cleanup_old_exports are faked to stay inside
tmp_path. No network is used. All data is neutral and fictional.
"""

import copy
from pathlib import Path

from core import fixtures
from core.schema import record_to_dict

from ui import export_pdf, handlers
from ui.state import new_state

_PDF_NAME = "visitprep-visit-note.pdf"


def _step4_state(pdf_path=None):
    state = new_state()
    state["step"] = 4
    state["story"] = "My son has had a cough for five days."
    state["alert_texts"] = ["My son has had a cough for five days."]
    state["merged"] = True
    state["record"] = record_to_dict(fixtures.get_fixture("child_cough"))
    state["summary"] = {
        "doctor_card": "Patient: 7 years old",
        "patient_script": "I am here about my son.",
        "priority_questions": ["Should he stay home from school?"],
    }
    state["pdf_path"] = pdf_path
    return state


def _step3_state(editing="problem"):
    state = new_state()
    state["step"] = 3
    state["story"] = "My son has had a cough for five days."
    state["alert_texts"] = ["My son has had a cough for five days."]
    state["merged"] = True
    state["editing"] = editing
    state["record"] = record_to_dict(fixtures.get_fixture("child_cough"))
    return state


def _fake_temp_dirs(monkeypatch, tmp_path):
    """new_session_dir and cleanup_old_exports stay inside tmp_path."""
    dirs = []

    def fake_new_session_dir():
        folder = tmp_path / f"visitprep_fake{len(dirs) + 1}"
        dirs.append(folder)
        return folder

    cleanups = []

    def fake_cleanup(*args, **kwargs):
        cleanups.append((args, kwargs))
        return 0

    monkeypatch.setattr("ui.export_pdf.new_session_dir", fake_new_session_dir)
    monkeypatch.setattr("ui.export_pdf.cleanup_old_exports", fake_cleanup)
    return dirs, cleanups


# make_pdf


def test_make_pdf_builds_the_note_once(tmp_path, monkeypatch):
    dirs, cleanups = _fake_temp_dirs(monkeypatch, tmp_path)
    state = _step4_state()
    original = copy.deepcopy(state)
    result = handlers.make_pdf(state)
    assert len(cleanups) == 1
    assert dirs == [tmp_path / "visitprep_fake1"]
    expected = tmp_path / "visitprep_fake1" / _PDF_NAME
    assert result["pdf_path"] == str(expected)
    assert expected.exists()
    assert expected.read_bytes()[:4] == b"%PDF"
    assert result["error"] is None
    assert result["step"] == 4
    assert result["summary"] == original["summary"]
    assert result["token"] == state["token"] + 1
    assert state == original
    again = handlers.make_pdf(result)
    assert again is result
    assert len(cleanups) == 1
    assert len(dirs) == 1
    assert len(list(tmp_path.glob("visitprep_*"))) == 1


def test_make_pdf_does_nothing_off_step4_without_summary_or_when_built(
    tmp_path, monkeypatch
):
    dirs, cleanups = _fake_temp_dirs(monkeypatch, tmp_path)

    def boom(*args, **kwargs):
        raise AssertionError("new_session_dir must not be called")

    monkeypatch.setattr("ui.export_pdf.new_session_dir", boom)
    off_step = _step4_state()
    off_step["step"] = 3
    assert handlers.make_pdf(off_step) is off_step
    no_summary = _step4_state()
    no_summary["summary"] = None
    assert handlers.make_pdf(no_summary) is no_summary
    built = _step4_state(pdf_path="/tmp/visitprep_fake_built.pdf")
    assert handlers.make_pdf(built) is built
    assert cleanups == []
    assert dirs == []
    assert list(tmp_path.iterdir()) == []


def test_make_pdf_failure_keeps_the_summary_and_sets_the_error(
    tmp_path, monkeypatch
):
    _fake_temp_dirs(monkeypatch, tmp_path)

    def broken_build(*args, **kwargs):
        raise RuntimeError("the disk is on fire")

    monkeypatch.setattr("ui.export_pdf.build_pdf", broken_build)
    state = _step4_state()
    original = copy.deepcopy(state)
    result = handlers.make_pdf(state)
    assert result["error"] == handlers.PDF_FAILED
    assert (
        result["error"]
        == "The PDF could not be created. You can still copy the note above."
    )
    assert result["summary"] == original["summary"]
    assert result["pdf_path"] is None
    assert result["step"] == 4
    assert result["token"] == state["token"] + 1
    assert state == original
    assert list(tmp_path.iterdir()) == []


# removal when the note is no longer current


def test_on_change_details_removes_the_built_pdf(tmp_path, monkeypatch):
    _fake_temp_dirs(monkeypatch, tmp_path)
    built = handlers.make_pdf(_step4_state())
    path = Path(built["pdf_path"])
    assert path.exists()
    result = handlers.on_change_details(built)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["pdf_path"] is None
    assert not path.exists()
    assert not path.parent.exists()


def test_on_reset_removes_the_built_pdf(tmp_path, monkeypatch):
    _fake_temp_dirs(monkeypatch, tmp_path)
    built = handlers.make_pdf(_step4_state())
    path = Path(built["pdf_path"])
    assert path.exists()
    result = handlers.on_reset(built)
    assert result == new_state()
    assert not path.exists()
    assert not path.parent.exists()


def test_on_reset_without_a_pdf_does_not_raise():
    fresh = new_state()
    assert handlers.on_reset(fresh) == new_state()
    state = _step4_state()
    state["pdf_path"] = None
    assert handlers.on_reset(state) == new_state()


def test_save_section_removes_a_stale_pdf(tmp_path, monkeypatch):
    _fake_temp_dirs(monkeypatch, tmp_path)
    folder = tmp_path / "visitprep_stale"
    folder.mkdir()
    stale = export_pdf.build_pdf(
        {
            "doctor_card": "Patient: 7 years old",
            "patient_script": "I am here about my son.",
            "priority_questions": ["Should he stay home from school?"],
        },
        [],
        folder,
    )
    state = _step3_state(editing="problem")
    state["pdf_path"] = str(stale)
    original = copy.deepcopy(state)
    result = handlers.save_section(
        state,
        "problem",
        {"complaint": "a cough for five days", "symptoms": "cough"},
    )
    assert result["error"] is None
    assert result["pdf_path"] is None
    assert not stale.exists()
    assert not folder.exists()
    assert state == original


# no mutation


def test_pdf_handlers_never_mutate_the_input_state(tmp_path, monkeypatch):
    _fake_temp_dirs(monkeypatch, tmp_path)
    state = _step4_state()
    original = copy.deepcopy(state)
    handlers.make_pdf(state)
    assert state == original

    state = _step4_state(pdf_path="/tmp/visitprep_ghost1.pdf")
    original = copy.deepcopy(state)
    handlers.on_change_details(state)
    assert state == original

    state = _step3_state(editing="problem")
    state["pdf_path"] = "/tmp/visitprep_ghost2.pdf"
    original = copy.deepcopy(state)
    handlers.save_section(
        state, "problem", {"complaint": "a cough", "symptoms": "cough"}
    )
    assert state == original

    state = _step4_state(pdf_path="/tmp/visitprep_ghost3.pdf")
    original = copy.deepcopy(state)
    handlers.on_reset(state)
    assert state == original
