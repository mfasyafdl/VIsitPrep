"""Tests for the pure HTML functions in ui/components.py."""

import re
from datetime import date
from types import SimpleNamespace

from ui.components import (
    ALERTS_ERROR_MESSAGE,
    DETAIL_ROWS,
    answers_list_html,
    alerts_error_html,
    alerts_html,
    change_label,
    detail_row_html,
    footer_html,
    header_html,
    note_date,
    pips_html,
    preview_banner_html,
    progress_html,
    question_heading_html,
    question_text_html,
    questions_html,
    rail_html,
    read_time_seconds,
    script_html,
    visit_note_html,
)


def _alert(level, message):
    return SimpleNamespace(level=level, message=message)


def test_urgent_alert_has_call_link_heading_and_hidden_label():
    html_text = alerts_html([_alert("urgent", "Chest pain spreading to the arm.")])
    assert 'href="tel:119"' in html_text
    assert "Get medical help now" in html_text
    assert "Call 119" in html_text
    match = re.search(r'<span class="vp-sr-only">(.*?)</span>', html_text)
    assert match is not None
    assert "Urgent advice:" in match.group(1)


def test_urgent_card_heading_is_h2_with_sr_only_prefix():
    html_text = alerts_html([_alert("urgent", "Chest pain spreading to the arm.")])
    assert (
        '<h2 class="vp-card-heading"><span class="vp-sr-only">Urgent advice:</span> '
        "Get medical help now</h2>" in html_text
    )


def test_urgent_call_link_has_button_class():
    html_text = alerts_html([_alert("urgent", "m")])
    assert '<a class="vp-btn vp-btn-call" href="tel:119">Call 119</a>' in html_text


def test_attention_alert_heading_and_no_call_link():
    html_text = alerts_html([_alert("attention", "Fever for two days.")])
    assert "Tell your doctor about this" in html_text
    assert "tel:" not in html_text
    assert (
        '<h2 class="vp-card-heading"><span class="vp-sr-only">Attention:</span> '
        "Tell your doctor about this</h2>" in html_text
    )


def test_alert_message_is_escaped():
    html_text = alerts_html([_alert("attention", "<script>x</script>")])
    assert "<script>" not in html_text
    assert "&lt;script&gt;x&lt;/script&gt;" in html_text


def test_no_alerts_renders_empty_live_container():
    html_text = alerts_html([])
    assert 'class="vp-alerts' in html_text
    assert 'aria-live="polite"' in html_text
    assert re.sub(r"<[^>]+>", "", html_text).strip() == ""


def test_container_role_depends_on_urgency():
    urgent = alerts_html([_alert("urgent", "m"), _alert("attention", "n")])
    assert 'role="alert"' in urgent
    attention_only = alerts_html([_alert("attention", "m")])
    assert 'aria-live="polite"' in attention_only
    assert "role=" not in attention_only


def test_unknown_alert_level_raises():
    import pytest

    with pytest.raises(ValueError):
        alerts_html([_alert("maybe", "m")])


def test_progress_marks_current_segment():
    html_text = progress_html(2)
    segments = re.findall(r'<span class="([^"]*)"></span>', html_text)
    assert segments == [
        "vp-progress-seg is-done",
        "vp-progress-seg is-current",
        "vp-progress-seg",
        "vp-progress-seg",
    ]
    assert "<strong>Step 2 of 4</strong>" in html_text
    assert "a few questions" in html_text


def test_progress_step_one_and_four():
    first = progress_html(1)
    first_segments = re.findall(r'<span class="([^"]*)"></span>', first)
    assert first_segments[0] == "vp-progress-seg is-current"
    assert "<strong>Step 1 of 4</strong>" in first
    assert "describe your symptoms" in first
    last = progress_html(4)
    last_segments = re.findall(r'<span class="([^"]*)"></span>', last)
    assert last_segments[3] == "vp-progress-seg is-current"
    assert last_segments[0] == "vp-progress-seg is-done"
    assert "<strong>Step 4 of 4</strong>" in last
    assert "your summary" in last


