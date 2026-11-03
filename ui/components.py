"""Pure HTML-building functions for the VisitPrep UI.

Every function returns an escaped HTML string. There is no business
logic here: alerts come from core.redflag, questions from core.interview
and summaries from core.summarize. These functions only render the data
they are given. No gradio imports.
"""

import html
from datetime import date

# Step headings (h1) shown inside each step.
STEP_NAMES = (
    "What's bothering you today?",
    "Question 1 of 5",
    "Is this right?",
    "Your visit note is ready",
)

# Labels for the "Step N of 4, <label>" line.
STEP_LABELS = (
    "describe your symptoms",
    "a few questions",
    "check your details",
    "your summary",
)

# Labels for the desktop progress rail.
RAIL_LABELS = (
    "Describe",
    "Questions",
    "Check details",
    "Your summary",
)

_URGENT = "urgent"
_ATTENTION = "attention"


def header_html() -> str:
    """Header bar content: the brand only (the Start over button is
    a real Gradio button in the layout)."""
    return '<span class="vp-brand">VisitPrep</span>'


def note_date(prepared_on: date) -> str:
    """Format a date as '3 November 2026' (no leading zero day)."""
    return f"{prepared_on.day} {prepared_on.strftime('%B')} {prepared_on.year}"


def _note_row(line: str) -> str:
    """One doctor card line: bold label before the first ': ', else whole."""
    if ": " in line:
        label, value = line.split(": ", 1)
        return (
            '<div class="vp-note-row">'
            f"<strong>{html.escape(label, quote=True)}:</strong> "
            f"{html.escape(value, quote=True)}</div>"
        )
    return f'<div class="vp-note-row">{html.escape(line, quote=True)}</div>'


def visit_note_html(summary: dict, prepared_on: date) -> str:
    """The visit note slip: title with date, stamp, rows, helper line."""
    rows = []
    for line in str(summary["doctor_card"]).splitlines():
        if line.strip():
            rows.append(_note_row(line.strip()))
    return (
        '<div class="vp-note">'
        '<div class="vp-note-head">'
        '<h2 class="vp-note-title">Visit note</h2>'
        f'<span class="vp-note-date">{note_date(prepared_on)}</span>'
        "</div>"
        '<span class="vp-stamp">For the doctor</span>'
        '<div class="vp-perforation"></div>'
        + "".join(rows)
        + '<p class="vp-helper">Written by the patient with VisitPrep. '
        "Not a diagnosis.</p>"
        "</div>"
    )


def read_time_seconds(script: str) -> int:
    """Whole seconds to read the script aloud at 150 words per minute."""
    return round(len(str(script).split()) / 150 * 60)


def script_html(summary: dict) -> str:
    """The 'What to say' script with its read time when not empty."""
    script = str(summary["patient_script"])
    parts = [
        '<h2 class="vp-script-heading">What to say</h2>',
        f'<p id="vp-script-text">{html.escape(script, quote=True)}</p>',
    ]
    seconds = read_time_seconds(script)
    if seconds > 0:
        parts.append(
            f'<p class="vp-helper">About {seconds} seconds when read aloud</p>'
        )
    return "".join(parts)


def questions_html(summary: dict) -> str:
    """The 'Questions to ask' list; empty string when there are none."""
    questions = list(summary["priority_questions"])
    if not questions:
        return ""
    items = "".join(
        f"<li>{html.escape(str(question), quote=True)}</li>"
        for question in questions
    )
    return (
        '<h2 class="vp-questions-heading">Questions to ask</h2>'
        f'<ol class="vp-questions">{items}</ol>'
    )


