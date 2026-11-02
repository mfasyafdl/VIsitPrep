"""Pure HTML-building functions for the VisitPrep UI.

Every function returns an escaped HTML string. There is no business
logic here: alerts come from core.redflag, questions from core.interview
and summaries from core.summarize. These functions only render the data
they are given. No gradio imports.
"""

import html

# Placeholder step names for the static shell, used by the "Step N of 4"
# line, the progress bar and the desktop rail.
STEP_NAMES = (
    "What's bothering you today?",
    "Question 1 of 5",
    "Is this right?",
    "Your visit note is ready",
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
    """'Step N of 4, <step name>' line plus a 4-segment progress bar.

    The segment for the given step is marked current; earlier segments
    are marked done.
    """
    if not 1 <= step <= len(STEP_NAMES):
        raise ValueError(f"step must be 1..{len(STEP_NAMES)}, got {step!r}")
    title = f"Step {step} of {len(STEP_NAMES)}, {STEP_NAMES[step - 1]}"
    segments = []
    for index in range(1, len(STEP_NAMES) + 1):
        if index < step:
            classes = "vp-progress-seg is-done"
        elif index == step:
            classes = "vp-progress-seg is-current"
        else:
            classes = "vp-progress-seg"
        segments.append(f'<span class="{classes}"></span>')
    return (
        '<div class="vp-step">'
        f'<p class="vp-step-title">{html.escape(title)}</p>'
        '<div class="vp-progress" role="progressbar" '
        f'aria-valuemin="1" aria-valuemax="{len(STEP_NAMES)}" '
        f'aria-valuenow="{step}" aria-label="{html.escape(title)}">'
        + "".join(segments)
        + "</div>"
        "</div>"
    )


def rail_html(step: int) -> str:
    """Desktop progress rail: the four steps, the current one marked."""
    if not 1 <= step <= len(STEP_NAMES):
        raise ValueError(f"step must be 1..{len(STEP_NAMES)}, got {step!r}")
    items = []
    for index, name in enumerate(STEP_NAMES, start=1):
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
    .message (str). Returns "" when there are no alerts: the alert area
    shows nothing and never says "no alerts" or "you are safe".
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
                '<span class="vp-sr-only">Urgent advice:</span>'
                '<p class="vp-card-heading">Get medical help now</p>'
                "</div>"
                f'<div class="vp-card-body"><p>{message}</p></div>'
                '<a class="vp-btn vp-btn-link" href="tel:119">Call 119</a>'
                "</div>"
            )
        elif level == _ATTENTION:
            cards.append(
                '<div class="vp-card vp-card-attention">'
                '<div class="vp-card-band vp-band-attention">'
                '<span class="vp-sr-only">Attention:</span>'
                '<p class="vp-card-heading">Tell your doctor about this</p>'
                "</div>"
                f'<div class="vp-card-body"><p>{message}</p></div>'
                "</div>"
            )
        else:
            raise ValueError(f"Unknown alert level: {alert.level!r}")
    if not cards:
        return ""
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
    """Small banner marking a preview build. Copy to be confirmed."""
    return '<div class="vp-preview-banner">Preview</div>'