def test_rail_marks_current_step():
    html_text = rail_html(1)
    items = re.findall(r'<span class="([^"]*)"', html_text)
    assert items[0] == "vp-rail-item is-current"
    assert 'aria-current="step"' in html_text
    assert items[1] == "vp-rail-item"


def test_rail_uses_short_labels():
    html_text = rail_html(2)
    for label in ("Describe", "Questions", "Check details", "Your summary"):
        assert label in html_text
    assert "What's bothering you today?" not in html_text
    assert "Question 1 of 5" not in html_text


def test_rail_marks_current_step():
    html_text = rail_html(1)
    items = re.findall(r'<span class="([^"]*)"', html_text)
    assert items[0] == "vp-rail-item is-current"
    assert 'aria-current="step"' in html_text
    assert items[1] == "vp-rail-item"


def test_error_html_is_escaped_and_neutral():
    html_text = alerts_error_html("<b>Something went wrong</b>")
    assert "<b>" not in html_text
    assert "&lt;b&gt;Something went wrong&lt;/b&gt;" in html_text
    assert "urgent" not in html_text


def test_header_and_footer_text():
    header = header_html()
    assert "VisitPrep" in header
    assert 'href="#"' not in header
    footer = footer_html()
    assert "Leave out your name, address and phone number" in footer
    assert "VisitPrep doesn't diagnose, give medical advice or suggest treatment." in footer


# Step 4: visit note, script, questions


def _summary(doctor_card=None, script=None, questions=None):
    return {
        "doctor_card": doctor_card
        if doctor_card is not None
        else "Patient: 7 years old",
        "patient_script": (
            script if script is not None else "I am here about my son."
        ),
        "priority_questions": (
            [] if questions is None else list(questions)
        ),
    }


def test_note_date_formats_day_without_leading_zero():
    assert note_date(date(2026, 11, 3)) == "3 November 2026"
    assert note_date(date(2027, 1, 12)) == "12 January 2027"


def test_visit_note_html_escapes_doctor_card_text():
    payload = "<img src=x onerror=alert(1)>"
    html_text = visit_note_html(
        _summary(doctor_card=f"Problem: {payload}"), date(2026, 11, 3)
    )
    assert "<img" not in html_text
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_text


def test_script_html_escapes_the_script():
    payload = "<img src=x onerror=alert(1)>"
    html_text = script_html(_summary(script=payload))
    assert "<img" not in html_text
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_text


def test_questions_html_escapes_a_question():
    payload = "<img src=x onerror=alert(1)>"
    html_text = questions_html(_summary(questions=[payload]))
    assert "<img" not in html_text
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_text


def test_visit_note_html_contains_title_date_stamp_and_rows():
    html_text = visit_note_html(
        _summary(doctor_card="Patient: 7 years old\nProblem: a cough"),
        date(2026, 11, 3),
    )
    assert "Visit note" in html_text
    assert "For the doctor" in html_text
    assert "3 November 2026" in html_text
    assert 'class="vp-stamp"' in html_text
    assert 'class="vp-perforation"' in html_text
    assert "<strong>Patient:</strong> 7 years old" in html_text
    assert "Written by the patient with VisitPrep. Not a diagnosis." in html_text


def test_visit_note_html_splits_on_the_first_separator_only():
    html_text = visit_note_html(
        _summary(doctor_card='Severity: mild ("still playing")'),
        date(2027, 1, 12),
    )
    assert "<strong>Severity:</strong> mild (&quot;still playing&quot;)" in html_text


def test_visit_note_html_line_without_separator_is_shown_whole():
    html_text = visit_note_html(
        _summary(doctor_card="Allergies not mentioned"), date(2027, 1, 12)
    )
    assert "<strong>" not in html_text
    assert "Allergies not mentioned" in html_text


