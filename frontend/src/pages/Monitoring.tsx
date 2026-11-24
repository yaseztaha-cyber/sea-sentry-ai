import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

const API = 'http://127.0.0.1:8000';

export default function Monitoring() {
  const { refresh } = useOutletContext<any>();
  const [cameraStatus, setCameraStatus] = useState<any>(null);
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [detections, setDetections] = useState<any[]>([]);
  const [tracks, setTracks] = useState<any[]>([]);
  const [mode, setMode] = useState<'raw' | 'ai'>('ai');
  const [showHeat, setShowHeat] = useState(false);
  const [heatImg, setHeatImg] = useState<string | null>(null);
  const [wsMsg, setWsMsg] = useState<string>('');

  const poll = async () => {
    try {
      const cs = await fetch(`${API}/api/v1/camera/status`).then(r=>r.json());
      setCameraStatus(cs);
      const as = await fetch(`${API}/api/v1/ai/status`).then(r=>r.json());
      setAiStatus(as);
      const d = await fetch(`${API}/api/v1/ai/detections`).then(r=>r.json());
      setDetections(d.detections || []);
      const t = await fetch(`${API}/api/v1/ai/tracks`).then(r=>r.json());
      setTracks(t.tracks || []);
    } catch {}
  };

  useEffect(() => { poll(); const t=setInterval(poll,2000); return ()=>clearInterval(t); }, []);

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    ws.onmessage = (e) => {
      try {
        const m = JSON.parse(e.data);
        if (m.type === 'incident_created') setWsMsg(`New incident #${m.incident?.id}`);
        if (m.type === 'ai_update') {
          // light update
        }
      } catch {}
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (!showHeat) { setHeatImg(null); return; }
    const t = setInterval(async () => {
      try {
        const h = await fetch(`${API}/api/v1/ai/heatmap?window=300`).then(r=>r.json());
        if (h.image_base64) setHeatImg(`data:image/png;base64,${h.image_base64}`);
      } catch {}
    }, 3000);
    return () => clearInterval(t);
  }, [showHeat]);

  const connectCam = async () => { await fetch(`${API}/api/v1/camera/connect`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_index:0})}); poll(); refresh(); };
  const disconnectCam = async () => { await fetch(`${API}/api/v1/camera/disconnect`, {method:'POST'}); poll(); refresh(); };
  const startAI = async () => { await fetch(`${API}/api/v1/ai/start`, {method:'POST'}); poll(); refresh(); };
  const stopAI = async () => { await fetch(`${API}/api/v1/ai/stop`, {method:'POST'}); poll(); refresh(); };

  // previewUrl removed
  const stablePreview = mode === 'ai' && aiStatus?.running
    ? `${API}/api/v1/ai/preview.mjpg`
    : `${API}/api/v1/camera/preview.mjpg`;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontFamily: 'Instrument Serif, serif', fontSize: 28 }}>Monitoring</h2>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button className="btn btn-ghost" onClick={connectCam}>Connect Camera</button>
          <button className="btn btn-ghost" onClick={disconnectCam}>Disconnect</button>
          <button className="btn btn-primary" onClick={startAI}>Start AI</button>
          <button className="btn btn-ghost" onClick={stopAI}>Stop AI</button>
        </div>
      </div>

      {wsMsg && <div style={{ background: 'var(--coral)', color: '#fff', padding: 10, borderRadius: 8, marginBottom: 12 }}>{wsMsg}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
        <div>
          <div className="video-box">
            {cameraStatus?.state === 'CONNECTED' ? (
              <img src={stablePreview} alt="camera preview" />
            ) : (
              <div className="empty" style={{ color: '#fff' }}>Camera not connected</div>
            )}
            {showHeat && heatImg && (
              <img src={heatImg} alt="heatmap" style={{ position: 'absolute', inset: 0, opacity: 0.45, mixBlendMode: 'screen', pointerEvents: 'none' }} />
            )}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
            <button className={`btn ${mode==='raw'?'btn-primary':'btn-ghost'}`} onClick={()=>setMode('raw')}>Raw Camera</button>
            <button className={`btn ${mode==='ai'?'btn-primary':'btn-ghost'}`} onClick={()=>setMode('ai')}>AI Annotated</button>
            <button className={`btn ${showHeat?'btn-primary':'btn-ghost'}`} onClick={()=>setShowHeat(!showHeat)}>Heat Map</button>
          </div>
        </div>
        <div className="card inspector">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Inspector</div>
          <div className="row"><span>Camera state</span><span className="mono-val">{cameraStatus?.state ?? '—'}</span></div>
          <div className="row"><span>Device index</span><span className="mono-val">{cameraStatus?.device_index ?? '—'}</span></div>
          <div className="row"><span>Resolution</span><span className="mono-val">{cameraStatus?.actual_width ?? '—'}×{cameraStatus?.actual_height ?? '—'}</span></div>
          <div className="row"><span>Capture FPS</span><span className="mono-val">{cameraStatus?.actual_fps ?? '—'}</span></div>
          <div className="row"><span>FourCC</span><span className="mono-val">{cameraStatus?.actual_fourcc ?? '—'}</span></div>
          <div className="row"><span>AI running</span><span className="mono-val">{aiStatus?.running ? 'YES' : 'NO'}</span></div>
          <div className="row"><span>Model</span><span className="mono-val">{aiStatus?.metrics?.model_version ?? '—'}</span></div>
          <div className="row"><span>Inference FPS</span><span className="mono-val">{aiStatus?.metrics?.inference_fps ?? '—'}</span></div>
          <div className="row"><span>Inference latency</span><span className="mono-val">{aiStatus?.metrics?.inference_latency_ms ?? '—'} ms</span></div>
          <div className="row"><span>People tracked</span><span className="mono-val">{detections.length}</span></div>
          <div className="row"><span>Frames processed</span><span className="mono-val">{aiStatus?.metrics?.frames_processed ?? 0}</span></div>
        </div>
      </div>

      <div style={{ marginTop: 16 }} className="card">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Tracks</div>
        {tracks.length === 0 ? <div className="empty">No tracks yet</div> : (
          <table className="incident-table">
            <thead><tr><th>ID</th><th>Duration</th><th>Points</th><th>Active</th></tr></thead>
            <tbody>
              {tracks.map(t => (
                <tr key={t.track_id}><td className="mono-val">{t.track_id}</td><td>{t.duration}s</td><td>{t.points}</td><td>{t.recent?'LIVE':'—'}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
