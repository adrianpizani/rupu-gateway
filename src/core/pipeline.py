from models.job import Job, JobStatus
from core.job_service import update_job_status, update_job_content
from providers.analyzers import get_analyzer
from providers.enrichers import get_enricher
from providers.extractors import get_extractor
from models.database import SessionLocal
import asyncio
from messaging.publisher import EventPublisher

MAX_RETRIES = 3
INITIAL_BACKOFF = 2

events = EventPublisher(queues=["events"])

async def process_doc(job_id: str):
    """
    Main pipeline executor. Runs the document through the configured stages
    and handles transient failures using exponential backoff.
    """
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return

        update_job_status(job, JobStatus.PROCESSING, db)

        try:
            data_to_process = job.config['doc']['content']

            for task in job.config['config']['stages']:
                for attempt in range(MAX_RETRIES):
                    try:
                        current_task = get_factory(task)

                        events.publish_event('job.stage_started', str(job.id), {'stage': task}, "events")
                        data_to_process = await current_task.process(data_to_process)
                        events.publish_event('job.stage_completed', str(job.id), {'result': data_to_process}, "events")

                        update_job_content(job, data_to_process, db)
                        break

                    except Exception as e:
                        if attempt == MAX_RETRIES - 1:
                            raise e
                        
                        wait_time = INITIAL_BACKOFF ** attempt
                        await asyncio.sleep(wait_time)
                        
            update_job_status(job, JobStatus.COMPLETED, db)

        except Exception as e:
            update_job_status(job, JobStatus.FAILED, db)
            update_job_content(job, str(e), db)


def get_factory(task):
    """
    Simple factory to grab the right provider instance for a given stage.
    """
    if isinstance(task, str):
        task = {'name': task, 'provider': 'default'}
        
    task_name = task.get('name')
    provider_name = task.get('provider', 'default')

    if task_name == 'extract':
        return get_extractor(provider_name)
    if task_name == 'analyze':
        return get_analyzer(provider_name)
    if task_name == 'enrich':
        return get_enricher(provider_name)
    
    raise ValueError(f"Unknown pipeline stage: {task_name}")


