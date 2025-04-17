import os
import jwt
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

load_dotenv(".env")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_SERVER_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(user:dict, expires_delta: timedelta | None = None) ->str:
    to_encode = user.copy()
    to_encode['uuid'] = str(user['uuid'])
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token:str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_uuid: str = payload.get("uuid")
        if user_uuid is None:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user_uuid
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token: {}".format(e))