import os
import pika
import json
import time

from dotenv import load_dotenv

class Producer:
    def __init__(self, queue_name):
        load_dotenv()
        self.queue_name = queue_name
        amqp_url = os.getenv('RABBITMQ_URL', 'amqp://admin:admin@localhost:5672/')
        params = pika.URLParameters(amqp_url)
        for attempt in range(10):
            try:
                self.connection = pika.BlockingConnection(params)
                break
            except pika.exceptions.AMQPConnectionError:
                print(f"Tentativa {attempt + 1}: RabbitMQ ainda não está pronto. Tentando novamente em 3s...")
                time.sleep(3)
        else:
            raise Exception("Não foi possível conectar ao RabbitMQ após várias tentativas.")


        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def send_message(self, message: dict) -> None:
        message: str = json.dumps(message)
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
    def close_connection(self) -> None:
        self.connection.close()
