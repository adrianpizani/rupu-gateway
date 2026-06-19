import pytest
import time
import requests
from models.database import SessionLocal
from models.job import Job, JobStatus

def test_full_pipeline_e2e():
    # 1. Enviar job a la API
    # Asumimos que la API corre en localhost:8000 o dentro del contenedor
    # Para el test desde fuera usamos localhost
    api_url = "http://localhost:8000/jobs"
    payload = {
        "document": {
            "name": "e2e_test.txt",
            "type": "text/plain",
            "content": "Contenido para procesar"
        },
        "pipelineconfig": {
            "stages": [{"name": "extract"}]
        }
    }
    
    response = requests.post(api_url, json=payload)
    assert response.status_code == 200
    job_id = response.json()["id"]
    
    # 2. Esperar a que el worker lo procese (damos 5 segundos de margen)
    # Consultamos la DB directamente para ver el cambio
    db = SessionLocal()
    max_retries = 10
    finished = False
    
    try:
        for _ in range(max_retries):
            db.expire_all() # Limpiamos cache de SQLAlchemy
            job = db.get(Job, job_id)
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                finished = True
                break
            time.sleep(1)
            
        assert finished, f"El job {job_id} no terminó a tiempo (status actual: {job.status})"
        assert job.status == JobStatus.COMPLETED, f"El job falló: {job.result}"
        
    finally:
        db.close()
