import threading, time, cv2, numpy as np
from collections import deque
from .config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

STATES = ["DISCONNECTED","DISCOVERING","CONNECTING","CONNECTED","DEGRADED","ERROR"]

class CameraManager:
    def __init__(self):
        self.device_index = None
        self.cap = None
        self.state = "DISCONNECTED"
        self.lock = threading.Lock()
        self.latest_frame = None  # BGR ndarray
        self.latest_ts = None
        self.frame_count = 0
        self._thread = None
        self._running = False
        self.actual_width = None
        self.actual_height = None
        self.actual_fps = None
        self.actual_fourcc = None
        self.errors = []
        self.session_id = None
        self._last_frame_ts = None
        self._fps_samples = deque(maxlen=60)
        self._inf_fps = None

    def discover(self):
        self.state = "DISCOVERING"
        devs = []
        for i in range(6):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret,_ = cap.read()
                    if ret:
                        devs.append({"index": i, "name": f"Camera {i}"})
                    cap.release()
                else:
                    cap.release()
            except Exception as e:
                self.errors.append(str(e))
        self.state = "DISCONNECTED"
        return devs

    def _fourcc_str(self, v):
        try:
            v=int(v)
            return "".join([chr((v>>(8*i))&0xFF) for i in range(4)])
        except Exception:
            return str(v)

    def connect(self, device_index=0, db_session=None):
        self.disconnect()
        self.state = "CONNECTING"
        self.device_index = device_index
        try:
            cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                # try MSMF
                cap.release()
                cap = cv2.VideoCapture(device_index, cv2.CAP_MSMF)
            if not cap.isOpened():
                self.state = "ERROR"
                self.errors.append("Unable to open camera")
                return False
            # negotiate
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            time.sleep(0.8)
            # if still low res, try YUY2 fallback automatically by reopening? We'll report actual
            self.cap = cap
            self.actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.actual_fps = float(cap.get(cv2.CAP_PROP_FPS))
            self.actual_fourcc = self._fourcc_str(cap.get(cv2.CAP_PROP_FOURCC))
            # verify frame
            ret, frame = cap.read()
            if not ret or frame is None:
                self.state = "ERROR"
                self.errors.append("No frames received")
                cap.release(); self.cap=None
                return False
            with self.lock:
                self.latest_frame = frame
                self.latest_ts = time.time()
            self.state = "CONNECTED"
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            # record session
            if db_session is not None:
                from .db import CameraSession
                cs = CameraSession(device_index=device_index, actual_width=self.actual_width,
                                   actual_height=self.actual_height, actual_fps=self.actual_fps,
                                   actual_fourcc=self.actual_fourcc, status="CONNECTED")
                db_session.add(cs); db_session.commit(); db_session.refresh(cs)
                self.session_id = cs.id
            return True
        except Exception as e:
            self.state = "ERROR"
            self.errors.append(str(e))
            return False

    def _loop(self):
        while self._running and self.cap is not None:
            t0 = time.time()
            ret, frame = self.cap.read()
            if not ret or frame is None:
                # degraded
                self.state = "DEGRADED"
                time.sleep(0.1)
                continue
            if self.state in ("DEGRADED","ERROR"):
                self.state = "CONNECTED"
            with self.lock:
                self.latest_frame = frame
                self.latest_ts = time.time()
            self.frame_count += 1
            self._fps_samples.append(time.time())
            # compute fps
            if len(self._fps_samples) >= 2:
                dt = self._fps_samples[-1]-self._fps_samples[0]
                if dt>0:
                    self.actual_fps = (len(self._fps_samples)-1)/dt
            time.sleep(0.001)

    def disconnect(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self.cap is not None:
            try: self.cap.release()
            except Exception: pass
            self.cap = None
        self.state = "DISCONNECTED"
        self.latest_frame = None

    def reconnect(self):
        idx = self.device_index if self.device_index is not None else 0
        return self.connect(idx)

    def get_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy(), self.latest_ts

    def snapshot_jpeg(self, quality=85):
        f = self.get_frame()
        if f is None: return None
        frame,_ = f
        ok,buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok: return None
        return buf.tobytes()

    def is_live(self):
        # frozen detection: frame timestamp recent
        with self.lock:
            if self.latest_ts is None: return False
            return (time.time()-self.latest_ts) < 2.0

    def status(self):
        return {
            "state": self.state,
            "device_index": self.device_index,
            "actual_width": self.actual_width,
            "actual_height": self.actual_height,
            "actual_fps": round(float(self.actual_fps),2) if self.actual_fps else None,
            "actual_fourcc": self.actual_fourcc,
            "frame_count": self.frame_count,
            "live": self.is_live(),
            "errors": self.errors[-5:],
        }

    def diagnostics(self):
        devs = self.discover()
        return {"devices": devs, "status": self.status()}
