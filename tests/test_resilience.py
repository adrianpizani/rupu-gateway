import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from core.pipeline import process_doc
from models.job import Job, JobStatus
from models.database import SessionLocal

@pytest.mark.asyncio
async def test_pipeline_retry_mechanism():
    """Verifica que el pipeline reintenta una tarea antes de fallar."""
    job_id = 1
    mock_job = MagicMock(spec=Job)
    mock_job.id = job_id
    mock_job.status = JobStatus.PENDING
    mock_job.config = {
        'doc': {'content': 'test content'},
        'config': {'stages': [{'name': 'extract', 'provider': 'fail'}]}
    }

    # Mock de la base de datos
    with patch('core.pipeline.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_db.get.return_value = mock_job

        # Mock de los servicios de actualización
        with patch('core.pipeline.update_job_status') as mock_status, \
             patch('core.pipeline.update_job_content') as mock_content, \
             patch('core.pipeline.get_extractor') as mock_get_extractor, \
             patch('core.pipeline.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

            # Configuramos el extractor para que falle siempre
            mock_extractor = AsyncMock()
            mock_extractor.process.side_effect = Exception("Temporary Failure")
            mock_get_extractor.return_value = mock_extractor

            # Ejecutamos el proceso
            await process_doc(job_id)

            # VERIFICACIONES:
            # 1. El extractor debe haberse llamado 3 veces (MAX_RETRIES)
            assert mock_extractor.process.call_count == 3
            
            # 2. El sleep debe haberse llamado 2 veces (entre intentos)
            assert mock_sleep.call_count == 2
            
            # 3. El estado final debe ser FAILED
            # Buscamos la última llamada a update_job_status
            last_status_call = mock_status.call_args_list[-1]
            assert last_status_call[0][1] == JobStatus.FAILED
