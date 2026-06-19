import pytest
from unittest.mock import patch, MagicMock

def test_api_create_job(client, db):
    payload = {
        "document": {
            "name": "challenge.pdf",
            "type": "application/pdf",
            "content": "lorem ipsum"
        },
        "pipelineconfig": {
            "stages": [{"name": "extract"}, {"name": "analyze"}]
        }
    }

    # Parcheamos SessionLocal dentro del pipeline para que use la sesión de test
    with patch("core.pipeline.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = db

        response = client.post("/jobs", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert "id" in data
    assert data["config"]["config"]["stages"] == [{"name": "extract"}, {"name": "analyze"}]

def test_api_create_job_invalid_data(client):
    # Payload incompleto (falta el documento)
    payload = {
        "pipelineconfig": {
            "stages": ["extract"]
        }
    }
    
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
