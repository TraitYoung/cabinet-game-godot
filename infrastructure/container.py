"""Per-application dependencies plus a scoped accessor for graph nodes.

The compatibility getters resolve the active application, so graph/prompt code
can stay small without sharing model, mood or database instances between apps.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from typing import Any

from config.settings import Settings


class dependency:
    """Lazy dependency with per-container locking; tests may explicitly replace it."""

    def __init__(self, factory):
        self.factory = factory

    def __get__(self, instance, owner):
        if instance is None:
            return self
        with instance._lock:
            name = self.factory.__name__
            if name not in instance.__dict__:
                instance.__dict__[name] = self.factory(instance)
            return instance.__dict__[name]


class Container:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings
        self._lock = RLock()

    @property
    def settings(self) -> Settings:
        with self._lock:
            if self._settings is None:
                self._settings = Settings.load()
            return self._settings

    @dependency
    def history(self):
        from storage.chat_history import ChatHistory

        return ChatHistory(self.settings.db_path)

    @dependency
    def mood(self):
        from state.mood_engine import MoodEngine

        return MoodEngine(self.settings.db_path, settings=self.settings)

    @dependency
    def memory(self):
        from memory.hindsight import HindsightMemory

        return HindsightMemory(settings=self.settings)

    @dependency
    def llm(self):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(**_chat_openai_kwargs(self.settings, self.settings.chat_model))

    @dependency
    def requests(self):
        from storage.turn_requests import TurnRequests

        return TurnRequests(self.settings.db_path)

    @dependency
    def turns(self):
        from modules.chat_api.service import TurnService

        return TurnService(container=self)

    @dependency
    def proactive(self):
        from agents.proactive import ProactiveAgent

        return ProactiveAgent(self)


_active: ContextVar[Container | None] = ContextVar("bina_container", default=None)
_default: Container | None = None


def get_container() -> Container:
    current = _active.get()
    if current is not None:
        return current
    global _default
    if _default is None:
        _default = Container()
    return _default


@contextmanager
def use_container(container: Container):
    token = _active.set(container)
    try:
        yield container
    finally:
        _active.reset(token)


def get_settings() -> Settings:
    return get_container().settings


def _chat_openai_kwargs(settings: Settings, model: str) -> dict[str, Any]:
    qwen = settings.llm_provider == "qwen"
    kwargs: dict[str, Any] = {
        "model": model,
        "api_key": (settings.qwen_api_key if qwen else settings.deepseek_api_key).get_secret_value()
        or "missing-key-will-fail-on-invoke",
        "base_url": settings.qwen_base_url if qwen else settings.deepseek_base_url,
    }
    if not qwen:
        kwargs["extra_body"] = {"thinking": {"type": "enabled" if settings.deepseek_thinking else "disabled"}}
    return kwargs


def get_llm_provider() -> str:
    return get_settings().llm_provider


def get_chat_model() -> str:
    return get_settings().chat_model


def get_chat_options() -> dict[str, Any]:
    settings = get_settings()
    models = [settings.chat_model] + (
        ["deepseek-flash", "deepseek-v4-pro"] if settings.llm_provider == "deepseek" else []
    )
    return {
        "provider": settings.llm_provider,
        "default_model": settings.chat_model,
        "models": list(dict.fromkeys(models)),
        "reasoning_levels": ["off", "low", "high", "max"] if settings.llm_provider == "deepseek" else [],
    }


def get_turn_llm(model: str | None = None, reasoning_effort: str | None = None):
    if model is None and reasoning_effort is None:
        return get_llm()
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    kwargs = _chat_openai_kwargs(settings, model or settings.chat_model)
    if settings.llm_provider == "deepseek" and reasoning_effort is not None:
        kwargs["extra_body"] = {"thinking": {"type": "disabled" if reasoning_effort == "off" else "enabled"}}
        if reasoning_effort != "off":
            kwargs["extra_body"]["reasoning_effort"] = reasoning_effort
    return ChatOpenAI(**kwargs)


def get_llm():
    return get_container().llm


def get_chat_history():
    return get_container().history


def get_mood_engine():
    return get_container().mood


def get_db_path() -> str:
    return get_settings().db_path


def get_deepseek_search_credentials() -> tuple[str, str]:
    settings = get_settings()
    return settings.deepseek_api_key.get_secret_value(), settings.deepseek_base_url
