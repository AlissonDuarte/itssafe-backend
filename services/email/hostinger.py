import os
import smtplib

from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from services.singleton.log import logger

TAG = "HostingerEmail -> "

class HostingerEmail:
    def __init__(self):
        logger.info("{} Starting class".format(TAG))
        load_dotenv()
        self.host = os.getenv("HOSTINGER_EMAIL_HOST")
        self.port = os.getenv("HOSTINGER_EMAIL_PORT")
        self.email = os.getenv("HOSTINGER_EMAIL_ADDRESS")
        self.password = os.getenv("HOSTINGER_EMAIL_PASSWORD")

        assert self.host, "❌ Environment variable HOSTINGER_EMAIL_HOST is not set."
        assert self.port, "❌ Environment variable HOSTINGER_EMAIL_PORT is not set."
        assert self.email, "❌ Environment variable HOSTINGER_EMAIL_ADDRESS is not set."
        assert self.password, "❌ Environment variable HOSTINGER_EMAIL_PASSWORD is not set."
        logger.info("{} Class started with success".format(TAG))

    def _send_email(self, dst:str, subject:str, message:str):
        mime = MIMEMultipart()
        mime['From'] = self.email
        mime['To'] = dst
        mime['Subject'] = subject
        mime.attach(MIMEText(message, "html"))

        with smtplib.SMTP_SSL(self.host, self.port) as server:
            try:
                server.login(self.email, self.password)
                logger.info(f"{TAG} Successful login on Hostinger SMTP to {dst}")
            except Exception as e:
                logger.info(f"{TAG} Error in login process with Email {e}")

            try:
                server.send_message(mime)
                logger.info(f"{TAG} Message sent with Hostinger SMTP to {dst}")
            except Exception as e:
                logger.info(f"{TAG} login ok but error to send message {e}")
    def send_email_interface(self, data:dict):
        dst = data.get("dst")
        subject = data.get("subject")
        message = data.get("message")
        logger.info("{} Interface accessed to dst {}".format(TAG, dst))
        self._send_email(dst, subject, message)
