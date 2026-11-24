import json, time, asyncio, threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .db import init_db, SessionLocal, MonitoringZone, Incident, IncidentTimeline, IncidentEvidence, SystemEvent, CameraSession
from .camera import CameraManager
from .ai import AIEngine
from .websocket import WSManager
from .config import FRONTEND_ORIGIN, DATA_DIR

from fastapi.staticfiles import StaticFiles
app = FastAPI(title="Sea Sentry AI", version="0.1.0")
app.mount("/data/evidence", StaticFiles(directory=str(DATA_DIR/"evidence")), name="evidence")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN,"http://127.0.0.1:5173","http://localhost:5173"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

camera = CameraManager()
ws_manager = WSManager()
ai_engine = None
zones_cache = []

def db():
    return SessionLocal()

def broadcast(d):
    if ws_manager:
        ws_manager.broadcast(d)

@app.on_event("startup")
async def startup():
    global ai_engine
    init_db()
    ws_manager.set_loop(asyncio.get_event_loop())
    ai_engine = AIEngine(camera, SessionLocal, broadcast)
    ai_engine.load_model()
    # load zones
    s = SessionLocal()
    for z in s.query(MonitoringZone).all():
        zones_cache.append({"id":z.id,"name":z.name,"zone_type":z.zone_type,
                           "points":json.loads(z.points),"enabled":z.enabled})
    s.close()
    ai_engine.set_zones_provider(lambda: zones_cache)

@app.on_event("shutdown")
async def shutdown():
    if ai_engine: ai_engine.stop()
    camera.disconnect()

# --- Camera endpoints ---
class ConnectReq(BaseModel):
    device_index: int = 0

@app.get("/api/v1/camera/devices")
def camera_devices():
    return {"devices": camera.discover()}

@app.get("/api/v1/camera/status")
def camera_status():
    return camera.status()

@app.post("/api/v1/camera/connect")
def camera_connect(req: ConnectReq):
    ok = camera.connect(req.device_index, SessionLocal())
    if ok:
        broadcast({"type":"camera_status","status":camera.status()})
    return {"ok": ok, "status": camera.status()}

@app.post("/api/v1/camera/disconnect")
def camera_disconnect():
    camera.disconnect()
    broadcast({"type":"camera_status","status":camera.status()})
    return {"ok": True, "status": camera.status()}

@app.post("/api/v1/camera/reconnect")
def camera_reconnect():
    ok = camera.reconnect()
    broadcast({"type":"camera_status","status":camera.status()})
    return {"ok": ok, "status": camera.status()}

@app.get("/api/v1/camera/diagnostics")
def camera_diagnostics():
    return camera.diagnostics()

def mjpeg_gen(get_frame_func, overlay=False):
    while True:
        if overlay and ai_engine is not None and ai_engine.running:
            data = ai_engine.get_annotated_jpeg()
        else:
            snap = camera.snapshot_jpeg(80)
            data = snap
        if data is None:
            time.sleep(0.1); continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n")
        time.sleep(0.05)

