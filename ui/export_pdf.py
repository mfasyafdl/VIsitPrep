"""Build the printable visit note PDF.

Takes the plain dicts the UI keeps (summary and alerts) and renders one A4
PDF with fpdf2. No gradio, no business logic, no state: every value is
passed in as an argument and the inputs are never mutated.
"""

import shutil
import tempfile
import time
from datetime import date
from pathlib import Path

from fpdf import FPDF

FONT_PATH = (
    Path(__file__).parent / "assets" / "fonts" / "AtkinsonHyperlegibleNext-wght.ttf"
)
PDF_NAME = "visitprep-visit-note.pdf"

_TEXT = (21, 35, 42)  # #15232A
_ACCENT = (11, 107, 96)  # #0B6B60
_URGENT_BG = (196, 43, 28)  # #C42B1C
_ATTENTION_BG = (255, 216, 77)  # #FFD84D
_WHITE = (255, 255, 255)

_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class _NotePdf(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("AHN", "", 9)
        self.set_text_color(*_TEXT)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} of {self.str_alias_nb_pages}"
            " \u00b7 VisitPrep \u00b7 not a diagnosis",
            align="C",
        )


def note_date(d: date) -> str:
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}"


def new_session_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="visitprep_"))


def _ensure_space(pdf: _NotePdf, height: float) -> None:
    if pdf.get_y() + height > pdf.h - pdf.b_margin:
        pdf.add_page()


def _body(pdf: _NotePdf, text: str) -> None:
    pdf.set_text_color(*_TEXT)
    pdf.set_font("AHN", "", 11)
    pdf.multi_cell(0, 5.5, text, new_x="LMARGIN", new_y="NEXT")


def _heading(pdf: _NotePdf, text: str) -> None:
    pdf.set_text_color(*_TEXT)
    pdf.set_font("AHN", "B", 13)
    pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")


def build_pdf(
    summary: dict,
    alerts: list[dict],
    out_dir,
    *,
    prepared_on: date | None = None,
) -> Path:
    if prepared_on is None:
        prepared_on = date.today()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / PDF_NAME

    pdf = _NotePdf(format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, 15)
    pdf.add_font("AHN", "", str(FONT_PATH), variations={"wght": 400})
    pdf.add_font("AHN", "B", str(FONT_PATH), variations={"wght": 700})
    pdf.set_text_color(*_TEXT)
    pdf.add_page()

    pdf.set_fill_color(*_ACCENT)
    pdf.rect(0, 0, pdf.w, 2, "F")

    pdf.set_font("AHN", "B", 16)
    pdf.multi_cell(0, 6, "Visit note", new_x="LMARGIN", new_y="NEXT")
    _body(pdf, note_date(prepared_on))
    _body(pdf, "Prepared from patient-reported information. Not a diagnosis.")
    pdf.ln(3)

    urgent = [a for a in alerts if a.get("level") == "urgent"]
    attention = [a for a in alerts if a.get("level") == "attention"]
    for alert in urgent + attention:
        if alert.get("level") == "urgent":
            band, label, text_color = _URGENT_BG, "Get medical help now", _WHITE
        else:
            band, label, text_color = (
                _ATTENTION_BG,
                "Tell your doctor about this",
                _TEXT,
            )
        _ensure_space(pdf, 13)
        pdf.set_fill_color(*band)
        pdf.set_text_color(*text_color)
        pdf.set_font("AHN", "B", 11)
        pdf.cell(pdf.epw, 7, label, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        _body(pdf, alert.get("message", ""))
        pdf.ln(2)

    pdf.ln(2)
    _heading(pdf, "For the doctor")
    pdf.ln(1)
    for line in str(summary.get("doctor_card", "")).splitlines():
        line = line.rstrip()
        if not line:
            continue
        _ensure_space(pdf, 6)
        parts = line.split(": ", 1)
        if len(parts) == 2:
            pdf.set_text_color(*_TEXT)
            pdf.set_font("AHN", "B", 11)
            pdf.write(6, parts[0] + ": ")
            pdf.set_font("AHN", "", 11)
            pdf.write(6, parts[1])
            pdf.ln(6)
        else:
            _body(pdf, line)
    pdf.ln(3)

    _heading(pdf, "What to say")
    pdf.ln(1)
    _body(pdf, str(summary.get("patient_script", "")))
    pdf.ln(3)

    questions = list(summary.get("priority_questions") or [])
    if questions:
        _heading(pdf, "Questions to ask")
        pdf.ln(1)
        for i, question in enumerate(questions, 1):
            _ensure_space(pdf, 6)
            _body(pdf, f"{i}. {question}")
        pdf.ln(2)

    pdf.output(str(out_path))
    return out_path


def remove_pdf(path) -> None:
    if path is None:
        return
    path = Path(path)
    if path.exists():
        path.unlink()
    folder = path.parent
    if folder.name.startswith("visitprep_"):
        try:
            folder.rmdir()
        except OSError:
            pass


def cleanup_old_exports(root=None, max_age_minutes: float = 60) -> int:
    base = Path(root) if root is not None else Path(tempfile.gettempdir())
    if not base.is_dir():
        return 0
    cutoff = time.time() - max_age_minutes * 60
    deleted = 0
    for entry in base.iterdir():
        try:
            if not entry.is_dir() or not entry.name.startswith("visitprep_"):
                continue
            if entry.stat().st_mtime < cutoff:
                shutil.rmtree(entry)
                deleted += 1
        except OSError:
            continue
    return deleted
