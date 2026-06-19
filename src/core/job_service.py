from models.job import Job,JobStatus
from sqlalchemy.orm import Session
from api.schemas import JobCreate, JobResponse
from sqlalchemy import JSON
from messaging.publisher import EventPublisher
from fastapi import HTTPException
from typing import List

VALID_STATUS = {
    JobStatus.PENDING : [JobStatus.PROCESSING, JobStatus.CANCELLED],
    JobStatus.PROCESSING : [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.COMPLETED : [],
    JobStatus.FAILED : [],
    JobStatus.CANCELLED : []
}

JOB_EVENTS = {
   JobStatus.COMPLETED : "job.completed",
   JobStatus.CANCELLED : "job.cancelled",
   JobStatus.FAILED : "job.failed",
   JobStatus.PROCESSING: "job.processing"
}

events = EventPublisher(queues=["events", "tasks"])


def update_job_status(job: Job, new_status: JobStatus, db_session: Session) -> Job:
    """Safely updates the job status, preventing invalid state transitions."""
    if new_status in VALID_STATUS[job.status]:
        job.status = new_status
        db_session.commit()
        db_session.refresh(job)
        events.publish_event(JOB_EVENTS.get(new_status, "job.status_updated"), job.id, job.config, "events")
        return job
    raise ValueError("Trying to update to a not valid status")

def update_job_content(job: Job, new_content: JSON, db_session: Session) -> Job:
    """Updates the partial result/content of a job."""
    if new_content:
        job.result = new_content
        db_session.commit()
        db_session.refresh(job)
        events.publish_event('job.content_updated', job.id, job.config, "events")
        return job
    raise ValueError("Invalid content to update")

def create_job(job_data: JobCreate, db: Session) -> JobResponse:
    """Drops a new job in the DB and pings the worker via RabbitMQ."""
    try:
        # Keep the raw document and pipeline config in the DB
        job = Job(config={
            'config': job_data.pipelineconfig.model_dump(), 
            'doc': job_data.document.model_dump()
        })
        db.add(job)
        db.commit()
        db.refresh(job)
        events.publish_event('job.created', job.id, job.config, "tasks")
        return job
    except Exception:
        raise HTTPException(status_code=400, detil="Couldn't create job with specific data")
    
def get_job(job_id: str, db: Session) -> Job:
    """Retrieves a single job by ID."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job doesn't exist")
    return job

def get_jobs(status: JobStatus, db: Session) -> List[Job]:
    """Retrieves all jobs, optionally filtering by status."""
    jobs = db.query(Job)
    if status:
        jobs = jobs.filter(Job.status==status)
    return jobs.all()
    
def cancel_job(job_id: str, db: Session):
    """Cancels an existing job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job doesn't exist")
    
    try:
        return update_job_status(job, JobStatus.CANCELLED, db)
    except ValueError:
        raise HTTPException(status_code=400, detail="Couldn't cancel job, invalid new status")
