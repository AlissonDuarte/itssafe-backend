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

        self.mime = MIMEMultipart()
        logger.info("{} Class started with success".format(TAG))


    def _send_email(self, dst:str, subject:str, message:str):
        self.mime['From'] = self.email
        self.mime['To'] = dst
        self.mime['Subject'] = subject
        self.mime.attach(MIMEText(message, "html"))
        with smtplib.SMTP_SSL(self.host, self.port) as server:
            try:
                server.login(self.email, self.password)
            except Exception as e:
                logger.info("{} Error in login proccess with Email {}".format(TAG, e))

            try:
                server.send_message(self.mime)
            except Exception as e:
                logger.info("{} login with success but error to send a message {}".format(TAG, e))

    def send_email_interface(self, data:dict):
        dst = data.get("dst")
        subject = data.get("subject")
        message = data.get("message")
        self._send_email(dst, subject, message)
