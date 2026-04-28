import pika
import json
import sys
import time
import asyncio
from core.pipeline import process_doc

MAX_RETRIES = 15
RETRY_DELAY = 3

def callback(ch, method, properties, body):
    try:
        payload = json.loads(body.decode('utf-8'))
        job_id = payload.get('job_id')

        if job_id:
            print(f"Processing JOB for job_id '{job_id}'...")
            asyncio.run(process_doc(job_id)) 

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error processing message: {e}")


def main():
    for i in range(MAX_RETRIES):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=600))
            channel = connection.channel()
            channel.queue_declare('tasks', durable=True)
            print("RabbitMQ connection stablished.")
            break
        except Exception as e:
            print(f"Error connecting to RabbitMQ: {e}. Retrying...")
            time.sleep(RETRY_DELAY)

    channel.basic_consume("tasks", on_message_callback=callback)
    channel.basic_qos(prefetch_count=1)
    print("Waiting messages... ")
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)


