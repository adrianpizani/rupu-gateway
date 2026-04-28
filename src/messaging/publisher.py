from datetime import datetime
import pika
import json
import time
import sys

MAX_RETRIES = 15
RETRY_DELAY = 3

class EventPublisher():
    def __init__(self, host="rabbitmq", queues=None):
        self.queues = queues or []
        self.channel = None
        self.connection = None
        self._connect()

    def _connect(self):
        for i in range(MAX_RETRIES):
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=600))
                self.channel = self.connection.channel()
                
                # Specific queue for dispatching work to the background workers
                if "tasks" in self.queues:
                    self.channel.queue_declare(queue="tasks", durable=True)
                
                # Fanout exchange for events so multiple consumer groups can listen in
                if "events" in self.queues:
                    self.channel.exchange_declare(exchange='events_exchange', exchange_type='fanout')
                    # Keep the original 'events' queue alive and bind it to the exchange
                    # so any existing consumers/tests don't break.
                    self.channel.queue_declare(queue="events", durable=True)
                    self.channel.queue_bind(exchange='events_exchange', queue='events')
                    
                break
            except Exception as e:
                print(f"Error connecting to RabbitMQ: {e}. Retrying...")
                time.sleep(RETRY_DELAY)
        else:
            print("Can't connect to RabbitMQ.")
            sys.exit(1)


    def publish_event(self, event_type: str, job_id: str, payload: dict, routing: str = "events"):
        new_event = {
            "event_type": event_type,
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }
        
        body = json.dumps(new_event).encode('utf-8')

        if routing == "events":
            # Publish to exchange for pub/sub (Consumer Groups)
            self.channel.basic_publish(
                exchange='events_exchange',
                routing_key='',
                body=body,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        else:
            # Publish directly to a queue (e.g., tasks)
            self.channel.basic_publish(
                exchange='',
                routing_key=routing,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2)
            )

        print(f"Event published to {routing}")