def test_read_time_seconds():
    assert read_time_seconds(" ".join(["word"] * 150)) == 60
    assert read_time_seconds(" ".join(["word"] * 35)) == 14
    assert read_time_seconds("") == 0


def test_script_html_has_heading_text_and_read_time():
    html_text = script_html(_summary())
    assert "What to say" in html_text
    assert '<p id="vp-script-text">' in html_text
    assert "seconds when read aloud" in html_text
    empty = script_html(_summary(script=""))
    assert "seconds when read aloud" not in empty
    assert '<p id="vp-script-text"></p>' in empty


def test_questions_html_two_questions_one_ol_two_li():
    html_text = questions_html(
        _summary(questions=["Should he stay home?", "When to come back?"])
    )
    assert "Questions to ask" in html_text
    assert html_text.count("<ol") == 1
    assert html_text.count("<li>") == 2


def test_questions_html_empty_returns_empty_string():
    assert questions_html(_summary(questions=[])) == ""


def test_preview_banner():
    banner = preview_banner_html()
    assert "vp-preview-banner" in banner
    assert (
        "Preview mode: example answers only. Nothing is sent to ModelScope."
        in banner
    )


def test_pips_first_question_current():
    html_text = pips_html(0, [], 1)
    classes = re.findall(r'<span class="([^"]+)"></span>', html_text)
    assert classes == [
        "vp-pip vp-pip-current",
        "vp-pip",
        "vp-pip",
        "vp-pip",
        "vp-pip",
    ]


def test_pips_answered_skipped_current_upcoming():
    html_text = pips_html(2, [2], 3)
    classes = re.findall(r'<span class="([^"]+)"></span>', html_text)
    assert classes == [
        "vp-pip vp-pip-answered",
        "vp-pip vp-pip-skipped",
        "vp-pip vp-pip-current",
        "vp-pip",
        "vp-pip",
    ]


def test_pips_all_answered_and_skipped():
    html_text = pips_html(3, [3, 4], 5)
    classes = re.findall(r'<span class="([^"]+)"></span>', html_text)
    assert classes == [
        "vp-pip vp-pip-answered",
        "vp-pip vp-pip-answered",
        "vp-pip vp-pip-skipped",
        "vp-pip vp-pip-skipped",
        "vp-pip vp-pip-current",
    ]


def test_pips_out_of_range_raises():
    import pytest

    with pytest.raises(ValueError):
        pips_html(0, [], 6)


def test_answers_list_escapes_question_and_answer():
    html_text = answers_list_html(
        [{"question": "<b>Q</b>", "answer": "A & B"}]
    )
    assert "<b>" not in html_text
    assert "&lt;b&gt;Q&lt;/b&gt;" in html_text
    assert "A &amp; B" in html_text


def test_answers_list_empty():
    html_text = answers_list_html([])
    assert "No answers yet." in html_text
    assert "vp-answer-question" not in html_text


def test_question_heading_html():
    assert (
        question_heading_html(3)
        == '<h2 class="vp-question-heading">Question 3 of 5</h2>'
    )
    import pytest

    with pytest.raises(ValueError):
        question_heading_html(0)
    with pytest.raises(ValueError):
        question_heading_html(6)


def test_question_text_html_escapes_and_is_empty_when_blank():
    assert question_text_html("") == ""
    html_text = question_text_html("<i>Feel</i> worse?")
    assert "vp-question-text" in html_text
    assert "&lt;i&gt;Feel&lt;/i&gt; worse?" in html_text


def test_alerts_error_message_text():
    assert (
        ALERTS_ERROR_MESSAGE
        == "We could not check your answers for warning signs. "
        "If you feel very unwell, call 119."
    )


def _blank_record(**overrides) -> dict:
    record = {
        "complaint": None,
        "symptoms": [],
        "onset": None,
        "duration": None,
        "severity": None,
        "severity_note": None,
        "medicines": [],
        "medicines_denied": None,
        "allergies": [],
        "allergies_denied": None,
        "medical_history": [],
        "medical_history_denied": None,
        "concerns": [],
        "patient_age": None,
        "patient_age_text": None,
        "patient_sex": None,
        "reporting_on_behalf": None,
        "reporter_relationship": None,
    }
    record.update(overrides)
    return record


