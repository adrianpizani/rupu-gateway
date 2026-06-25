# -*- coding: utf-8 -*-
"""Tests del ChainRegistry y carga de chains.

Verifica que el registry:
- Tiene las 3 chains registradas después de importar ``src.llm.chains``.
- Permite registrar chains nuevas en runtime.
- Devuelve instancias con el LLM inyectado.
- Falla con mensaje útil cuando se pide una chain inexistente.
- Se puede limpiar (útil para tests aislados).
"""
import pytest

from src.llm.chains.base import BaseLLMChain
from src.llm.chains.registry import ChainRegistry


class _DummyChain(BaseLLMChain):
    """Chain mínima para tests: solo guarda el LLM."""

    async def process(self, data: str) -> str:
        return f"dummy:{data}"


class TestChainRegistryBuiltin:
    """Verifica que el módulo registra las 3 chains por side-effect."""

    def test_registry_has_three_builtin_chains(self):
        chains = set(ChainRegistry.list_chains())
        assert {"extract", "analyze", "enrich"}.issubset(chains)

    def test_list_chains_returns_strings(self):
        names = ChainRegistry.list_chains()
        assert all(isinstance(n, str) for n in names)
        assert len(names) >= 3

    def test_get_chain_returns_instance_with_llm(self):
        llm = object()  # sentinel: cualquier objeto sirve como llm
        instance = ChainRegistry.get_chain("extract", llm)
        assert isinstance(instance, BaseLLMChain)
        assert instance.llm is llm


class TestChainRegistryRuntime:
    """Verifica que se pueden registrar chains nuevas en runtime."""

    def setup_method(self):
        # Snapshot del estado para restaurar al final del test
        self._snapshot = dict(ChainRegistry._chains)

    def teardown_method(self):
        ChainRegistry._chains.clear()
        ChainRegistry._chains.update(self._snapshot)

    def test_register_adds_chain(self):
        ChainRegistry.register("dummy-test")(  # noqa: PD009
            _DummyChain
        )
        assert "dummy-test" in ChainRegistry.list_chains()
        instance = ChainRegistry.get_chain("dummy-test", object())
        assert isinstance(instance, _DummyChain)

    def test_register_overwrites_existing(self):
        @ChainRegistry.register("dummy-test")
        class FirstChain(BaseLLMChain):
            async def process(self, data: str) -> str:
                return "first"

        @ChainRegistry.register("dummy-test")
        class SecondChain(BaseLLMChain):
            async def process(self, data: str) -> str:
                return "second"

        # La segunda registración pisa a la primera
        assert ChainRegistry.get_chain("dummy-test", object()).__class__ is SecondChain


class TestChainRegistryErrors:
    """Verifica los caminos de error."""

    def test_get_unknown_chain_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            ChainRegistry.get_chain("no-existe-este-stage", object())
        # El mensaje debe listar las chains disponibles
        msg = str(exc_info.value)
        assert "no-existe-este-stage" in msg
        assert "extract" in msg  # debe mencionar alguna chain disponible

    def test_clear_empties_registry(self):
        ChainRegistry.clear()
        assert ChainRegistry.list_chains() == []
