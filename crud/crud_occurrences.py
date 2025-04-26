from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from models import models
from schemas import schemas
from geoalchemy2 import WKTElement
from crud import crud_user
from fastapi import HTTPException
from datetime import datetime, timezone
from services.singleton.log import logger


TAG = "Occurrences_CRUD ->"

def get_occurrences(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Occurrence).offset(skip).limit(limit).all()

def create_occurrence_and_user_occurrence(db: Session, occurrence_data: schemas.OccurrenceCreate, uuid:str):
    user = crud_user.get_user(db, uuid)
    now = datetime.now(timezone.utc)

    if not user:
        logger.error("{} User not found uuid: {}".format(TAG, uuid))
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info("{} User {} trying to create occurrence at {}".format(TAG, user.username, now))
    user_limit = (
        db.query(func.count(models.UserOccurrence.occurrence_id))
        .filter(
            models.UserOccurrence.user_id == user.id,
            extract("year", models.UserOccurrence.created_at) == now.year,
            extract("month", models.UserOccurrence.created_at) == now.month,
            models.UserOccurrence.deleted_at.is_(None)
        )
        .scalar()
    )

    if user_limit >=10:
        logger.error("{} User {} has reached the limit of 10 occurrences per month".format(TAG, user.username))
        raise HTTPException(status_code=403, detail="User has reached the limit of 10 occurrences per month")
    
    point = f"POINT({occurrence_data.local[0]} {occurrence_data.local[1]})"

    db_occurrence = models.Occurrence(
        description=occurrence_data.description,
        type=occurrence_data.type,
        local=WKTElement(point, srid=4326),
        coordinates=occurrence_data.local,
        event_datetime=occurrence_data.event_datetime
    )

    db.add(db_occurrence)
    db.commit()
    db.refresh(db_occurrence)

    logger.info("{} User {} created occurrence {}".format(TAG, user.username, db_occurrence.id))
    # cria o registro de user_occurrence
    db_user_occurrence = models.UserOccurrence(
        user_id=user.id,
        occurrence_id=db_occurrence.id
    )
    db.add(db_user_occurrence)
    db.commit()
    db.refresh(db_user_occurrence)

    user.contributions += 1
    db.commit()
    db.refresh(user)
    logger.info("{} User {} created user_occurrence {}".format(TAG, user.username, db_user_occurrence.id))

    db_occurrence.local  = occurrence_data.local
    return db_occurrence