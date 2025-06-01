import requests
import json
import os

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_MakeEnvelope
from geopy.distance import geodesic
from typing import List
from schemas import schemas
from database import SessionLocal
from services import geoloc, auth
from services.singleton.producer import producer
from services.singleton.s3 import client_s3
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
        occurrenceType: List[str] = Query(default=[]),
        shifts: List[str] = Query(default=[]),
        riskLevel: List[str] 
        
        = Query(default=[]),
        db: Session = Depends(get_db),
        user_uuid: str = Depends(auth.verify_token)
    ):

    user = crud_user.get_user(db, user_uuid)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.phone_identifier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User without token identifier")

    sc = geoloc.Scans(db).user_location(
        base_location=[lat, lng],
        radius_meters=radius,
        raw_occurrence_type=occurrenceType,
        raw_shifts=shifts,
    )

    cr = geoloc.ClusteringResult()
    
    if riskLevel:
        riskLevel = [rsk.lower() for rsk in riskLevel]
        
    cluster = cr.generate_geojson_cluster_polygons(sc, eps = radius,min_samples=2, risk_level_filter=riskLevel)
    if sc:
        producer.send_message(
            {
                "message":"Warning!",
                "registration_token":user.phone_identifier,
                "mode":"fcm"
            }
        )
    return cluster




def round_grid(value: float, precision=1) -> float:
    return round(value, precision)


BUCKET_NAME = 'itssafeboundzones'
CLOUDFRONT_URL = os.getenv("AWS_CLOUDFRONT_URL")
GRID_SIZE = 0.1

@router.get("/remote-zones")
def get_zonas(
        swLat: float,
        swLng: float,
        neLat: float,
        neLng: float,
        shifts: List[str] = Query(default=[]),
        occurrenceType: List[str] = Query(default=[]),
        riskLevel: List[str] = Query(default=[]),
        db: Session = Depends(get_db),
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
    cell_lat = round_grid(swLat, 1)
    cell_lng = round_grid(swLng, 1)

    filename = f'zone_{int(cell_lat*100)}_{int(cell_lng*100)}.json'
    url = f'{CLOUDFRONT_URL}/zones/{filename}'

    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            if resp.json():
                return resp.json()
    except requests.RequestException:
        pass 

    bbox = f'SRID=4326;POLYGON(({cell_lng} {cell_lat}, {cell_lng+GRID_SIZE} {cell_lat}, {cell_lng+GRID_SIZE} {cell_lat+GRID_SIZE}, {cell_lng} {cell_lat+GRID_SIZE}, {cell_lng} {cell_lat}))'

    sc = geoloc.Scans(db)
    points = sc.remote_scan(bbox=bbox, raw_occurrence_type=occurrenceType, raw_shifts=shifts)
        
    if not points:
        return {"message": "Clean Zone"}

    clustering = geoloc.ClusteringResult()
    geojson = clustering.generate_geojson_cluster_polygons(points, eps=1, min_samples=2, risk_level_filter=riskLevel)

    bucket_s3 = client_s3.get_client()
    bucket_s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f'zones/{filename}',
        Body=json.dumps(geojson),
        ContentType='application/json',
        CacheControl='public, max-age=604800'
    )
    return geojson