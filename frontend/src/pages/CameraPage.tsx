import { useEffect, useState } from 'react';
const API = 'http://127.0.0.1:8000';

export default function CameraPage() {
  const [devices, setDevices] = useState<any[]>([]);
  const [status, setStatus] = useState<any>(null);
  const [diag, setDiag] = useState<any>(null);
  const [selected, setSelected] = useState(0);

  const refresh = async () => {
    setDevices((await fetch(`${API}/api/v1/camera/devices`).then(r=>r.json())).devices || []);
    setStatus(await fetch(`${API}/api/v1/camera/status`).then(r=>r.json()));
  };
  useEffect(() => { refresh(); }, []);

  const connect = async () => { await fetch(`${API}/api/v1/camera/connect`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_index:selected})}); refresh(); };
  const disconnect = async () => { await fetch(`${API}/api/v1/camera/disconnect`, {method:'POST'}); refresh(); };
  const reconnect = async () => { await fetch(`${API}/api/v1/camera/reconnect`, {method:'POST'}); refresh(); };
  const diagnostics = async () => { setDiag(await fetch(`${API}/api/v1/camera/diagnostics`).then(r=>r.json())); };

  return (
    <div>
      <h2 style={{ margin:'0 0 16px', fontFamily:'Instrument Serif, serif', fontSize:28 }}>Camera & AI</h2>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        <div className="card">
          <div style={{ fontWeight:600, marginBottom:10 }}>Devices</div>
          <select value={selected} onChange={e=>setSelected(Number(e.target.value))} style={{ width:'100%', padding:8, borderRadius:8, border:'1px solid var(--stone)', marginBottom:10 }}>
            {devices.length===0 && <option value={0}>No devices</option>}
            {devices.map(d => <option key={d.index} value={d.index}>{d.name} (index {d.index})</option>)}
          </select>
          <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
            <button className="btn btn-primary" onClick={connect}>Connect</button>
            <button className="btn btn-ghost" onClick={disconnect}>Disconnect</button>
            <button className="btn btn-ghost" onClick={reconnect}>Reconnect</button>
            <button className="btn btn-ghost" onClick={diagnostics}>Diagnostics</button>
          </div>
        </div>
        <div className="card inspector">
          <div style={{ fontWeight:600, marginBottom:10 }}>Status</div>
          <div className="row"><span>State</span><span className="mono-val">{status?.state}</span></div>
          <div className="row"><span>Index</span><span className="mono-val">{status?.device_index}</span></div>
          <div className="row"><span>Resolution</span><span className="mono-val">{status?.actual_width}×{status?.actual_height}</span></div>
          <div className="row"><span>FPS</span><span className="mono-val">{status?.actual_fps}</span></div>
          <div className="row"><span>FourCC</span><span className="mono-val">{status?.actual_fourcc}</span></div>
          <div className="row"><span>Live</span><span className="mono-val">{status?.live?'YES':'NO'}</span></div>
          <div className="row"><span>Frames</span><span className="mono-val">{status?.frame_count}</span></div>
        </div>
      </div>
      {diag && (
        <div className="card" style={{ marginTop:16 }}>
          <div style={{ fontWeight:600, marginBottom:8 }}>Diagnostics</div>
          <pre className="mono" style={{ fontSize:11, whiteSpace:'pre-wrap' }}>{JSON.stringify(diag,null,2)}</pre>
        </div>
      )}
      {status?.errors?.length>0 && (
        <div className="card" style={{ marginTop:16, color:'var(--coral)' }}>
          {status.errors.map((e:string,i:number)=><div key={i}>{e}</div>)}
        </div>
      )}
    </div>
  );
}
