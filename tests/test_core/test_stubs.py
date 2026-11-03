"""Tests for the core error classes (task P1-1b; the stub tests were removed when the last stub was implemented in P1-6)."""

from core import llm


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
