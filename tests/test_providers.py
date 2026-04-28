import pytest
import asyncio
import time
from providers.extractors import get_extractor, FastExtractorProvider, SlowExtractorProvider
from providers.analyzers import AnalyzerProvider
from providers.enrichers import EnricherProvider

@pytest.mark.asyncio
async def test_fast_extractor_latency():
    extractor = get_extractor("fast")
    start_time = time.time()
    result = await extractor.process("Contenido de prueba")
    duration = time.time() - start_time
    
    assert "FAST EXTRACTED" in result
    assert 0.1 <= duration < 0.5  # Debería tardar ~0.1s

@pytest.mark.asyncio
async def test_slow_extractor_latency():
    extractor = get_extractor("slow")
    start_time = time.time()
    result = await extractor.process("Contenido de prueba")
    duration = time.time() - start_time
    
    assert "SLOW EXTRACTED" in result
    assert duration >= 2.0  # Debería tardar al menos 2s

def test_extractor_factory():
    assert isinstance(get_extractor("fast"), FastExtractorProvider)
    assert isinstance(get_extractor("slow"), SlowExtractorProvider)
    with pytest.raises(ValueError):
        get_extractor("unknown")

@pytest.mark.asyncio
async def test_analyzer_provider():
    analyzer = AnalyzerProvider()
    result = await analyzer.process("Texto extraído")
    assert "ANALYZED" in result

@pytest.mark.asyncio
async def test_enricher_provider():
    enricher = EnricherProvider()
    result = await enricher.process("Entidades detectadas")
    assert "ENRICHED" in result
