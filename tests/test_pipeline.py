"""
Tests del pipeline de procesamiento con LangChain.

Se mockean el ChainRegistry y LLMFactory para evitar
dependencia con LLMs reales durante los tests.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from core.pipeline import process_doc
from models.job import Job, JobStatus


@pytest.fixture
def mock_db_session():
    with patch("core.pipeline.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        yield mock_session


@pytest.mark.asyncio
async def test_process_doc_success(mock_db_session):
    job_id = "123"
    job_config = {
        "config": {
            "stages": [{"name": "extract"}, {"name": "analyze"}],
            "llm_provider": "ollama",
            "llm_model": "llama3.1",
        },
        "doc": {"content": "texto original"},
    }
    test_job = Job(id=job_id, status=JobStatus.PENDING, config=job_config, result=None)
    mock_db_session.get.return_value = test_job

    # Mock de una chain: responde cualquier cosa que le manden
    mock_chain = AsyncMock()
    mock_chain.process.return_value = "texto procesado"

    # Importante: parcheamos get_chain con un Mock (no con return_value=),
    # porque necesitamos inspeccionar .call_count / assert_any_call sobre
    # el mock en sí, no sobre la chain.
    with patch("core.pipeline.ChainRegistry.get_chain") as mock_get_chain, \
         patch("core.pipeline.LLMFactory.get_llm") as mock_llm_factory:
        mock_get_chain.return_value = mock_chain
        await process_doc(job_id)

    assert test_job.status == JobStatus.COMPLETED
    assert test_job.result == "texto procesado"
    # Verificar que se invocó el registry con los nombres correctos
    assert mock_get_chain.call_count == 2  # extract + analyze
    mock_get_chain.assert_any_call("extract", mock_llm_factory.return_value)
    mock_get_chain.assert_any_call("analyze", mock_llm_factory.return_value)


@pytest.mark.asyncio
async def test_process_doc_failure(mock_db_session):
    job_id = "456"
    job_config = {
        "config": {
            "stages": [{"name": "extract"}],
            "llm_provider": "ollama",
        },
        "doc": {"content": "texto original"},
    }
    test_job = Job(id=job_id, status=JobStatus.PENDING, config=job_config, result=None)
    mock_db_session.get.return_value = test_job

    mock_chain = MagicMock()
    mock_chain.process.side_effect = Exception("Fallo simulado")

    with patch("core.pipeline.ChainRegistry.get_chain", return_value=mock_chain), \
         patch("core.pipeline.LLMFactory.get_llm"):

        await process_doc(job_id)

    assert test_job.status == JobStatus.FAILED
    assert "Fallo simulado" in test_job.result
