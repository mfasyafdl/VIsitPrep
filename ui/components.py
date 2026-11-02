"""Pure HTML-building functions for the VisitPrep UI.

Every function returns an escaped HTML string. There is no business
logic here: alerts come from core.redflag, questions from core.interview
and summaries from core.summarize. These functions only render the data
they are given. No gradio imports.
"""

import html

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
    """Header bar: brand on the left, Start over link on the right."""
    return (
        '<header class="vp-header">'
        '<span class="vp-brand">VisitPrep</span>'
        '<a class="vp-btn vp-btn-link" href="#">Start over</a>'
        "</header>"
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
