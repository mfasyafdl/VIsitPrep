"""Tests for scripts/make_zip.py and scripts/extract_prompt.py (tasks P1-7a and P1-7a-FIX-1)."""

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_zip = _load("make_zip_under_test", "make_zip.py")
extract_prompt = _load("extract_prompt_under_test", "extract_prompt.py")


def test_select_files_keeps_env_example_and_drops_excluded():
    paths = [
        ".env",
        ".env.example",
        ".env.local",
        "dist/x.zip",
        "a/b.pdf",
        "core/__pycache__/x.pyc",
        ".pytest_cache/x",
        "README.md",
        "core/llm.py",
    ]
    assert make_zip.select_files(paths) == [".env.example", "README.md", "core/llm.py"]


def test_find_secrets_flags_key_like_lines():
    key = "ms-" + "ab3-" * 6
    env = "MODELSCOPE_API_KEY=" + "notAFakeValue" + "123"
    text = "clean line\n" + key + "\n" + env + "\n"
    assert make_zip.find_secrets(text) == [2, 3]


def test_find_secrets_ignores_known_fake_values():
    for value in sorted(make_zip.KNOWN_FAKE_VALUES):
        plain = "MODELSCOPE_API_KEY=" + value
        quoted = "MODELSCOPE_API_KEY=\"" + value + "\""
        assert make_zip.find_secrets(plain + "\n") == []
        assert make_zip.find_secrets(quoted + "\n") == []


def test_find_secrets_flags_real_value_among_fakes():
    fake = "sk-file-key"
    line = (
        "MODELSCOPE_API_KEY=\"" + fake + "\" "
        "MODELSCOPE_API_KEY=" + "notAFakeValue" + "123"
    )
    assert make_zip.find_secrets(line) == [1]


def test_find_secrets_ignores_clean_lines():
    text = "MODELSCOPE_API_KEY=\nitems-abcdefghijklmnopqrstuvwxyz\n"
    assert make_zip.find_secrets(text) == []


def test_prompt_block_returns_section(tmp_path):
    log = tmp_path / "log.md"
    log.write_text(
        "# log\n"
        "\n"
        "## A-1\n"
        "\n"
        "Model: Qwen/Qwen3.8-27B\n"
        "\n"
        "Prompt (verbatim):\n"
        "\n"
        "```\n"
        "line one\n"
        "a line with ``` in the middle\n"
        "line three\n"
        "```\n"
        "\n"
        "## A-2\n"
        "\n"
        "```\n"
        "other block\n"
        "```\n",
        encoding="utf-8",
    )
    assert extract_prompt.prompt_block(log, "A-1") == (
        "line one\na line with ``` in the middle\nline three"
    )
    assert extract_prompt.prompt_block(log, "A-2") == "other block"


def test_prompt_block_honours_four_backtick_fence(tmp_path):
    log = tmp_path / "log.md"
    log.write_text(
        "# log\n"
        "\n"
        "## B-1\n"
        "\n"
        "Model: Qwen/Qwen3.8-27B\n"
        "\n"
        "Prompt (verbatim):\n"
        "\n"
        "````\n"
        "first line\n"
        "```\n"
        "last line\n"
        "````\n",
        encoding="utf-8",
    )
    assert extract_prompt.prompt_block(log, "B-1") == "first line\n```\nlast line"