def progress_html(step: int) -> str:
    """'Step N of 4, <label>' line plus a 4-segment progress bar.

    "Step N of 4" is bold and the label comes from STEP_LABELS. The
    segment for the given step is marked current; earlier segments are
    marked done.
    """
    if not 1 <= step <= len(STEP_NAMES):
        raise ValueError(f"step must be 1..{len(STEP_NAMES)}, got {step!r}")
    label = STEP_LABELS[step - 1]
    total = len(STEP_NAMES)
    title = f"Step {step} of {total}, {label}"
    segments = []
    for index in range(1, total + 1):
        if index < step:
            classes = "vp-progress-seg is-done"
        elif index == step:
            classes = "vp-progress-seg is-current"
        else:
            classes = "vp-progress-seg"
        segments.append(f'<span class="{classes}"></span>')
    return (
        '<div class="vp-step">'
        f'<p class="vp-step-title"><strong>Step {step} of {total}</strong>, '
        f"{html.escape(label)}</p>"
        '<div class="vp-progress" role="progressbar" '
        f'aria-valuemin="1" aria-valuemax="{total}" '
        f'aria-valuenow="{step}" aria-label="{html.escape(title)}">'
        + "".join(segments)
        + "</div>"
        "</div>"
    )


def rail_html(step: int) -> str:
    """Desktop progress rail: the four steps, the current one marked.

    Rail items use the short RAIL_LABELS names.
    """
    if not 1 <= step <= len(STEP_NAMES):
        raise ValueError(f"step must be 1..{len(STEP_NAMES)}, got {step!r}")
    items = []
    for index, name in enumerate(RAIL_LABELS, start=1):
        escaped = html.escape(name)
        if index == step:
            items.append(
                f'<span class="vp-rail-item is-current" '
                f'aria-current="step">{escaped}</span>'
            )
        else:
            items.append(f'<span class="vp-rail-item">{escaped}</span>')
    return (
        '<nav class="vp-rail-nav" aria-label="Steps">'
        + "".join(items)
        + "</nav>"
    )


def alerts_html(alerts: list) -> str:
    """Care cards for the given alerts.

    Each alert must expose .level ("urgent" or "attention") and
    .message (str). Always returns the vp-alerts container: when there
    are no alerts it is empty (no visible text) and never says "no
    alerts" or "you are safe".
    """
    cards = []
    has_urgent = False
    for alert in alerts:
        level = str(alert.level).strip().lower()
        message = html.escape(str(alert.message), quote=True)
        if level == _URGENT:
            has_urgent = True
            cards.append(
                '<div class="vp-card vp-card-urgent">'
                '<div class="vp-card-band vp-band-urgent">'
                '<h2 class="vp-card-heading"><span class="vp-sr-only">'
                "Urgent advice:</span> Get medical help now</h2>"
                "</div>"
                f'<div class="vp-card-body"><p>{message}</p>'
                '<a class="vp-btn vp-btn-call" href="tel:119">Call 119</a>'
                "</div>"
                "</div>"
            )
        elif level == _ATTENTION:
            cards.append(
                '<div class="vp-card vp-card-attention">'
                '<div class="vp-card-band vp-band-attention">'
                '<h2 class="vp-card-heading"><span class="vp-sr-only">'
                "Attention:</span> Tell your doctor about this</h2>"
                "</div>"
                f'<div class="vp-card-body"><p>{message}</p></div>'
                "</div>"
            )
        else:
            raise ValueError(f"Unknown alert level: {alert.level!r}")
    if not cards:
        return '<div class="vp-alerts vp-alerts-empty" aria-live="polite"></div>'
    container_attrs = ' role="alert"' if has_urgent else ' aria-live="polite"'
    return f'<div class="vp-alerts"{container_attrs}>' + "".join(cards) + "</div>"


def alerts_error_html(message: str) -> str:
    """Error card for a failed core call. Never uses urgent red."""
    return (
        '<div class="vp-error" role="alert">'
        f"<p>{html.escape(str(message), quote=True)}</p>"
        "</div>"
    )


def footer_html() -> str:
    """Footer: privacy note, then the no-advice statement."""
    return (
        '<footer class="vp-footer">'
        "<p>Before you type: your notes are sent to ModelScope to be "
        "organized. Leave out your name, address and phone number. The "
        "provider doesn't promise to delete them, and closing this tab "
        "doesn't delete them right away.</p>"
        "<p>VisitPrep doesn't diagnose, give medical advice or suggest "
        "treatment.</p>"
        "</footer>"
    )


