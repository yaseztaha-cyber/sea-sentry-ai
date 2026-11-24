# Sea Sentry AI — Real-Time Coastal Monitoring

Sea Sentry AI is an in-development computer-vision system for monitoring coastal/swimming areas. A FastAPI backend captures a camera stream, runs YOLOv8 person detection, tracks individuals, builds a density heat map, and detects behavioral incidents (pause, trajectory change, disappearance, restricted-zone dwell). A React/Vite frontend provides live monitoring, incident review, camera, AI, heat-map, and settings views. Incidents and zones are persisted in SQLite.

A separate Next.js/PostgreSQL prototype ("The Living Tides") exists under `sea-sentry-ai-development (1)/` and is kept locally; it is not part of this repository's published source.

## Technology stack

- **Backend:** Python, FastAPI, Uvicorn, SQLAlchemy, SQLite, Ultralytics YOLOv8, OpenCV, NumPy, SciPy, WebSocket.
- **Frontend:** React, TypeScript, Vite.
- **AI/ML:** YOLOv8n (COCO person class), ONNX/PyTorch runtime.
- **Camera:** local webcam via pygrabber/OpenCV.

## Running locally

Prerequisites: Python 3.11+, Node.js 20+, a webcam.

```powershell
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# frontend
cd ..\frontend
npm install
npm run dev
```

Open http://localhost:5173. API docs at http://127.0.0.1:8000/docs.

Or run `scripts\start.ps1` from the project root.

## Configuration

No environment variables are required for the primary build. The nested Next.js prototype uses its own `.env` (see its README).

## Limitations

- Windows-oriented camera capture (pygrabber).
- YOLOv8n model file (`models/yolov8n.pt`) is not committed.
- Experimental behavior rules; not validated for safety-critical use.
- Single-camera, local deployment only.

## Status

In development.

## License

No license file is present; licensing decision required.
