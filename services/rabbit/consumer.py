import os
import pika
import json
import asyncio
import time

from dotenv import load_dotenv
from services.alerts.firebase import FirebaseAlertService


class Consumer:
    def __init__(self, queue_name):
        load_dotenv()
        self.queue_name = queue_name
        self.fcm = FirebaseAlertService()
        self.mode_map = {
            'fcm': self.fcm.send_alert,
            'sns': self._sns
        }
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

    async def send_notification(self, payload: dict):
        message = payload.get('message')
        registration_token = payload.get('registration_token')
        mode = payload.get('mode')
        if not mode:
            print("Hello? ", message)
            return
        func = self.mode_map[mode]
        await func(message, registration_token)

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            print(f"📩 Mensagem recebida: {message}")
            asyncio.run(self.send_notification(message))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("✅ Mensagem processada com sucesso!")
        except json.JSONDecodeError:
            print("❌ Erro ao decodificar JSON")
        except pika.exceptions.AMQPConnectionError:
            print("❌ Conexão perdida com RabbitMQ. Tentando reconectar...")
            self.reconnect()
        except pika.exceptions.AMQPChannelError:
            print("❌ Canal fechado. Tentando reconectar...")
            self.reconnect()

    def reconnect(self):
        try:
            self.connection.close()
        except Exception as e:
            print(f"Erro ao fechar a conexão anterior: {e}")
        self._connect()
        self.consume()

    def consume(self):
        print("📡 Iniciando consumidor RabbitMQ...")
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
        self.channel.start_consuming()

    def _sns(self):
        pass
