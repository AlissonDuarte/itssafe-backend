import boto3
import json


class AmazonAlertService:
    def __init__(self):
        self.sns_client = boto3.client("sns")

    def send_alert(self, message):
        try:
            self.sns_client.publish(
                TopicArn='arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:alert_topic',
                Message=json.dumps(message),
                Subject="🚨 Warning of proximity to a risk zone!"
            )
        except Exception as e:
            print(f"❌ Erro ao enviar notificação SNS: {e}")