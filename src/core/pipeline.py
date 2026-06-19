"""
Pipeline de procesamiento con LangChain.

Ejecuta las etapas configuradas usando chains de LangChain.
Cada etapa se resuelve por nombre desde el ChainRegistry.
"""
import asyncio
from models.job import Job, JobStatus
from core.job_service import update_job_status, update_job_content
from models.database import SessionLocal
from messaging.publisher import EventPublisher
from src.llm.chains.registry import ChainRegistry
from src.llm.providers.factory import LLMFactory
from src.llm.providers.models import LLMConfig

MAX_RETRIES = 3
INITIAL_BACKOFF = 2

events = EventPublisher(queues=["events"])


def build_llm_config(config: dict) -> LLMConfig:
    """Construye un LLMConfig desde la configuración del job."""
    return LLMConfig(
        provider=config.get("llm_provider", "ollama"),
        model=config.get("llm_model", "llama3.1"),
        temperature=0.0,
        max_tokens=4096,
    )


async def process_doc(job_id: str):
    """
    Ejecuta el pipeline: para cada stage en la config del job,
    resuelve la chain desde el Registry y la ejecuta con el LLM.
    """
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return

        update_job_status(job, JobStatus.PROCESSING, db)

        try:
            pipeline_config = job.config.get("config", {})
            data_to_process = job.config["doc"]["content"]

            # Instanciar el LLM una sola vez para todo el pipeline
            llm_config = build_llm_config(pipeline_config)
            llm = LLMFactory.get_llm(llm_config)

            stages = pipeline_config.get("stages", [])

            for stage in stages:
                # stage puede venir como string o como dict con "name"
                stage_name = stage if isinstance(stage, str) else stage.get("name", "")

                for attempt in range(MAX_RETRIES):
                    try:
                        # Resolver la chain desde el Registry
                        chain = ChainRegistry.get_chain(stage_name, llm)

                        events.publish_event(
                            "job.stage_started", str(job.id),
                            {"stage": stage_name}, "events"
                        )
                        data_to_process = await chain.process(data_to_process)
                        events.publish_event(
                            "job.stage_completed", str(job.id),
                            {"stage": stage_name, "result": data_to_process}, "events"
                        )

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


