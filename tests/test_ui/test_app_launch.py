"""Tests for the launch settings in app.py.

No network and no API key are needed: these check the values that
launch_kwargs() passes to demo.launch(), and scan the app.py source
for hard-coded tokens.
"""

import re
from pathlib import Path

import app

import ui.theme


def test_launch_kwargs_privacy_and_gradio(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    kwargs = app.launch_kwargs()
    assert kwargs["run_history"] is False
    assert kwargs["footer_links"] == []
    assert kwargs["show_error"] is False
    assert kwargs["server_name"] == "0.0.0.0"
    assert kwargs["css"] is ui.theme.THEME_CSS
    assert kwargs["head"] is ui.theme.THEME_HEAD


def test_launch_kwargs_default_port(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    kwargs = app.launch_kwargs()
    assert kwargs["server_port"] == 7860
    assert isinstance(kwargs["server_port"], int)


def test_launch_kwargs_reads_port_when_called(monkeypatch):
    monkeypatch.setenv("PORT", "7861")
    kwargs = app.launch_kwargs()
    assert kwargs["server_port"] == 7861


def test_app_source_has_no_hardcoded_tokens():
    source = Path(app.__file__).resolve().read_text(encoding="utf-8")
    assert not re.search(r"ms-[0-9a-f]{8}", source)
    assert "MODELSCOPE_API_KEY=" not in source
