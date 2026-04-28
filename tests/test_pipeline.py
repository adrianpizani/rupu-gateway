import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from core.pipeline import process_doc
from models.job import Job, JobStatus
from models.database import SessionLocal

@pytest.fixture
def mock_db_session():
    with patch("core.pipeline.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        yield mock_session

@pytest.mark.asyncio
async def test_process_doc_success(mock_db_session):
    job_id = "123"
    # Estructura REAL: config tiene 'config' (con stages) y 'doc' (con content)
    job_config = {
        "config": {
            "stages": [
                {"name": "extract", "provider": "fast"},
                {"name": "analyze", "provider": "default"}
            ]
        },
        "doc": {
            "content": "texto original"
        }
    }
    test_job = Job(id=job_id, status=JobStatus.PENDING, config=job_config, result=None)
    mock_db_session.get.return_value = test_job

    mock_extractor = AsyncMock()
    mock_extractor.process.return_value = "texto extraido"
    
    mock_analyzer = AsyncMock()
    mock_analyzer.process.return_value = "texto analizado"

    with patch("core.pipeline.get_extractor", return_value=mock_extractor), \
         patch("core.pipeline.get_analyzer", return_value=mock_analyzer):
        
        await process_doc(job_id)

    assert test_job.status == JobStatus.COMPLETED
    assert test_job.result == "texto analizado"

@pytest.mark.asyncio
async def test_process_doc_failure(mock_db_session):
    job_id = "456"
    # Estructura REAL incluso para el fallo
    job_config = {
        "config": {"stages": [{"name": "extract", "provider": "fail"}]},
        "doc": {"content": "texto original"}
    }
    test_job = Job(id=job_id, status=JobStatus.PENDING, config=job_config, result=None)
    mock_db_session.get.return_value = test_job

    mock_extractor = MagicMock()
    mock_extractor.process.side_effect = Exception("Fallo simulado")

    with patch("core.pipeline.get_extractor", return_value=mock_extractor):
        await process_doc(job_id)

    assert test_job.status == JobStatus.FAILED
    assert "Fallo simulado" in test_job.result
