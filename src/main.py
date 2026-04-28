from fastapi import FastAPI, Depends
from models.database import Base, engine, get_db
from models.job import Job, JobStatus
from api.schemas import JobCreate
from core.job_service import create_job, get_job, cancel_job, get_jobs
from sqlalchemy.orm import Session
from core.pipeline import process_doc

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/jobs")
def post_job(job_data: JobCreate, db: Session = Depends(get_db)):
    job = create_job(job_data, db)
    return job

@app.get("/jobs/{job_id}")
def get_a_job(job_id: str, db: Session = Depends(get_db)):
    job = get_job(job_id, db)
    return job

@app.get("/jobs")
def get_all_jobs(status: JobStatus | None = None, db: Session = Depends(get_db)):
    jobs = get_jobs(status, db)
    return jobs

@app.delete("/jobs/{job_id}", status_code=204)
def cancel_a_job(job_id: str, db: Session = Depends(get_db)):
    cancel_job(job_id, db)