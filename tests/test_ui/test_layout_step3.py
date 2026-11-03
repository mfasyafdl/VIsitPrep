"""Tests for the step 3 editor field updates in ui/layout.py.

These test the pure helper _editor_field_values, so no browser is
needed. The record is a neutral fictional fixture.
"""

import gradio as gr

from core import fixtures
from core.schema import record_to_dict

from ui import layout
from ui.state import new_state


def _step3_state(record=None, merged=True, editing=None, error=None):
    state = new_state()
    state["step"] = 3
    state["merged"] = merged
    state["editing"] = editing
    state["error"] = error
    if record is None:
        record = fixtures.get_fixture("fever_adult")
    state["record"] = record_to_dict(record)
    return state


def test_open_editor_without_error_gets_record_values():
    state = _step3_state(editing="medicines")
    updates = layout._editor_field_values(state, "medicines")
    assert updates == [
        gr.update(value="ginger tea, twice a day"),
        gr.update(value=False),
    ]


def test_open_editor_with_error_keeps_typed_values():
    state = _step3_state(
        editing="allergies",
        error="Remove the items, or untick the box.",
    )
    updates = layout._editor_field_values(state, "allergies")
    assert len(updates) == len(layout.EDITOR_FIELDS["allergies"])
    for update in updates:
        assert update == gr.update()
        assert "value" not in update


def test_closed_editor_gets_record_values_even_with_error():
    state = _step3_state(editing="allergies", error="Remove the items, or untick the box.")
    updates = layout._editor_field_values(state, "medicines")
    assert updates == [
        gr.update(value="ginger tea, twice a day"),
        gr.update(value=False),
    ]


def test_error_freezes_only_the_open_editor():
    state = _step3_state(
        editing="problem",
        error="This could not be saved. Please check what you typed.",
    )
    open_editor = layout._editor_field_values(state, "problem")
    assert open_editor == [gr.update(), gr.update()]
    closed_editor = layout._editor_field_values(state, "about")
    assert closed_editor == [
        gr.update(value="34"),
        gr.update(value="female"),
    ]


def test_unmerged_editor_gets_empty_placeholders():
    state = _step3_state(merged=False)
    assert layout._editor_field_values(state, "about") == [
        gr.update(value=""),
        gr.update(value=None),
    ]
    assert layout._editor_field_values(state, "timing") == [
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=None),
    ]
