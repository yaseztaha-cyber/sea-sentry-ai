import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "yolov8n.pt"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "sea_sentry.db"
EVIDENCE_DIR = DATA_DIR / "evidence"
FRONTEND_ORIGIN = "http://localhost:5173"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30
AI_IMGSZ = 640
AI_TARGET_FPS = 6
AI_CONF = 0.35
HEATMAP_GRID = (128, 72)
""" width, height bins """
