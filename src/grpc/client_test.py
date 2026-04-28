import grpc
import sys
import os

# Asegurar que Python encuentre los módulos generados en src/grpc
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'grpc'))

import gateway_pb2
import gateway_pb2_grpc

def run():
    # Using the Docker service name here so it resolves properly inside the container network
    print("Connecting to gRPC server (gateway-grpc:50051)...")
    with grpc.insecure_channel('gateway-grpc:50051') as channel:
        stub = gateway_pb2_grpc.JobGatewayStub(channel)
        
        print("\n--- 1. Probando CreateJob via gRPC ---")
        request = gateway_pb2.CreateJobRequest(
            document=gateway_pb2.DocumentMetadata(
                name="test_grpc.txt",
                type="text/plain",
                content="Este es un documento enviado por gRPC"
            ),
            pipeline_config=gateway_pb2.PipelineConfig(
                stages=["extract"]
            )
        )
        
        try:
            response = stub.CreateJob(request)
            print(f"Respuesta recibida: Job ID = {response.id}, Status = {response.status}")
            
            print("\n--- 2. Probando GetJob via gRPC ---")
            get_request = gateway_pb2.GetJobRequest(job_id=response.id)
            get_response = stub.GetJob(get_request)
            print(f"Detalles del Job: ID = {get_response.id}, Status = {get_response.status}")
            if get_response.result:
                print(f"Resultado parcial: {get_response.result}")
                
        except grpc.RpcError as e:
            print(f"Error gRPC: Status={e.code()}, Detalles={e.details()}")

if __name__ == '__main__':
    run()
