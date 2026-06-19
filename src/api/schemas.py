from pydantic import BaseModel
from models.job import JobStatus
from typing import List


class StageConfig(BaseModel):
    """Configuración de una etapa del pipeline.

    ``name`` es un string libre que identifica la operación.
    Debe coincidir con el nombre con que se registró la chain
    (ej: "extract", "analyze", "detect_faces", etc.).
    """
    name: str


class DocumentMetadata(BaseModel):
    name: str
    type: str
    content: str


class PipelineConfig(BaseModel):
    """Configuración completa del pipeline LLM."""
    stages: List[StageConfig]
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1"


class JobCreate(BaseModel):
    document: DocumentMetadata
    pipelineconfig: PipelineConfig


class JobResponse(BaseModel):
    id: int
    status: JobStatus
    config: PipelineConfig
    result: dict | None = None
    model_config = {"from_attributes": True}

