"""LLM client interface: defines LLMConfig, the LLMError hierarchy (ConfigError, LLMAuthError, LLMQuotaError, LLMNetworkError, LLMServerError, LLMResponseError, LLMContentFilterError) and the stubs load_config() and chat_json() with the exact signatures from docs/data_contract.md; no logic is implemented yet."""

import dataclasses
from typing import Callable


@dataclasses.dataclass
class LLMConfig:
    api_key: str
    model: str
    base_url: str


class LLMError(Exception):
    """Base error for all LLM failures in core.llm."""


class ConfigError(LLMError):
    """The LLM configuration is missing or invalid."""


class LLMAuthError(LLMError):
    """The provider rejected the API key."""


class LLMQuotaError(LLMError):
    """The provider quota or rate limit was reached."""


class LLMNetworkError(LLMError):
    """The network request to the provider failed."""


class LLMServerError(LLMError):
    """The provider server returned a server error."""


class LLMResponseError(LLMError):
    """The provider response is not usable JSON data."""


class LLMContentFilterError(LLMError):
    """The provider's content filter rejected the text."""


def load_config() -> LLMConfig:
    raise NotImplementedError("load_config is not implemented yet")


def chat_json(
    system: str,
    user: str,
    *,
    validate: Callable[[dict], list[str]],
    config: LLMConfig | None = None,
    max_tokens: int = 4000,
    timeout: float = 120.0,
    max_retries: int = 2,
    max_repairs: int = 1,
) -> dict:
    raise NotImplementedError("chat_json is not implemented yet")
