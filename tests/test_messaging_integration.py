import pytest
import json
import pika
import time
from unittest.mock import patch
from core.job_service import create_job
from api.schemas import JobCreate
from models.database import SessionLocal

def test_rabbitmq_integration():
    # 1. Configurar conexión para verificar el mensaje
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    
    # Creamos una cola exclusiva para el test y evitamos que el worker nos robe el mensaje
    test_queue = 'tasks_test_queue'
    channel.queue_declare(queue=test_queue, durable=True)
    channel.queue_purge(test_queue)
    
    # 2. Crear un Job usando el servicio real, interceptando publish_event para usar test_queue
    db = SessionLocal()

    # Datos que cumplen con DocumentMetadata y PipelineConfig
    job_data = JobCreate(
        document={
            "name": "test_file.txt",
            "type": "text/plain",
            "content": "Contenido de prueba para RabbitMQ"
        },
        pipelineconfig={
            "stages": [{"name": "extract"}]
        }
    )
    
    try:
        with patch('core.job_service.events.publish_event') as mock_publish:
            # Reemplazamos la función real por una que publique a la cola de test
            def side_effect(event_type, job_id, payload, queue):
                from messaging.publisher import EventPublisher
                temp_pub = EventPublisher(host='rabbitmq', queues=[test_queue])
                temp_pub.publish_event(event_type, job_id, payload, test_queue)
            
            mock_publish.side_effect = side_effect
            
            job = create_job(job_data, db)
            
            # 3. Intentar recuperar el mensaje de RabbitMQ
            method_frame, header_frame, body = None, None, None
            for _ in range(10):
                method_frame, header_frame, body = channel.basic_get(queue=test_queue, auto_ack=True)
                if method_frame:
                    break
                time.sleep(0.5)
                
            assert method_frame is not None, f"No se recibió mensaje en la cola '{test_queue}'"
            
            payload_data = json.loads(body.decode('utf-8'))
            assert payload_data['event_type'] == 'job.created'
            assert payload_data['job_id'] == job.id
            assert 'doc' in payload_data['payload']
            assert payload_data['payload']['doc']['content'] == "Contenido de prueba para RabbitMQ"
        
    finally:
        channel.queue_delete(test_queue)
        db.close()
        connection.close()

