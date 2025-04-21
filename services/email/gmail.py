import os
import smtplib

from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class HostingerEmail:
    def __init__(self):
        self.host = os.getenv("HOSTINGER_EMAIL_HOST")
        self.port = os.getenv("HOSTNGER_EMAIL_PORT")
        self.email = os.getenv("HOSTINGER_EMAIL_ADDRESS")
        self.password = os.getenv("HOSTINGER_EMAIL_PASSWORD")
        self.mime = MIMEMultipart()

    def send_email(self,dst, subject, message):
        self.mime['From'] = self.email
        self.mime['To'] = dst
        self.mime['Subject'] = subject
        self.mime.attach(MIMEText(message), "plain")


    def send_email_interface(self, data):
        dst = data.get("dst")
        subject = data.get("subject")
        message = data.get("message")
        self.send_email(dst, subject, message)



# --- CRIANDO MENSAGEM ---
mensagem = MIMEMultipart()
mensagem["From"] = email
mensagem["To"] = destinatario
mensagem["Subject"] = assunto
mensagem.attach(MIMEText(mensagem_texto, "plain"))

# --- ENVIO VIA SMTP SSL ---
try:
    with smtplib.SMTP_SSL(host, porta) as servidor:
        servidor.login(email, senha)
        servidor.send_message(mensagem)
        print("✅ E-mail enviado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao enviar e-mail: {e}")
