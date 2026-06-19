import grpc
from concurrent import futures
import gateway_pb2
import gateway_pb2_grpc
from core.job_service import create_job, get_job
from api.schemas import JobCreate, DocumentMetadata, PipelineConfig, StageConfig
from models.database import SessionLocal
import json

class JobGatewayService(gateway_pb2_grpc.JobGatewayServicer):
    
    def CreateJob(self, request, context):
        try:
            # 1. Convertir datos de gRPC a modelos de Pydantic
            doc_meta = DocumentMetadata(
                name=request.document.name,
                type=request.document.type,
                content=request.document.content
            )
            
            # gRPC usa un objeto 'repeated' que convertimos a lista
            # gRPC pasa stages como strings planos → convertimos a StageConfig
            pipe_config = PipelineConfig(
                stages=[StageConfig(name=s) for s in request.pipeline_config.stages]
            )
            
            job_data = JobCreate(
                document=doc_meta,
                pipelineconfig=pipe_config
            )

            # 2. Llamar a la lógica de negocio existente
            with SessionLocal() as db:
                job = create_job(job_data, db)
                return gateway_pb2.JobResponse(
                    id=str(job.id), 
                    status=job.status.value
                )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return gateway_pb2.JobResponse()
        
    def GetJob(self, request, context):
        try:
            with SessionLocal() as db:
                job = get_job(request.job_id, db)
                # Convertimos el resultado a JSON string si existe
                result_str = json.dumps(job.result) if job.result else ""
                
                return gateway_pb2.JobResponse(
                    id=str(job.id),
                    status=job.status.value,
                    result=result_str
                )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return gateway_pb2.JobResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gateway_pb2_grpc.add_JobGatewayServicer_to_server(JobGatewayService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Server started on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
