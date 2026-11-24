import threading, time, os, json, cv2, numpy as np
from collections import deque, defaultdict
from datetime import datetime
from ultralytics import YOLO
from .config import MODEL_PATH, AI_IMGSZ, AI_TARGET_FPS, AI_CONF, HEATMAP_GRID, DATA_DIR
from .camera import CameraManager

MODEL_VERSION = "yolov8n.pt"

class AIEngine:
    def __init__(self, camera: CameraManager, db_session_factory, ws_broadcast):
        self.camera = camera
        self.db = db_session_factory
        self.ws = ws_broadcast
        self.model = None
        self.model_error = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.latest_annotated = None  # BGR
        self.latest_detections = []
        self.tracks = {}  # track_id -> dict
        self.track_history = defaultdict(lambda: deque(maxlen=300))  # track_id -> deque of (ts,cx,cy)
        self.observations = deque(maxlen=200)
        self.heat_events = deque(maxlen=20000)  # (ts, xn, yn)
        self.metrics = {
            "inference_fps": 0.0,
            "inference_latency_ms": None,
            "frames_processed": 0,
            "model_loaded": False,
            "model_version": MODEL_VERSION,
            "device": "CPU",
        }
        self._fps_samples = deque(maxlen=30)
        self._last_heat_add = defaultdict(float)
        self._last_incident_by_track = defaultdict(float)
        self._last_observation_by_track = defaultdict(float)
        self.zones_provider = None  # callable returns list zones
        self._stop = False

    def load_model(self):
        try:
            self.model = YOLO(str(MODEL_PATH))
            self.metrics["model_loaded"] = True
        except Exception as e:
            self.model_error = str(e)
            self.metrics["model_loaded"] = False

    def set_zones_provider(self, fn):
        self.zones_provider = fn

    def start(self):
        if self.running: return True
        if self.model is None:
            self.load_model()
        if self.model is None:
            return False
        self._stop = False
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self._stop = True
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=3)
            self.thread = None

    def _loop(self):
        period = 1.0 / max(1, AI_TARGET_FPS)
        while not self._stop:
            t0 = time.time()
            frame_pack = self.camera.get_frame()
            if frame_pack is None:
                time.sleep(0.1); continue
            frame, fts = frame_pack
            try:
                res = self.model.track(frame, persist=True, classes=[0], conf=AI_CONF,
                                      imgsz=AI_IMGSZ, verbose=False, tracker="bytetrack.yaml")
            except Exception as e:
                self.model_error = str(e)
                time.sleep(0.5); continue
            t1 = time.time()
            latency = (t1-t0)*1000.0
            # parse
            detections = []
            annotated = frame.copy()
            h,w = frame.shape[:2]
            if res and len(res)>0:
                r = res[0]
                boxes = r.boxes
                if boxes is not None and boxes.id is not None:
                    ids = boxes.id.cpu().numpy().astype(int)
                    xyxy = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    for i,tid in enumerate(ids):
                        x1,y1,x2,y2 = xyxy[i]
                        conf = float(confs[i])
                        cx = (x1+x2)/2.0; cy=(y1+y2)/2.0
                        detections.append({"track_id": int(tid), "bbox":[float(x1),float(y1),float(x2),float(y2)],
                                          "conf": conf, "cx": float(cx), "cy": float(cy)})
                        # draw
                        cv2.rectangle(annotated,(int(x1),int(y1)),(int(x2),int(y2)),(129,151,138),2)
                        cv2.putText(annotated, f"ID {tid}", (int(x1),int(y1)-6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (129,151,138),1)
                        # trail
                        self.track_history[int(tid)].append((time.time(), float(cx)/w, float(cy)/h,
                                                            float(x2-x1)/w, float(y2-y1)/h, float(conf)))
                        # update track meta
                        tr = self.tracks.setdefault(int(tid), {"track_id":int(tid),"first_seen":time.time(),"last_seen":time.time(),
                                                              "points":0,"missing":0})
                        tr["last_seen"]=time.time()
                        tr["points"]+=1
                        # heat event (throttled per track)
                        now=time.time()
                        if now-self._last_heat_add[int(tid)] > 0.5:
                            self._last_heat_add[int(tid)]=now
                            self.heat_events.append((now, float(cx)/w, float(cy)/h))
                elif boxes is not None:
                    xyxy = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    for i in range(len(xyxy)):
                        x1,y1,x2,y2 = xyxy[i]
                        detections.append({"track_id": None, "bbox":[float(x1),float(y1),float(x2),float(y2)],
                                          "conf": float(confs[i]), "cx": float((x1+x2)/2), "cy": float((y1+y2)/2)})
            # behavior analysis
            self._behavior_analysis(detections, h, w, annotated)
            with self.lock:
                self.latest_annotated = annotated
                self.latest_detections = detections
                self.metrics["frames_processed"] += 1
                self.metrics["inference_latency_ms"] = round(latency,1)
                self._fps_samples.append(time.time())
                if len(self._fps_samples)>=2:
                    dt=self._fps_samples[-1]-self._fps_samples[0]
                    if dt>0:
                        self.metrics["inference_fps"]=round((len(self._fps_samples)-1)/dt,2)
            # broadcast via ws (throttled maybe)
            try:
                import asyncio
            except Exception:
                pass
            self.ws({"type":"ai_update","detections":detections,"metrics":self.metrics})
            elapsed=time.time()-t0
            sleep=period-elapsed
            if sleep>0: time.sleep(sleep)

    def _zones(self):
        if self.zones_provider:
            try: return self.zones_provider()
            except Exception: return []
        return []

    def _in_zone(self, xn, yn, zone):
        pts = zone.get("points",[])
        if len(pts)<3: return False
        # ray casting
        poly=[(p[0],p[1]) for p in pts]
        inside=False
        j=len(poly)-1
        for i in range(len(poly)):
            xi,yi=poly[i]; xj,yj=poly[j]
            if ((yi>yn)!=(yj>yn)) and (xn < (xj-xi)*(yn-yi)/(yj-yi)+xi):
                inside = not inside
            j=i
        return inside

    def _behavior_analysis(self, detections, h, w, annotated):
        now = time.time()
        zones = self._zones()
        swimming_zones = [z for z in zones if z.get("zone_type") == "swimming" and z.get("enabled", True)]
        observation_zones = [z for z in zones if z.get("zone_type") in ("observation", "swimming") and z.get("enabled", True)]
        for d in detections:
            tid = d["track_id"]
            if tid is None:
                continue
            tr = self.tracks.get(tid)
            if tr is None:
                continue
            hist = list(self.track_history[tid])
            if len(hist) < 8:
                continue
            # features
            xs = [p[1] for p in hist]
            ys = [p[2] for p in hist]
            ws = [p[3] for p in hist]
            hs = [p[4] for p in hist]
            ts = [p[0] for p in hist]
            # displacement & velocity
            dx = xs[-1] - xs[0]
            dy = ys[-1] - ys[0]
            disp = (dx*dx + dy*dy) ** 0.5
            dur = ts[-1] - ts[0]
            if dur <= 0:
                continue
            speed = disp / dur
            # direction changes
            dirs = []
            for i in range(1, len(xs)):
                dirs.append((xs[i]-xs[i-1], ys[i]-ys[i-1]))
            turns = 0
            for i in range(1, len(dirs)):
                if dirs[i-1][0]*dirs[i][0] + dirs[i-1][1]*dirs[i][1] < 0:
                    turns += 1
            turn_rate = turns / max(1, len(dirs)-1)
            # bbox aspect ratio variability
            ars = [ (ws[i]/hs[i]) if hs[i] > 0 else 0 for i in range(len(ws)) ]
            ar_std = float(np.std(ars)) if len(ars) > 1 else 0.0
            # movement variability (std of step sizes)
            steps = [((xs[i]-xs[i-1])**2 + (ys[i]-ys[i-1])**2)**0.5 for i in range(1, len(xs))]
            step_std = float(np.std(steps)) if len(steps) > 1 else 0.0
            # dwell in zone
            xn, yn = xs[-1], ys[-1]
            in_swim = any(self._in_zone(xn, yn, z) for z in swimming_zones) if swimming_zones else False
            in_obs = any(self._in_zone(xn, yn, z) for z in observation_zones) if observation_zones else True
            # recent stillness
            recent = hist[-8:]
            rxs = [p[1] for p in recent]; rys = [p[2] for p in recent]
            span = ((max(rxs)-min(rxs))**2 + (max(rys)-min(rys))**2) ** 0.5
            recent_dur = recent[-1][0] - recent[0][0]
            features = {
                "duration": round(float(dur), 2),
                "displacement": round(float(disp), 4),
                "speed": round(float(speed), 4),
                "turn_rate": round(float(turn_rate), 3),
                "bbox_aspect_std": round(float(ar_std), 4),
                "step_std": round(float(step_std), 4),
                "recent_span": round(float(span), 4),
                "in_swimming_zone": bool(in_swim),
            }
            # thresholds
            thresholds = {
                "min_track_points": 8,
                "stillness_span": 0.03,
                "stillness_duration": 8.0,
                "erratic_turn_rate": 0.55,
            }
            # Level determination
            level = 1
            obs_type = None
            explanation = ""
            if turn_rate >= thresholds["erratic_turn_rate"] and speed > 0.01 and in_obs:
                level = 2
                obs_type = "ERRATIC_MOVEMENT_PATTERN"
                explanation = "High direction-change rate over recent track history."
            if in_swim and span <= thresholds["stillness_span"] and recent_dur >= thresholds["stillness_duration"]:
                level = 3
                obs_type = "PROLONGED_INACTIVITY_IN_ZONE"
                explanation = "Track remained nearly stationary in a configured swimming zone for an extended period."
            if obs_type is None:
                continue
            if now - self._last_observation_by_track.get((tid, obs_type), 0) < 10:
                continue
            # dedup per track
            if now - self._last_incident_by_track.get(tid, 0) < 120 and level == 3:
                continue
            if level == 3:
                self._last_incident_by_track[tid] = now
            self._last_observation_by_track[(tid, obs_type)] = now
            obs = self._create_observation(tid, obs_type, recent_dur if level == 3 else dur, features, None,
                                          level, thresholds, explanation)
            if level == 3:
                self._maybe_incident(obs, tid, None)
        # disappeared tracks
        for tid, tr in list(self.tracks.items()):
            if tr["last_seen"] < now - 4.0 and not tr.get("disappeared_notified"):
                if tr["points"] >= 12:
                    tr["disappeared_notified"] = True
                    features = {"points": tr["points"], "duration": round(tr["last_seen"]-tr["first_seen"], 2)}
                    obs = self._create_observation(tid, "TRACK_DISAPPEARANCE", now - tr["last_seen"], features, None,
                                                  2, {}, "Track disappeared after sustained observation.")
        cv2.putText(annotated, f"tracks:{len(detections)}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    def _create_observation(self, track_id, obs_type, duration, features, frame_ref,
                            level=1, thresholds=None, explanation=""):
        from .db import BehavioralObservation, SessionLocal
        import json
        payload = {
            "level": level,
            "features": features,
            "thresholds": thresholds or {},
            "explanation": explanation,
            "status": "EXPERIMENTAL — HUMAN REVIEW REQUIRED",
        }
        obs = BehavioralObservation(track_id=track_id, obs_type=obs_type, duration=float(duration),
                                   features=json.dumps(payload), rule_version="exp-temporal-0.2",
                                   status="EXPERIMENTAL — HUMAN REVIEW REQUIRED")
        s = self.db()
        s.add(obs); s.commit(); s.refresh(obs)
        oid = obs.id
        s.close()
        o = {"id": oid, "track_id": track_id, "obs_type": obs_type, "duration": float(duration),
             "level": level, "features": features, "thresholds": thresholds or {},
             "explanation": explanation, "status": "EXPERIMENTAL — HUMAN REVIEW REQUIRED",
             "ts": datetime.utcnow().isoformat()}
        self.observations.appendleft(o)
        self.ws({"type": "observation", "observation": o})
        return o

    def _maybe_incident(self, obs, track_id, frame_ref):
        now=time.time()
        if now-self._last_incident_by_track.get(track_id,0) < 0: pass
        # dedup already handled by _last_incident_by_track set before
        # create incident
        import cv2
        # save snapshot
        path=None
        fpack=self.camera.get_frame()
        if fpack is not None:
            frame,_=fpack
            fname=f"incident_{int(now)}.jpg"
            fpath=str(DATA_DIR/"evidence"/fname)
            cv2.imwrite(fpath, frame)
            # annotated too
            if self.latest_annotated is not None:
                cv2.imwrite(str(DATA_DIR/"evidence"/("ann_"+fname)), self.latest_annotated)
            path=fname
        from .db import Incident, IncidentEvidence, IncidentTimeline, SessionLocal
        s=self.db()
        inc=Incident(severity="MEDIUM", status="NEW", track_id=track_id,
                    observation_id=obs.get("id"), frame_ref=path,
                    ai_version=MODEL_VERSION, notes="Experimental observation. Human review required.")
        s.add(inc); s.commit(); s.refresh(inc)
        # evidence
        ev=IncidentEvidence(incident_id=inc.id, kind="snapshot", path=path, meta=json.dumps({"track_id":track_id}))
        s.add(ev)
        tl=IncidentTimeline(incident_id=inc.id, action="CREATED", detail="Experimental observation triggered incident.")
        s.add(tl); s.commit()
        iid=inc.id
        s.close()
        inc_obj={"id":iid,"severity":"MEDIUM","status":"NEW","track_id":track_id,
                 "observation_id":obs.get("id"),"frame_ref":path,"created_at":datetime.utcnow().isoformat()}
        self.ws({"type":"incident_created","incident":inc_obj})
        return iid

    def get_annotated_jpeg(self):
        with self.lock:
            fr=self.latest_annotated
        if fr is None:
            f=self.camera.get_frame()
            if f is None: return None
            fr=f[0]
        ok,buf=cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY,80])
        if not ok: return None
        return buf.tobytes()

    def get_raw_detections(self):
        with self.lock:
            return list(self.latest_detections), dict(self.metrics)

    def get_tracks(self):
        now=time.time()
        out=[]
        for tid,tr in self.tracks.items():
            hist=list(self.track_history[tid])
            out.append({"track_id":tid,"first_seen":tr["first_seen"],"last_seen":tr["last_seen"],
                        "points":tr["points"],"duration":round(tr["last_seen"]-tr["first_seen"],2),
                        "recent": (now-tr["last_seen"])<2.0,
                        "trail": [(float(p[1]), float(p[2])) for p in hist[-60:]]})
        return out

    def get_observations(self):
        return list(self.observations)

    def get_heatmap(self, window_sec=300):
        now=time.time()
        cutoff=now-window_sec
        pts=[(p[1],p[2]) for p in self.heat_events if p[0]>=cutoff]
        gw,gh=HEATMAP_GRID
        grid=np.zeros((gh,gw),dtype=np.float64)
        for xn,yn in pts:
            ix=min(gw-1,max(0,int(xn*gw)))
            iy=min(gh-1,max(0,int(yn*gh)))
            grid[iy,ix]+=1.0
        # gaussian smooth
        from scipy.ndimage import gaussian_filter
        grid=gaussian_filter(grid,sigma=1.2)
        # normalize
        mx=grid.max() if grid.max()>0 else 1.0
        norm=(grid/mx*255).astype(np.uint8)
        # colorize
        colored=cv2.applyColorMap(norm, cv2.COLORMAP_JET)
        # return as png base64? We'll encode jpeg
        ok,buf=cv2.imencode(".png", colored)
        import base64
        b64=base64.b64encode(buf.tobytes()).decode() if ok else None
        return {"window":window_sec,"points":len(pts),"image_base64":b64,"width":gw,"height":gh}

    def reset_heatmap(self):
        self.heat_events.clear()
        self._last_heat_add.clear()

    def create_test_observation(self):
        # explicitly labeled test
        obs=self._create_observation(None, "TEST_OBSERVATION", 0.0, {"test":True}, None)
        # create incident labeled test
        from .db import Incident, IncidentTimeline, SessionLocal
        s=self.db()
        inc=Incident(severity="LOW", status="NEW", track_id=None, observation_id=obs["id"],
                    frame_ref=None, ai_version=MODEL_VERSION,
                    notes="TEST incident created for verification. Not a real emergency.")
        s.add(inc); s.commit(); s.refresh(inc)
        tl=IncidentTimeline(incident_id=inc.id, action="CREATED", detail="Test incident for verification.")
        s.add(tl); s.commit(); iid=inc.id; s.close()
        self.ws({"type":"incident_created","incident":{"id":iid,"severity":"LOW","status":"NEW","track_id":None}})
        return obs, iid