@app.get("/api/v1/camera/preview.mjpg")
def camera_preview():
    return StreamingResponse(mjpeg_gen(lambda: None, overlay=False), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/v1/camera/snapshot")
def camera_snapshot():
    data = camera.snapshot_jpeg(90)
    if data is None:
        raise HTTPException(404, "no frame")
    return Response(content=data, media_type="image/jpeg")

@app.get("/api/v1/camera/preview_annotated.mjpg")
def camera_preview_annotated():
    return StreamingResponse(mjpeg_gen(None, overlay=True), media_type="multipart/x-mixed-replace; boundary=frame")

# --- AI endpoints ---
@app.get("/api/v1/ai/status")
def ai_status():
    return {"running": ai_engine.running if ai_engine else False,
            "model_loaded": ai_engine.metrics.get("model_loaded") if ai_engine else False,
            "model_error": ai_engine.model_error if ai_engine else None,
            "metrics": ai_engine.metrics if ai_engine else {}}

@app.post("/api/v1/ai/start")
def ai_start():
    ok = ai_engine.start() if ai_engine else False
    broadcast({"type":"ai_status","running": ai_engine.running if ai_engine else False})
    return {"ok": ok, "status": ai_status()}

@app.post("/api/v1/ai/stop")
def ai_stop():
    if ai_engine: ai_engine.stop()
    broadcast({"type":"ai_status","running": False})
    return {"ok": True}

@app.get("/api/v1/ai/metrics")
def ai_metrics():
    return ai_engine.metrics if ai_engine else {}

@app.get("/api/v1/ai/detections")
def ai_detections():
    dets, m = ai_engine.get_raw_detections() if ai_engine else ([],{})
    return {"detections": dets, "metrics": m}

@app.get("/api/v1/ai/tracks")
def ai_tracks():
    return {"tracks": ai_engine.get_tracks() if ai_engine else []}

@app.get("/api/v1/ai/observations")
def ai_observations():
    return {"observations": ai_engine.get_observations() if ai_engine else []}

@app.get("/api/v1/ai/preview.mjpg")
def ai_preview():
    return StreamingResponse(mjpeg_gen(None, overlay=True), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/v1/ai/heatmap")
def ai_heatmap(window: int = Query(300)):
    if not ai_engine: return {"error":"no engine"}
    return ai_engine.get_heatmap(window)

@app.post("/api/v1/ai/heatmap/reset")
def ai_heatmap_reset():
    if ai_engine: ai_engine.reset_heatmap()
    return {"ok": True}

@app.post("/api/v1/ai/test-observation")
def ai_test_observation():
    if not ai_engine: raise HTTPException(500,"no engine")
    obs, iid = ai_engine.create_test_observation()
    return {"observation": obs, "incident_id": iid}

# --- Zones ---
class ZoneReq(BaseModel):
    name: str
    zone_type: str
    points: list
    enabled: bool = True

@app.get("/api/v1/zones")
def zones_list():
    return {"zones": zones_cache}

@app.post("/api/v1/zones")
def zones_create(req: ZoneReq):
    s=SessionLocal()
    z=MonitoringZone(name=req.name, zone_type=req.zone_type, points=json.dumps(req.points), enabled=req.enabled)
    s.add(z); s.commit(); s.refresh(z); s.close()
    obj={"id":z.id,"name":req.name,"zone_type":req.zone_type,"points":req.points,"enabled":req.enabled}
    zones_cache.append(obj)
    return obj

@app.patch("/api/v1/zones/{zid}")
def zones_patch(zid: int, req: dict):
    s=SessionLocal()
    z=s.query(MonitoringZone).filter(MonitoringZone.id==zid).first()
    if not z:
        s.close(); raise HTTPException(404)
    if "name" in req: z.name=req["name"]
    if "zone_type" in req: z.zone_type=req["zone_type"]
    if "points" in req: z.points=json.dumps(req["points"])
    if "enabled" in req: z.enabled=req["enabled"]
    s.commit(); s.close()
    # update cache
    for c in zones_cache:
        if c["id"]==zid:
            if "name" in req: c["name"]=req["name"]
            if "zone_type" in req: c["zone_type"]=req["zone_type"]
            if "points" in req: c["points"]=req["points"]
            if "enabled" in req: c["enabled"]=req["enabled"]
    return {"ok": True}

@app.delete("/api/v1/zones/{zid}")
def zones_delete(zid: int):
    s=SessionLocal()
    s.query(MonitoringZone).filter(MonitoringZone.id==zid).delete()
    s.commit(); s.close()
    global zones_cache
    zones_cache=[c for c in zones_cache if c["id"]!=zid]
    return {"ok": True}

# --- Incidents ---
def _incident_to_dict(inc):
    return {"id":inc.id,"severity":inc.severity,"status":inc.status,
            "created_at":inc.created_at.isoformat() if inc.created_at else None,
            "track_id":inc.track_id,"observation_id":inc.observation_id,
            "frame_ref":inc.frame_ref,"ai_version":inc.ai_version,"notes":inc.notes}

@app.get("/api/v1/incidents")
def incidents_list(status: str = None, severity: str = None, q: str = None):
    s=SessionLocal()
    qry=s.query(Incident)
    if status: qry=qry.filter(Incident.status==status)
    if severity: qry=qry.filter(Incident.severity==severity)
    items=qry.order_by(Incident.created_at.desc()).all()
    if q:
        items=[i for i in items if q.lower() in (i.notes or "").lower() or q in str(i.id)]
    out=[_incident_to_dict(i) for i in items]
    s.close()
    return {"incidents": out}

@app.get("/api/v1/incidents/{iid}")
def incident_detail(iid: int):
    s=SessionLocal()
    inc=s.query(Incident).filter(Incident.id==iid).first()
    if not inc:
        s.close(); raise HTTPException(404)
    evs=s.query(IncidentEvidence).filter(IncidentEvidence.incident_id==iid).all()
    tml=s.query(IncidentTimeline).filter(IncidentTimeline.incident_id==iid).order_by(IncidentTimeline.ts).all()
    d=_incident_to_dict(inc)
    d["evidence"]=[{"id":e.id,"kind":e.kind,"path":e.path,"meta":e.meta} for e in evs]
    d["timeline"]=[{"id":t.id,"ts":t.ts.isoformat(),"action":t.action,"detail":t.detail} for t in tml]
    s.close()
    return d

class NoteReq(BaseModel):
    note: str

def _add_timeline(s, iid, action, detail):
    tl=IncidentTimeline(incident_id=iid, action=action, detail=detail)
    s.add(tl)

@app.post("/api/v1/incidents/{iid}/acknowledge")
def incident_ack(iid: int):
    s=SessionLocal()
    inc=s.query(Incident).filter(Incident.id==iid).first()
    if not inc: s.close(); raise HTTPException(404)
    inc.status="ACKNOWLEDGED"
    _add_timeline(s,iid,"ACKNOWLEDGED","Incident acknowledged by operator.")
    s.commit(); s.close()
    broadcast({"type":"incident_updated","id":iid,"status":"ACKNOWLEDGED"})
    return {"ok": True}

@app.post("/api/v1/incidents/{iid}/resolve")
def incident_resolve(iid: int):
    s=SessionLocal()
    inc=s.query(Incident).filter(Incident.id==iid).first()
    if not inc: s.close(); raise HTTPException(404)
    inc.status="RESOLVED"
    _add_timeline(s,iid,"RESOLVED","Incident resolved.")
    s.commit(); s.close()
    broadcast({"type":"incident_updated","id":iid,"status":"RESOLVED"})
    return {"ok": True}

@app.post("/api/v1/incidents/{iid}/false-alarm")
def incident_false(iid: int):
    s=SessionLocal()
    inc=s.query(Incident).filter(Incident.id==iid).first()
    if not inc: s.close(); raise HTTPException(404)
    inc.status="FALSE ALARM"
    _add_timeline(s,iid,"FALSE_ALARM","Marked as false alarm.")
    s.commit(); s.close()
    broadcast({"type":"incident_updated","id":iid,"status":"FALSE ALARM"})
    return {"ok": True}

@app.post("/api/v1/incidents/{iid}/notes")
def incident_note(iid: int, req: NoteReq):
    s=SessionLocal()
    inc=s.query(Incident).filter(Incident.id==iid).first()
    if not inc: s.close(); raise HTTPException(404)
    inc.notes = (inc.notes or "") + "\n" + req.note
    _add_timeline(s,iid,"NOTE", req.note)
    s.commit(); s.close()
    return {"ok": True}

@app.get("/api/v1/incidents/{iid}/timeline")
def incident_timeline(iid: int):
    s=SessionLocal()
    tml=s.query(IncidentTimeline).filter(IncidentTimeline.incident_id==iid).order_by(IncidentTimeline.ts).all()
    out=[{"id":t.id,"ts":t.ts.isoformat(),"action":t.action,"detail":t.detail} for t in tml]
    s.close()
    return {"timeline": out}

# --- WS ---
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get("/api/v1/system/status")
def system_status():
    return {"app":"Sea Sentry AI","mode":"LOCAL DEVELOPMENT","ai_running": ai_engine.running if ai_engine else False,
            "camera": camera.status()}