def preview_banner_html() -> str:
    """Small banner marking a preview build."""
    return (
        '<div class="vp-preview-banner">'
        "Preview mode: example answers only. Nothing is sent to ModelScope."
        "</div>"
    )


# Message shown in the alert area when the core alert check fails.
ALERTS_ERROR_MESSAGE = (
    "We could not check your answers for warning signs. "
    "If you feel very unwell, call 119."
)

# The interview has five questions, shown as five pips.
QUESTION_COUNT = 5


def pips_html(answered: int, skipped_positions: list[int], current: int) -> str:
    """The five question pips.

    Answered pips are filled with --vp-primary, skipped pips have a
    dashed border, the current pip is --vp-tint with a --vp-primary
    border and upcoming pips are empty with the input border colour.
    Every question before the current one is answered or skipped.
    """
    if not 1 <= current <= QUESTION_COUNT:
        raise ValueError(f"current must be 1..{QUESTION_COUNT}, got {current!r}")
    skipped = set(skipped_positions)
    pips = []
    for position in range(1, QUESTION_COUNT + 1):
        if position in skipped:
            classes = "vp-pip vp-pip-skipped"
        elif position < current:
            classes = "vp-pip vp-pip-answered"
        elif position == current:
            classes = "vp-pip vp-pip-current"
        else:
            classes = "vp-pip"
        pips.append(f'<span class="{classes}"></span>')
    label = html.escape(
        f"{answered} of {QUESTION_COUNT} questions answered"
    )
    return (
        f'<div class="vp-pips" role="img" aria-label="{label}">'
        + "".join(pips)
        + "</div>"
    )


def question_heading_html(n: int) -> str:
    """'Question N of 5' heading for the step 2 question."""
    if not 1 <= n <= QUESTION_COUNT:
        raise ValueError(f"n must be 1..{QUESTION_COUNT}, got {n!r}")
    return f'<h2 class="vp-question-heading">Question {n} of {QUESTION_COUNT}</h2>'


def question_text_html(text: str) -> str:
    """The question text at 23px bold, escaped; empty when no text."""
    if not text:
        return ""
    return f'<p class="vp-question-text">{html.escape(str(text), quote=True)}</p>'


# The seven review sections in page order, with their row labels.
DETAIL_ROWS = (
    ("problem", "Main problem"),
    ("timing", "When and how bad"),
    ("medicines", "Medicines"),
    ("allergies", "Allergies"),
    ("history", "Medical history"),
    ("concerns", "Your questions and worries"),
    ("about", "About the patient"),
)

_DETAIL_LABELS = dict(DETAIL_ROWS)

_NOT_GIVEN = '<span class="vp-not-given">Not given</span>'
_DENIED = "None (you confirmed)"


def _detail_value(value: str | None) -> str:
    if value is None:
        return _NOT_GIVEN
    return html.escape(str(value), quote=True)


def _detail_line(content: str) -> str:
    return f'<p class="vp-detail-line">{content}</p>'


def _items_line(items: list) -> str:
    if items:
        return "".join(
            _detail_line(html.escape(str(item), quote=True)) for item in items
        )
    return _detail_line(_NOT_GIVEN)


