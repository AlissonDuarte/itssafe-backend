from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import schemas
from crud import crud_occurrences
from database import SessionLocal
from services.auth import verify_token

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/occurrences", response_model=schemas.OccurrenceResponse)
async def create_occurrence(occurrence: schemas.OccurrenceCreate, db: Session = Depends(get_db), uuid: str = Depends(verify_token)):
    return crud_occurrences.create_occurrence_and_user_occurrence(db, occurrence, uuid)


@router.get("/occurrences", response_model=list[schemas.OccurrenceResponse])
async def get_occurrences(db: Session = Depends(get_db), _: str = Depends(verify_token)):
    return crud_occurrences.get_occurrences(db)