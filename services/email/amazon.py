import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from services.singleton.log import logger

TAG = "SESSMTP -> "

class SESSMTP:
    def __init__(self):
        logger.info(f"{TAG} Starting class")
        load_dotenv()

        self.smtp_host = os.getenv("SES_SMTP_HOST", "email-smtp.us-east-1.amazonaws.com")  # substitua se for outra região
        self.smtp_port = int(os.getenv("SES_SMTP_PORT", 465))
        self.smtp_user = os.getenv("SES_SMTP_USERNAME")
        self.smtp_pass = os.getenv("SES_SMTP_PASSWORD")
        self.sender = os.getenv("SES_EMAIL_ADDRESS")

        assert self.smtp_user, "❌ SES_SMTP_USERNAME not set"
        assert self.smtp_pass, "❌ SES_SMTP_PASSWORD not set"
        assert self.sender, "❌ SES_EMAIL_ADDRESS not set"

        self.mime = MIMEMultipart()
        logger.info(f"{TAG} Class started successfully")

    def _send_email(self, dst: str, subject: str, message: str):
        self.mime['From'] = self.sender
        self.mime['To'] = dst
        self.mime['Subject'] = subject
        self.mime.attach(MIMEText(message, "html"))

        try:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(self.mime)
                logger.info(f"{TAG} Email sent via SES SMTP to {dst}")
        except Exception as e:
            logger.error(f"{TAG} Failed to send email to {dst}: {e}")

    def send_email_interface(self, data: dict):
        dst = data.get("dst")
        subject = data.get("subject")
        message = data.get("message")
        logger.info(f"{TAG} Interface accessed to dst {dst}")
        self._send_email(dst, subject, message)
