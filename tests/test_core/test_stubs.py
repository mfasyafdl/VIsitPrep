"""Tests for the core interface stubs (task P1-1b)."""

import pytest

from core import llm, summarize
from core.schema import empty_record

STUB_CALLS = [
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
