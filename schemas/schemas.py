from typing import Optional, List, Union, Literal, Any
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    username: str
    name: str
    email: EmailStr
    gender: Literal['male', 'female', 'other']
    info: Optional[dict[str, Any]] = {"data":None}
    phone_identifier: str
    subscription_status: str = "active"


class UserCreate(UserBase):
    password: str
    confirm_password: str

class UserResponse(UserBase):
    uuid: UUID
    username: str
    contributions: int
    remaining: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None
    

class OccurrenceBase(BaseModel):
    description: str
    type: Literal["Theft", "Aggressive Person", "Suspicious Activity", "Fight", "Drugs"]
    latitude: float
    longitude: float


class OccurrenceCreate(BaseModel):
    description: str
    type: Literal["Theft", "Aggressive Person", "Suspicious Activity", "Fight", "Drugs"]
    local: List[float]
    event_datetime: str

class OccurrenceResponse(BaseModel):
    id: int
    description: str
    type: str  
    coordinates: list
    updated_at: Optional[datetime]
    created_at: Optional[datetime]  

    class Config:
        from_attributes = True
    

class UserOccurrenceCreate(BaseModel):
    user_id: int
    occurrence_id: int


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str


class PointGeometry(BaseModel):
    type: str = Field("Point", Literal=True)
    coordinates: List[float]  # [lat, lng]

class LineStringGeometry(BaseModel):
    type: str = Field("LineString", Literal=True)
    coordinates: List[List[float]]  # [[lat, lng], [lat, lng], ...]

class PolygonGeometry(BaseModel):
    type: str = Field("Polygon", Literal=True)
    coordinates: List[List[List[float]]]  # [[[lat, lng], [lat, lng], ...]]

class FeatureProperties(BaseModel):
    cluster_id: int
    risk_level: str
    occurrence_count: int

class Feature(BaseModel):
    type: str = Field("Feature", Literal=True)
    geometry: Union[PointGeometry, LineStringGeometry, PolygonGeometry]
    properties: FeatureProperties

DangerZonesResponse = List[Feature]


class RabbitPayload(BaseModel):
    message: str
    registration_token: str
    mode: Literal['fcm', 'sns']
