import pytest
from models.job import Job, JobStatus
from core.job_service import update_job_status, create_job
from api.schemas import JobCreate, DocumentMetadata, PipelineConfig, StageConfig

def test_create_job_service(db):
    # Mock de datos de entrada
    job_data = JobCreate(
        document=DocumentMetadata(name="test.pdf", type="pdf", content="base64content"),
        pipelineconfig=PipelineConfig(stages=[StageConfig(name="extract")])
    )
    
    # Ejecutar creación
    job = create_job(job_data, db)
    
    assert job.id is not None
    assert job.status == JobStatus.PENDING
    assert job.config["config"]["stages"] == [{"name": "extract"}]

def test_valid_status_transition(db):
    # Crear un job inicial
    job = Job(status=JobStatus.PENDING, config={})
    db.add(job)
    db.commit()
    
    # Transición válida: PENDING -> PROCESSING
    updated_job = update_job_status(job, JobStatus.PROCESSING, db)
    assert updated_job.status == JobStatus.PROCESSING

def test_invalid_status_transition(db):
    # Crear un job en estado COMPLETED
    job = Job(status=JobStatus.COMPLETED, config={})
    db.add(job)
    db.commit()
    
    # Intento de transición inválida: COMPLETED -> PROCESSING
    with pytest.raises(ValueError, match="Trying to update to a not valid status"):
        update_job_status(job, JobStatus.PROCESSING, db)
