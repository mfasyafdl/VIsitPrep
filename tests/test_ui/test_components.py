"""Tests for the pure HTML functions in ui/components.py."""

import re
from types import SimpleNamespace

from ui.components import (
    alerts_error_html,
    alerts_html,
    footer_html,
    header_html,
    preview_banner_html,
    progress_html,
    rail_html,
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
    assert "Start over" in header
    footer = footer_html()
    assert "Leave out your name, address and phone number" in footer
    assert "VisitPrep doesn't diagnose, give medical advice or suggest treatment." in footer


def test_preview_banner():
    banner = preview_banner_html()
    assert "vp-preview-banner" in banner
    assert (
        "Preview mode: example answers only. Nothing is sent to ModelScope."
        in banner
    )
