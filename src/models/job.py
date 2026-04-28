import enum
from sqlalchemy import Column, Integer, Enum, JSON
from models.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    config = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)