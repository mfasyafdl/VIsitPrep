"""Tests for the core interface stubs (task P1-1b)."""

import pytest

from core import extract, interview, llm, redflag, summarize
from core.schema import empty_record

STUB_CALLS = [
    pytest.param(lambda: redflag.scan_text("a short story"), id="redflag.scan_text"),
    pytest.param(
        lambda: redflag.check_alerts(empty_record()), id="redflag.check_alerts"
    ),
    pytest.param(
        lambda: extract.extract_record("a short story"), id="extract.extract_record"
    ),
    pytest.param(
        lambda: interview.merge_answers(empty_record(), []),
        id="interview.merge_answers",
    ),
    pytest.param(
        lambda: summarize.generate_summary(empty_record(), []),
        id="summarize.generate_summary",
    ),
]


@pytest.mark.parametrize("call", STUB_CALLS)
def test_stub_raises_not_implemented(call):
    with pytest.raises(NotImplementedError):
        call()


def test_every_error_class_is_a_subclass_of_llm_error():
    for cls in (
        llm.ConfigError,
        llm.LLMAuthError,
        llm.LLMQuotaError,
        llm.LLMNetworkError,
        llm.LLMServerError,
        llm.LLMResponseError,
        llm.LLMContentFilterError,
    ):
        assert issubclass(cls, llm.LLMError)
