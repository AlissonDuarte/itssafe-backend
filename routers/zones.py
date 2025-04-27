from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_Within, ST_MakeEnvelope
from geopy.distance import geodesic
from typing import List
from schemas import schemas
from database import SessionLocal
from services import geoloc, auth
from services.singleton.producer import producer
from crud import crud_user
from models import models


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
        occurrenceType: List[str] = Query(default=[]),
        shifts: List[str] = Query(default=[]),
        db: Session = Depends(get_db),
        user_uuid: str = Depends(auth.verify_token)
    ):

    user = crud_user.get_user(db, user_uuid)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.phone_identifier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User without token identifier")

    sc = geoloc.Scans(db).user_location(
        base_location = [lat, lng], 
        radius_meters = radius, 
        raw_occurrence_type = occurrenceType,
        raw_shifts = shifts
    )

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




@router.get("/zonas")
def get_zonas(
    swLat: float, swLng: float, neLat: float, neLng: float, 
    db: Session = Depends(get_db)
):
    bbox = ST_MakeEnvelope(
        min(swLng, neLng),  
        min(swLat, neLat),
        max(swLng, neLng),
        max(swLat, neLat),
        4326  # SRID
    )
    diagonal_km = geodesic((swLat, swLng), (neLat, neLng)).kilometers
    
    if diagonal_km > 10: 
        raise HTTPException(
            status_code=400,
            detail="Very wide viewing area. Zoom in on the map to load risk zones."
        )
    query = db.query(models.Occurrence).filter(
        ST_Within(
            models.Occurrence.local,  
            bbox 
        )
    ).all()

    occurrences_coords = [occurrence.coordinates for occurrence in query]
    if occurrences_coords:
        clustering = geoloc.ClusteringResult()
        geojson = clustering.generate_geojson_cluster_polygons(
            occurrences_coords, 
            eps=0.5, 
            min_samples=2
        )
        return geojson
    else:
        return {"message": "Clean Zone"}