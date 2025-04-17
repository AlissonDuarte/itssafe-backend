import uuid as uuid_pkg
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from sqlalchemy import Enum as SQLEnum
from enum import Enum


class User(Base):
    __tablename__ = "users"

    class Gender(str, Enum):
        MALE = "male"
        FEMALE = "female"
        OTHER = "other"
        
    class SubscriptionStatus(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_pkg.uuid4, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    gender = Column(SQLEnum(Gender), nullable=False, default=Gender.OTHER)
    subscription_status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    phone_identifier = Column(String)
    info = Column(JSON, nullable=False)
    birth_date  = Column(DateTime(timezone=True), nullable=True)
    contributions = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class Occurrence(Base):

    class OccurrenceType(str, Enum):
        THEFT = "Theft"
        STRANGE_MOVIMENT = "Strange Movement"
        FIGHT = "Fight"
        PERSON_AGGRESSIVE = "Aggressive Person"
        DRUGS = "Drugs"

    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_pkg.uuid4, unique=True, index=True)
    description = Column(String)
    type = Column(SQLEnum(OccurrenceType), nullable=False)
    coordinates = Column(JSON, nullable=False)
    local = Column(Geometry(geometry_type='POINT', srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class UserOccurrence(Base):
    __tablename__ = "user_occurrences"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_pkg.uuid4, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    occurrence_id = Column(Integer, ForeignKey("occurrences.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
