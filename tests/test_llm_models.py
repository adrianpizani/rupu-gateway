# -*- coding: utf-8 -*-
"""Tests de ``LLMConfig`` y la función ``get_llm()`` con cada provider.

Mockeamos ``ChatOpenAI`` / ``ChatAnthropic`` / ``ChatOllama`` desde los
módulos originales (``langchain_openai``, ``langchain_anthropic``,
``langchain_ollama``) porque ``get_llm`` los importa de forma diferida.
"""
from unittest.mock import patch

from src.llm.providers.models import (
    LLMConfig,
    LLMProvider,
    get_llm,
)


class TestLLMConfig:
    def test_defaults_are_valid(self):
        cfg = LLMConfig()
        assert cfg.provider == LLMProvider.OLLAMA
        assert cfg.model == "llama3.1"
        assert cfg.temperature == 0.0
        assert cfg.max_tokens == 4096
        assert cfg.api_key is None
        assert cfg.base_url is None

    def test_provider_is_serializable_string(self):
        # LLMProvider(str, Enum) → se serializa como su valor string.
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.OLLAMA == "ollama"  # str mixin

    def test_overrides_work(self):
        cfg = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2048,
            api_key="sk-test",
            base_url="https://api.example.com/v1",
        )
        assert cfg.provider == LLMProvider.OPENAI
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 2048
        assert cfg.api_key == "sk-test"
        assert cfg.base_url == "https://api.example.com/v1"


class TestGetLLMRouting:
    """``get_llm`` debe enrutar al provider correcto y pasarle los kwargs."""

    def test_openai_routes_to_chat_openai(self):
        cfg = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            temperature=0.5,
            max_tokens=1024,
            api_key="sk-test",
            base_url="https://api.example.com/v1",
        )
        with patch("langchain_openai.ChatOpenAI") as mock_cls:
            mock_cls.return_value = "openai-instance"
            instance = get_llm(cfg)

        assert instance == "openai-instance"
        mock_cls.assert_called_once_with(
            model="gpt-4o",
            temperature=0.5,
            max_tokens=1024,
            api_key="sk-test",
            base_url="https://api.example.com/v1",
        )

    def test_anthropic_routes_to_chat_anthropic(self):
        cfg = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet",
            api_key="sk-ant",
        )
        with patch("langchain_anthropic.ChatAnthropic") as mock_cls:
            mock_cls.return_value = "anthropic-instance"
            instance = get_llm(cfg)

        assert instance == "anthropic-instance"
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-5-sonnet"
        assert call_kwargs["api_key"] == "sk-ant"

    def test_ollama_uses_localhost_default_base_url(self):
        cfg = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3.1")
        with patch("langchain_ollama.ChatOllama") as mock_cls:
            mock_cls.return_value = "ollama-instance"
            instance = get_llm(cfg)

        assert instance == "ollama-instance"
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["model"] == "llama3.1"
        assert call_kwargs["base_url"] == "http://localhost:11434"
        # num_predict viene de max_tokens
        assert call_kwargs["num_predict"] == cfg.max_tokens

    def test_ollama_respects_explicit_base_url(self):
        cfg = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="llama3.1",
            base_url="http://remote-ollama:11434",
        )
        with patch("langchain_ollama.ChatOllama") as mock_cls:
            get_llm(cfg)
        assert (
            mock_cls.call_args.kwargs["base_url"] == "http://remote-ollama:11434"
        )