def detail_row_html(record: dict, section: str) -> str:
    """The section label and its values, escaped.

    An unknown value shows "Not given"; a list whose *_denied flag is
    true shows "None (you confirmed)".
    """
    label = _DETAIL_LABELS.get(section)
    if label is None:
        raise ValueError(f"Unknown detail section: {section!r}")
    lines: list[str] = []
    if section == "problem":
        lines.append(_detail_line(_detail_value(record.get("complaint"))))
        lines.append(_items_line(record.get("symptoms") or []))
    elif section == "timing":
        lines.append(
            _detail_line(
                '<span class="vp-detail-sub">Started:</span> '
                + _detail_value(record.get("onset"))
            )
        )
        lines.append(
            _detail_line(
                '<span class="vp-detail-sub">How long:</span> '
                + _detail_value(record.get("duration"))
            )
        )
        severity = record.get("severity")
        note = record.get("severity_note")
        if severity is None:
            severity_html = _NOT_GIVEN
        elif note:
            severity_html = (
                html.escape(str(severity), quote=True)
                + ' "'
                + html.escape(str(note), quote=True)
                + '"'
            )
        else:
            severity_html = html.escape(str(severity), quote=True)
        lines.append(
            _detail_line(
                '<span class="vp-detail-sub">How bad:</span> ' + severity_html
            )
        )
    elif section == "medicines":
        if record.get("medicines_denied") is True:
            lines.append(_detail_line(_DENIED))
        else:
            medicines = record.get("medicines") or []
            if medicines:
                for medicine in medicines:
                    name = html.escape(str(medicine.get("name")), quote=True)
                    frequency = medicine.get("frequency")
                    if frequency:
                        lines.append(
                            _detail_line(
                                name
                                + ", "
                                + html.escape(str(frequency), quote=True)
                            )
                        )
                    else:
                        lines.append(_detail_line(name))
            else:
                lines.append(_detail_line(_NOT_GIVEN))
    elif section in ("allergies", "history"):
        key = "allergies" if section == "allergies" else "medical_history"
        if record.get(key + "_denied") is True:
            lines.append(_detail_line(_DENIED))
        else:
            lines.append(_items_line(record.get(key) or []))
    elif section == "concerns":
        lines.append(_items_line(record.get("concerns") or []))
    elif section == "about":
        age_text = record.get("patient_age_text")
        age = record.get("patient_age")
        shown_age = age_text if age_text else (str(age) if age is not None else None)
        lines.append(_detail_line(_detail_value(shown_age)))
        lines.append(_detail_line(_detail_value(record.get("patient_sex"))))
        if record.get("reporting_on_behalf") is True:
            relationship = record.get("reporter_relationship")
            if relationship:
                lines.append(
                    _detail_line(
                        "Reported by: "
                        + html.escape(str(relationship), quote=True)
                    )
                )
    return (
        '<div class="vp-detail-row">'
        f'<p class="vp-detail-label">{html.escape(label)}</p>'
        + "".join(lines)
        + "</div>"
    )


def change_label(record: dict, section: str) -> str:
    """'Add' when the whole section is unknown, 'Change' otherwise."""
    label = _DETAIL_LABELS.get(section)
    if label is None:
        raise ValueError(f"Unknown detail section: {section!r}")
    if section == "problem":
        blank = record.get("complaint") is None and not record.get("symptoms")
    elif section == "timing":
        blank = (
            record.get("onset") is None
            and record.get("duration") is None
            and record.get("severity") is None
            and record.get("severity_note") is None
        )
    elif section == "medicines":
        blank = (
            not record.get("medicines") and record.get("medicines_denied") is None
        )
    elif section == "allergies":
        blank = (
            not record.get("allergies") and record.get("allergies_denied") is None
        )
    elif section == "history":
        blank = (
            not record.get("medical_history")
            and record.get("medical_history_denied") is None
        )
    elif section == "concerns":
        blank = not record.get("concerns")
    elif section == "about":
        blank = (
            record.get("patient_age") is None
            and record.get("patient_age_text") is None
            and record.get("patient_sex") is None
            and not (
                record.get("reporting_on_behalf") is True
                and record.get("reporter_relationship")
            )
        )
    else:
        blank = False
    return "Add" if blank else "Change"


def answers_list_html(asked: list) -> str:
    """The answered questions with the patient's answers, escaped.

    Each entry of asked is a dict with "question" and "answer".
    """
    items = []
    for qa in asked:
        question = html.escape(str(qa["question"]), quote=True)
        answer = html.escape(str(qa["answer"]), quote=True)
        items.append(
            '<div class="vp-answer">'
            f'<p class="vp-answer-question">{question}</p>'
            f'<p class="vp-answer-text">{answer}</p>'
            "</div>"
        )
    if not items:
        return (
            '<div class="vp-answers">'
            '<p class="vp-answers-none">No answers yet.</p>'
            "</div>"
        )
    return '<div class="vp-answers">' + "".join(items) + "</div>"
