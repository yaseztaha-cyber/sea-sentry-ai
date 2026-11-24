from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from .config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class CameraConfig(Base):
    __tablename__ = "camera_configurations"
    id = Column(Integer, primary_key=True)
    device_index = Column(Integer, default=0)
    name = Column(String, default="Camera")
    created_at = Column(DateTime, default=datetime.utcnow)

class CameraSession(Base):
    __tablename__ = "camera_sessions"
    id = Column(Integer, primary_key=True)
    device_index = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    actual_width = Column(Integer)
    actual_height = Column(Integer)
    actual_fps = Column(Float)
    actual_fourcc = Column(String)
    status = Column(String)

class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True)
    frame_id = Column(Integer)
    ts = Column(DateTime, default=datetime.utcnow)
    track_id = Column(Integer, nullable=True)
    x = Column(Float); y = Column(Float); w = Column(Float); h = Column(Float)
    conf = Column(Float)
    model_version = Column(String)

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, unique=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float, default=0.0)

class TrackPoint(Base):
    __tablename__ = "track_points"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    ts = Column(DateTime, default=datetime.utcnow)
    cx = Column(Float); cy = Column(Float)
    frame_id = Column(Integer)

class MonitoringZone(Base):
    __tablename__ = "monitoring_zones"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    zone_type = Column(String)
    points = Column(Text)  # json list of [x,y] normalized
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BehavioralObservation(Base):
    __tablename__ = "behavioral_observations"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, nullable=True)
    obs_type = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Float, default=0.0)
    features = Column(Text)
    rule_version = Column(String)
    status = Column(String, default="EXPERIMENTAL")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True)
    severity = Column(String, default="MEDIUM")
    status = Column(String, default="NEW")
    created_at = Column(DateTime, default=datetime.utcnow)
    track_id = Column(Integer, nullable=True)
    observation_id = Column(Integer, nullable=True)
    frame_ref = Column(String, nullable=True)
    ai_version = Column(String)
    notes = Column(Text, default="")

class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    kind = Column(String)
    path = Column(String)
    meta = Column(Text)

class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    ts = Column(DateTime, default=datetime.utcnow)
    action = Column(String)
    detail = Column(Text)

class SystemEvent(Base):
    __tablename__ = "system_events"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, default=datetime.utcnow)
    level = Column(String)
    message = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)
