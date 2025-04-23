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

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/users/register", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    query = db.query(models.User).filter(models.User.email == user.email or models.User.username == user.username).first()
    if query is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
    response = crud_user.create_user(db, user)
    payload_email = utils.email_confirmation(
        dst=user.email,
        token=auth.create_access_token({"email":user.email, "uuid":response.uuid}, timedelta(days=1)),
        username=user.username
    )
    ses_email.send_email_interface(data=payload_email)
    return response


@router.get("/user", response_model=schemas.UserResponse)
def get_user(uuid: str = Depends(auth.verify_token), db: Session = Depends(get_db), _: str = Depends(auth.verify_token)):
    user = crud_user.get_user(db, uuid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/user", response_model=schemas.UserResponse)
def update_user(user: schemas.UserUpdate, uuid: str = Depends(auth.verify_token), db: Session = Depends(get_db), _: str = Depends(auth.verify_token)):
    db_user = crud_user.get_user(db, uuid)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    query = db.query(models.User).filter((models.User.email == user.email) | (models.User.username == user.username), models.User.id != db_user.id).first()
    if query is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
    
    return crud_user.update_user(db, uuid, user)

@router.delete("/user", response_model=schemas.UserResponse)
def delete_user(uuid: str = Depends(auth.verify_token), db: Session = Depends(get_db), _: str = Depends(auth.verify_token)):
    db_user = crud_user.get_user(db, uuid)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud_user.delete_user(db, uuid)


@router.post("/users/login")
def user_login(data: schemas.UserLoginRequest, db: Session = Depends(get_db), response_model=schemas.UserLoginResponse):

    user = crud_user.get_user_by_email(db, data.email)
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
def user_email_confirmation(token: str, db: Session = Depends(get_db)):
    
    try:
        user_uuid = auth.verify_token(token)
        user = crud_user.get_user(db, user_uuid)

        if not user:
            return HTMLResponse(content="<h1>User not found</h1>", status_code=404)
        
        try:
            with open("static/templates/email_verified.html", "r", encoding="utf-8") as f:
                email_template_html = f.read()
        except:
            email_template_html = "<p>Your email has been successfully confirmed. You can now log in and start exploring safely.</p>"
            
        if user.subscription_status == 'active':
            return HTMLResponse(content=email_template_html, status_code=200)

        if user.subscription_status == 'inactive':
            user.subscription_status = 'active'
            db.commit()
            return HTMLResponse(content=email_template_html, status_code=200)

        return HTMLResponse(content="<h1>Error verifying subscription</h1>", status_code=400)

    except:
        return HTMLResponse(content="<h1>Invalid or expired token</h1>", status_code=400)