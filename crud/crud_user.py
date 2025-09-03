from sqlalchemy.orm import Session
from models import models
from schemas import schemas
from services.security import hash_password, validate_password, check_current_password
from services.singleton.log import logger
from datetime import datetime, timezone
from sqlalchemy import func, extract


TAG = "User_CRUD ->"


def get_users(db: Session, skip: int = 0, limit: int = 100):
    logger.info("{} User trying to get users".format(TAG))
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    #usar dados salvos no insomnia para testes de criacao e validacao
    logger.info("{} {} trying to register in application".format( TAG, user.username))
    validate_password(user.password, user.confirm_password)
    db_user = models.User(
        username=user.username,
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        info=user.info,
        gender=user.gender.lower(),
        subscription_status=user.subscription_status,
        phone_identifier=user.phone_identifier
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("{} {} successfully registered in application".format(TAG, user.username))
    return db_user

def get_user(db: Session, uuid : str):
    logger.info(f"{TAG} Getting user by uuid {uuid}")
    user = db.query(models.User).filter(models.User.uuid == uuid).first()

    if not user:
        return None 
    now = datetime.now(timezone.utc)

    month_contrib = (
        db.query(func.count(models.UserOccurrence.occurrence_id))
        .filter(
            models.UserOccurrence.user_id == user.id,
            extract("year", models.UserOccurrence.created_at) == now.year,
            extract("month", models.UserOccurrence.created_at) == now.month,
            models.UserOccurrence.deleted_at.is_(None)
        )
        .scalar()
    )
    remaining = 10 - month_contrib
    if remaining < 0:
        remaining = 0
    user.remaining = remaining
    return user


def get_user_by_email(db: Session, email: str):
    logger.info("{} Getting user by email {}".format(TAG, email))
    return db.query(models.User).filter(models.User.email == email).first()

def update_user(db: Session, uuid: str, user: schemas.UserUpdate):
    logger.info("{} Updating user by uuid {} data: {}".format(TAG, uuid, user))
    db_user = db.query(models.User).filter(models.User.uuid == uuid).first()
    
    if user.username is not None:
        db_user.username = user.username
    if user.name is not None:
        db_user.name = user.name
    if user.email is not None:
        db_user.email = user.email
    if user.new_password is not None:
        check_current_password(user.current_password, db_user.password)
        validate_password(user.new_password, user.confirm_password)
        db_user.password = hash_password(user.new_password)
    
    db.commit()
    db.refresh(db_user)
    logger.info("{} Updated user by uuid {} data: {}".format(TAG, uuid, user))
    return db_user

def update_user_fcm(db: Session, uuid: str, fcm_token: str):
    db_user = db.query(models.User).filter(models.User.uuid == uuid).first()
    db_user.phone_identifier = fcm_token
    db.commit()
    db.refresh(db_user)
    return db_user


def create_exclusion_request(db: Session, exclusion_request: schemas.ExclusionRequestCreate):
    db_user = db.query(models.User).filter(models.User.email == exclusion_request.email).first()
    db_exclusion_request = models.ExclusionRequest(
        user_id=db_user.id,
        reason=exclusion_request.reason
    )
    db.add(db_exclusion_request)
    db.commit() 
    db.refresh(db_exclusion_request)
    return schemas.ExclusionRequestResponse(
        id=db_exclusion_request.id,
        reason=db_exclusion_request.reason
    )

def delete_user(db: Session, uuid: str):
    db_user = db.query(models.User).filter(models.User.uuid == uuid).first()
    db.delete(db_user)
    db.commit()
    return db_user
