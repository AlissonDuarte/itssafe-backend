from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from services import oauth2
import httpx

router = APIRouter()

@router.post("login/auth/google")
def google_auth():
    auth_url = oauth2.get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("login/auth/google/callback")
async def google_auth_callback(request: Request, code: str):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(oauth2.GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": oauth2.GOOGLE_CLIENT_ID,
            "client_secret": oauth2.GOOGLE_CLIENT_SECRET,
            "redirect_uri": oauth2.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        })

        token_data = token_response.json()
        access_token = token_data['access_token']

        user_info_response = await client.get(oauth2.GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}"
        })

        user_info = user_info_response.json()
        return {
            "access_token": access_token,
            "user_info": user_info
        }
    
@router.post("login/auth/facebook")
def facebook_auth():
    auth_url = oauth2.get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("login/auth/facebook/callback")
async def facebook_auth_callback(request: Request, code: str):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(oauth2.FACEBOOK_TOKEN_URL, data={
            "code": code,
            "client_id": oauth2.FACEBOOK_CLIENT_ID,
            "client_secret": oauth2.FACEBOOK_CLIENT_SECRET,
            "redirect_uri": oauth2.FACEBOOK_REDIRECT_URI,
            "grant_type": "authorization_code"
        })

        token_data = token_response.json()
        access_token = token_data['access_token']

        user_info_response = await client.get(oauth2.FACEBOOK_USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}"
        })

        user_info = user_info_response.json()
        return {
            "access_token": access_token,
            "user_info": user_info
        }
    