def test_detail_rows_cover_the_seven_sections_in_order():
    assert [section for section, _label in DETAIL_ROWS] == [
        "problem",
        "timing",
        "medicines",
        "allergies",
        "history",
        "concerns",
        "about",
    ]


def test_detail_row_escapes_patient_text_in_every_field():
    payload = "<img src=x onerror=alert(1)>"
    record = _blank_record(
        complaint=payload,
        symptoms=[payload],
        onset=payload,
        duration="a & b",
        severity="moderate",
        severity_note=payload,
        medicines=[{"name": payload, "frequency": payload}],
        allergies=[payload],
        medical_history=[payload],
        concerns=[payload],
        patient_age=34,
        patient_age_text=payload,
        patient_sex="female",
    )
    for section in [s for s, _l in DETAIL_ROWS]:
        html_text = detail_row_html(record, section)
        assert "<img" not in html_text
        assert "&lt;img src=x onerror=alert(1)&gt;" in html_text


def test_detail_row_shows_not_given_for_unknown_values():
    record = _blank_record()
    for section, _label in DETAIL_ROWS:
        html_text = detail_row_html(record, section)
        assert "Not given" in html_text
        assert 'class="vp-not-given"' in html_text


def test_detail_row_denied_list_shows_none_confirmed():
    record = _blank_record(
        medicines_denied=True,
        allergies_denied=True,
        medical_history_denied=True,
    )
    for section in ("medicines", "allergies", "history"):
        html_text = detail_row_html(record, section)
        assert "None (you confirmed)" in html_text
        assert "Not given" not in html_text


def test_detail_row_medicines_name_and_frequency():
    record = _blank_record(
        medicines=[
            {"name": "ginger tea", "frequency": "twice a day"},
            {"name": "honey", "frequency": None},
        ]
    )
    html_text = detail_row_html(record, "medicines")
    assert "ginger tea, twice a day" in html_text
    assert ">honey<" in html_text


def test_detail_row_severity_level_and_note_in_quotes():
    record = _blank_record(
        severity="mild", severity_note="He is still playing and eating."
    )
    html_text = detail_row_html(record, "timing")
    assert 'mild "He is still playing and eating."' in html_text
    assert "Started:" in html_text
    assert "How long:" in html_text
    assert "How bad:" in html_text


def test_detail_row_about_reported_by_only_when_on_behalf():
    on_behalf = _blank_record(
        reporting_on_behalf=True, reporter_relationship="mother"
    )
    assert "Reported by: mother" in detail_row_html(on_behalf, "about")

    not_on_behalf = _blank_record(
        reporting_on_behalf=False, reporter_relationship="mother"
    )
    assert "Reported by:" not in detail_row_html(not_on_behalf, "about")

    no_relationship = _blank_record(reporting_on_behalf=True)
    assert "Reported by:" not in detail_row_html(no_relationship, "about")


def test_detail_row_age_from_number_when_no_text():
    record = _blank_record(patient_age=7)
    html_text = detail_row_html(record, "about")
    assert ">7<" in html_text


def test_detail_row_unknown_section_raises():
    import pytest

    with pytest.raises(ValueError):
        detail_row_html(_blank_record(), "nope")


def test_change_label_add_when_blank_change_when_known():
    blank = _blank_record()
    for section, _label in DETAIL_ROWS:
        assert change_label(blank, section) == "Add"
    assert change_label(
        _blank_record(complaint="a mild cough"), "problem"
    ) == "Change"
    assert change_label(
        _blank_record(allergies_denied=True), "allergies"
    ) == "Change"
    assert change_label(
        _blank_record(patient_age=7), "about"
    ) == "Change"
