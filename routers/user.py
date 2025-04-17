from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import schemas
from crud import crud_user
from models import models
from services import security, auth
from database import SessionLocal


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@router.post("/users/register", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print("user", user)
    query = db.query(models.User).filter(models.User.email == user.email or models.User.username == user.username).first()
    if query is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
    response = crud_user.create_user(db, user)
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

    return schemas.UserLoginResponse(
        access_token=auth.create_access_token({"uuid":user.uuid, "email":user.email}),
        refresh_token="not implemented yet"
    )
