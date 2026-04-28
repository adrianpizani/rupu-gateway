from pydantic import BaseModel
from models.job import JobStatus
from typing import List
import enum

class Stages(str, enum.Enum):
    EXTRACT = "extract"
    ANALYZE = "analyze"
    ENRICH = "enrich"

class DocumentMetadata(BaseModel):
    name: str
    type: str
    content: str

class PipelineConfig(BaseModel):
    stages : List[Stages]

class JobCreate(BaseModel):
    document: DocumentMetadata
    pipelineconfig: PipelineConfig

class JobResponse(BaseModel):
    id: int
    status: JobStatus
    config: PipelineConfig
    result: dict | None = None
    model_config = {"from_attributes": True}

