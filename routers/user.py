from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from schemas import schemas
from crud import crud_user
from models import models
from services import security, auth, utils
from database import SessionLocal
from services.singleton.amazon import ses_email
from services.singleton.hostinger import hostinger_email
from services.utils import generate_token
from services.redis.redis import save_token, get_token_data, delete_token
from services.security import hash_password, validate_password

router=APIRouter()


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/users/register", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session=Depends(get_db)):
    query=db.query(models.User).filter(models.User.email == user.email or models.User.username == user.username).first()
    if query is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
    response=crud_user.create_user(db, user)
    payload_email=utils.email_confirmation(
        dst=user.email,
        token=auth.create_access_token({"email":user.email, "uuid":response.uuid}, timedelta(days=1)),
        username=user.username
    )
    hostinger_email.send_email_interface(data=payload_email)
    response = crud_user.get_user(db, response.uuid)
    return response


@router.get("/user", response_model=schemas.UserResponse)
def get_user(uuid: str=Depends(auth.verify_token), db: Session=Depends(get_db), _: str=Depends(auth.verify_token)):
    user=crud_user.get_user(db, uuid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/user", response_model=schemas.UserResponse)
def update_user(user: schemas.UserUpdate, uuid: str=Depends(auth.verify_token), db: Session=Depends(get_db), _: str=Depends(auth.verify_token)):
    db_user=crud_user.get_user(db, uuid)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    query=db.query(models.User).filter((models.User.email == user.email) | (models.User.username == user.username), models.User.id != db_user.id).first()
    if query is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
    
    return crud_user.update_user(db, uuid, user)

@router.delete("/user", response_model=schemas.UserResponse)
def delete_user(uuid: str=Depends(auth.verify_token), db: Session=Depends(get_db), _: str=Depends(auth.verify_token)):
    db_user=crud_user.get_user(db, uuid)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud_user.delete_user(db, uuid)


@router.post("/user/update/fcm", response_model=schemas.GenericResponse)
def update_user_fcm(payload:schemas.UserFCM, uuid: str=Depends(auth.verify_token), db: Session=Depends(get_db)):

    db_user=crud_user.get_user(db, uuid)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    response = crud_user.update_user_fcm(db, uuid, payload.fcm_token)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return schemas.GenericResponse(message="FCM token updated", status=True)

@router.post("/users/login")
def user_login(data: schemas.UserLoginRequest, db: Session=Depends(get_db), response_model=schemas.UserLoginResponse):

    user=crud_user.get_user_by_email(db, data.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if security.verify_password(data.password, user.password) is False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    if user.subscription_status == "inactive":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please confirm your email")
    return schemas.UserLoginResponse(
        access_token=auth.create_access_token({"uuid":user.uuid, "email":user.email}),
        refresh_token="not implemented yet"
    )

@router.get("/user/email/confirmation", response_class=HTMLResponse)
def user_email_confirmation(token: str, db: Session=Depends(get_db)):
    
    try:
        user_uuid=auth.verify_token(token)
        user=crud_user.get_user(db, user_uuid)

        if not user:
            return HTMLResponse(content="<h1>User not found</h1>", status_code=404)
        
        try:
            with open("static/templates/email_verified.html", "r", encoding="utf-8") as f:
                email_template_html=f.read()
        except:
            email_template_html="<p>Your email has been successfully confirmed. You can now log in and start exploring safely.</p>"
            
        if user.subscription_status == 'active':
            return HTMLResponse(content=email_template_html, status_code=200)

        if user.subscription_status == 'inactive':
            user.subscription_status='active'
            db.commit()
            return HTMLResponse(content=email_template_html, status_code=200)

        return HTMLResponse(content="<h1>Error verifying subscription</h1>", status_code=400)

    except:
        return HTMLResponse(content="<h1>Invalid or expired token</h1>", status_code=400)
    

@router.post("/users/password_recovery")
async def password_recovery(request: schemas.RecoveryPassword, db: Session=Depends(get_db)):
    user=crud_user.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token=generate_token()
    await save_token(user.uuid, token)

    payload=utils.reset_password_template(request.email, token)

    try:
        hostinger_email.send_email_interface(data=payload)
    except Exception:
        raise HTTPException(status_code=404, detail="Error to send email, please try later")
    
    return {"message":"Email sent with success"}


@router.post("/users/reset_password")
async def reset_password(request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    token_data = await get_token_data(request.recovery_token)

    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = crud_user.get_user(db, token_data['user_uuid'])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    validate_password(request.new_password, request.confirm_password)
    user.hashed_password = hash_password(request.new_password)
    db.commit()
    
    await delete_token(request.recovery_token)

    return {"message": "Password updated!"}


@router.delete("/users/exlusion", response_model=schemas.GenericResponse)
async def user_data_exclusion(payload: schemas.ExclusionRequestCreate, db: Session=Depends(get_db)):
    user=crud_user.get_user_by_email(db, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud_user.create_exclusion_request(db, schemas.ExclusionRequestCreate(email=user.email))
    return schemas.GenericResponse(message="Exclusion request created", status=True)