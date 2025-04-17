import os
import httpx
import firebase_admin
import google.auth.transport.requests

from dotenv import load_dotenv
from google.oauth2 import service_account
from firebase_admin import credentials


class FirebaseAlertService:
    def __init__(self):
        load_dotenv()
        scopes = ["https://www.googleapis.com/auth/firebase.messaging"]
        project_id = os.getenv("FIREBASE_PROJECT_ID")        
        service_account_file = "AccountServiceFCM.json"

        cred = credentials.Certificate(service_account_file)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        endpoint = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        credentials_ = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        request = google.auth.transport.requests.Request()
        credentials_.refresh(request)
        access_token = credentials_.token

        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

    async def send_alert(self, message: str, registration_token: str):

        payload = {
            "message": {
                "token": registration_token,
                "notification": {
                    "title": "🚨 Warning of proximity to a risk zone!",
                    "body": message
                }
            }
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(self.endpoint, headers=self.headers, json=payload)

        if response.status_code == 200:
            print("✅ Notificação enviada com sucesso!")
        else:
            print(f"❌ Falha ao enviar notificação. Status code: {response.status_code} -> {response.text}")
