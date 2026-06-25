# -*- coding: utf-8 -*-
"""Tests del LLMFactory (caché de instancias por provider:model).

Verifica que:
- La misma ``provider:model`` devuelve la misma instancia (caché).
- Distinto provider o modelo crea instancias separadas.
- ``clear_cache()`` resetea el caché.
- El mocking del provider real (ChatOpenAI/ChatOllama/etc.) evita
  conexiones de red durante los tests.

Nota: ``ChatOpenAI``/``ChatAnthropic``/``ChatOllama`` se importan de
forma diferida dentro de ``get_llm()``, así que parcheamos el módulo
del provider (``langchain_openai``, ``langchain_anthropic``,
``langchain_ollama``) en lugar de ``src.llm.providers.models``.
"""
from unittest.mock import patch

from src.llm.providers.factory import LLMFactory
from src.llm.providers.models import LLMConfig, LLMProvider


class TestLLMFactoryCache:
    """El caché es por combinación provider:model."""

    def setup_method(self):
        LLMFactory.clear_cache()

    def teardown_method(self):
        LLMFactory.clear_cache()

    def test_same_provider_model_returns_same_instance(self):
        config = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3.1")

        with patch("langchain_ollama.ChatOllama") as mock_cls:
            mock_cls.return_value = "sentinel-instance"
            a = LLMFactory.get_llm(config)
            b = LLMFactory.get_llm(config)

        assert a == b == "sentinel-instance"
        # ChatOllama se construye una sola vez (caché funcionando)
        assert mock_cls.call_count == 1

    def test_different_model_creates_separate_instance(self):
        cfg_a = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3.1")
        cfg_b = LLMConfig(provider=LLMProvider.OLLAMA, model="qwen2.5")

        with patch("langchain_ollama.ChatOllama") as mock_cls:
            mock_cls.side_effect = ["inst-llama", "inst-qwen"]
            a = LLMFactory.get_llm(cfg_a)
            b = LLMFactory.get_llm(cfg_b)

        assert a == "inst-llama"
        assert b == "inst-qwen"
        assert mock_cls.call_count == 2

    def test_different_provider_creates_separate_instance(self):
        cfg_openai = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test"
        )
        cfg_ollama = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3.1")

        with patch("langchain_openai.ChatOpenAI") as mock_openai, \
             patch("langchain_ollama.ChatOllama") as mock_ollama:
            mock_openai.return_value = "openai-inst"
            mock_ollama.return_value = "ollama-inst"
            a = LLMFactory.get_llm(cfg_openai)
            b = LLMFactory.get_llm(cfg_ollama)

        assert a == "openai-inst"
        assert b == "ollama-inst"


class TestLLMFactoryClearCache:
    def setup_method(self):
        LLMFactory.clear_cache()

    def teardown_method(self):
        LLMFactory.clear_cache()

    def test_clear_cache_resets_instances(self):
        config = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3.1")

        with patch("langchain_ollama.ChatOllama") as mock_cls:
            mock_cls.side_effect = ["first", "second"]
            a = LLMFactory.get_llm(config)
            assert a == "first"

            LLMFactory.clear_cache()
            b = LLMFactory.get_llm(config)
            assert b == "second"

        assert mock_cls.call_count == 2