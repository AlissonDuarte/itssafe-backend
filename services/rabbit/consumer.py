import os
import pika
import json
import asyncio

from services.alerts.firebase import FirebaseAlertService


class Consumer:
    def __init__(self, queue_name):
        credentials = pika.PlainCredentials(
            os.getenv('AMQP_USER', 'admin'), 
            os.getenv('AMQP_PASSWORD', 'admin')
        )

        self.fcm = FirebaseAlertService()
        self.queue_name = queue_name
        self.amqp_host = os.getenv('AMQP_HOST', 'localhost')
        self.amqp_port = int(os.getenv('AMQP_PORT', 5672))
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.amqp_host,
                port=self.amqp_port,
                credentials=credentials
            )
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.mode_map = {
            'fcm': self.fcm.send_alert,
            'sns':self._sns
        }

    async def send_notification(self, payload:dict):
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

    def consume(self):
        print("📡 Iniciando consumidor RabbitMQ...")
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
        self.channel.start_consuming()


    def _sns(self):
        pass