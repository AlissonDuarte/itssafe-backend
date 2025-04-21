import os
import pika
import json

from dotenv import load_dotenv

class Producer:
    def __init__(self, queue_name):
        load_dotenv()
        self.queue_name = queue_name
        credentials = pika.PlainCredentials(
            os.getenv('AMQP_USER', 'admin'), 
            os.getenv('AMQP_PASSWORD', 'admin')
        )
        print("credenciais", os.getenv('AMQP_USER', 'admin'), os.getenv('AMQP_PASSWORD', 'admin'))
        self.amqp_host = os.getenv('AMQP_HOST', 'rabbitmq')
        self.amqp_port = os.getenv('AMQP_PORT', 5672)
        print("address", self.amqp_host, self.amqp_port)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.amqp_host,
                port=self.amqp_port,
                credentials=credentials
            )
        )
        print("address", self.amqp_host, self.amqp_port)
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
