from src.core.config import settings
from src.llm.base import LLMProvider
from src.llm.gemini import GeminiProvider

_PROVIDERS: dict[str, type] = {
    "gemini": GeminiProvider,
}

_instance_cache: dict[str, LLMProvider] = {}


def get_provider() -> LLMProvider:
    """Get the configured LLM provider instance. Cached after first call."""
    name = settings.llm_provider
    if name not in _instance_cache:
        if name not in _PROVIDERS:
            raise ValueError(
                f"Unknown LLM provider: '{name}'. Available: {list(_PROVIDERS.keys())}"
            )
        _instance_cache[name] = _PROVIDERS[name]()
    return _instance_cache[name]


def register_provider(name: str, provider_class: type) -> None:
    """Register a new provider class. For testing and extension."""
    _PROVIDERS[name] = provider_class


def clear_cache() -> None:
    """Clear the instance cache. For testing."""
    _instance_cache.clear()
