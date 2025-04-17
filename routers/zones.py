from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from schemas import schemas
from database import SessionLocal
from services import geoloc, auth
from services.singleton.producer import producer
from crud import crud_user


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

@router.get("/danger-zones", response_model=schemas.DangerZonesResponse)
def get_danger_zones(
        lat:float = Query(..., description="Lat"),
        lng:float = Query(..., description="Long"),
        radius:float = Query(..., description="Radius zone"),
        db: Session = Depends(get_db),
        user_uuid: str = Depends(auth.verify_token)
    ):

    user = crud_user.get_user(db, user_uuid)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.phone_identifier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User without token identifier")

    sc = geoloc.Scans(db).user_location(base_location = [lat, lng], radius_meters = radius)
    
    cr = geoloc.ClusteringResult()
    cluster = cr.generate_geojson_cluster_polygons(sc, eps = radius,min_samples=2)
    if sc:
        producer.send_message(
            {
                "message":"Warning!",
                "registration_token":user.phone_identifier,
                "mode":"fcm"
            }
        )
    return cluster