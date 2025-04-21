import os
import pika
import json
import time
from dotenv import load_dotenv

class Producer:
    def __init__(self, queue_name):
        load_dotenv()
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        amqp_url = os.getenv('RABBITMQ_URL', 'amqp://admin:admin@localhost:5672/')
        params = pika.URLParameters(amqp_url)
        for attempt in range(10):
            try:
                print(f"Tentando conectar ao RabbitMQ... (tentativa {attempt + 1})")
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                print("Conexão e canal estabelecidos com sucesso.")
                break
            except pika.exceptions.AMQPConnectionError:
                print(f"Tentativa {attempt + 1}: RabbitMQ ainda não está pronto. Tentando novamente em 3s...")
                time.sleep(3)
        else:
            raise Exception("Não foi possível conectar ao RabbitMQ após várias tentativas.")

    def send_message(self, message: dict) -> None:
        # Tenta enviar a mensagem e reconectar se necessário
        try:
            message_str = json.dumps(message)
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=message_str,
                properties=pika.BasicProperties(
                    delivery_mode=2 
                )
            )
            print(f"Mensagem enviada: {message}")
        except pika.exceptions.AMQPConnectionError:
            print("❌ Conexão perdida com RabbitMQ. Tentando reconectar...")
            self.reconnect()
            self.send_message(message)
        except pika.exceptions.AMQPChannelError:
            print("❌ Canal fechado. Tentando reconectar...")
            self.reconnect()
            self.send_message(message)

    def reconnect(self):
        # Fecha a conexão atual e tenta se reconectar
        try:
            self.connection.close()
        except Exception as e:
            print(f"Erro ao fechar a conexão anterior: {e}")
        self._connect()

    def close_connection(self) -> None:
        self.connection.close()
