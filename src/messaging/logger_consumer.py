import pika
import json
import sys
import time

def main():
    for i in range(15):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()
            
            # Binding a shared queue to a fanout exchange gives us 
            # the "Consumer Groups" behavior right out of the box.
            # Multiple instances of this logger will automatically load-balance.
            channel.exchange_declare(exchange='events_exchange', exchange_type='fanout')
            channel.queue_declare(queue='logger_group_queue', durable=True)
            channel.queue_bind(exchange='events_exchange', queue='logger_group_queue')
            
            print(" [*] Logger Consumer started. Waiting for events. To exit press CTRL+C")
            break
        except Exception as e:
            print(f"Connection failed, retrying in 3s... ({e})")
            time.sleep(3)
    else:
        sys.exit(1)

    def callback(ch, method, properties, body):
        event = json.loads(body.decode('utf-8'))
        print(f" [EVENT RECEIVED] Type: {event.get('event_type')} | Job: {event.get('job_id')}")
        print(f" [PAYLOAD]: {event.get('payload')}")
        print("-" * 50)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='logger_group_queue', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
