import { useEffect, useState } from 'react';
const API = 'http://127.0.0.1:8000';

export default function AIPage() {
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [heatImg, setHeatImg] = useState<string | null>(null);
  const [window, setWindow] = useState(300);
  const [zones, setZones] = useState<any[]>([]);
  const [observations, setObservations] = useState<any[]>([]);
  const [newZoneName, setNewZoneName] = useState('');
  const [newZoneType, setNewZoneType] = useState('observation');

  const refresh = async () => {
    setAiStatus(await fetch(`${API}/api/v1/ai/status`).then(r=>r.json()));
    setZones((await fetch(`${API}/api/v1/zones`).then(r=>r.json())).zones || []);
    setObservations((await fetch(`${API}/api/v1/ai/observations`).then(r=>r.json())).observations || []);
  };
  useEffect(() => { refresh(); const t=setInterval(refresh,3000); return ()=>clearInterval(t); }, []);

  useEffect(() => {
    const t = setInterval(async () => {
      try {
        const h = await fetch(`${API}/api/v1/ai/heatmap?window=${window}`).then(r=>r.json());
        if (h.image_base64) setHeatImg(`data:image/png;base64,${h.image_base64}`);
      } catch {}
    }, 2500);
    return () => clearInterval(t);
  }, [window]);

  const start = async () => { await fetch(`${API}/api/v1/ai/start`, {method:'POST'}); refresh(); };
  const stop = async () => { await fetch(`${API}/api/v1/ai/stop`, {method:'POST'}); refresh(); };
  const resetHeat = async () => { await fetch(`${API}/api/v1/ai/heatmap/reset`, {method:'POST'}); };
  const testObs = async () => { await fetch(`${API}/api/v1/ai/test-observation`, {method:'POST'}); alert('Test observation created'); };

  const addZone = async () => {
    // default a small central polygon
    const pts = [[0.4,0.4],[0.6,0.4],[0.6,0.6],[0.4,0.6]];
    await fetch(`${API}/api/v1/zones`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:newZoneName||'Zone',zone_type:newZoneType,points:pts,enabled:true})});
    setNewZoneName(''); refresh();
  };
  const delZone = async (id:number) => { await fetch(`${API}/api/v1/zones/${id}`, {method:'DELETE'}); refresh(); };

  return (
    <div>
      <h2 style={{ margin:'0 0 16px', fontFamily:'Instrument Serif, serif', fontSize:28 }}>AI & Heat Map</h2>
      <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginBottom:16 }}>
        <button className="btn btn-primary" onClick={start}>Start AI</button>
        <button className="btn btn-ghost" onClick={stop}>Stop AI</button>
        <button className="btn btn-ghost" onClick={resetHeat}>Reset Heat Map</button>
        <button className="btn btn-ghost" onClick={testObs}>Create Test Observation</button>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        <div className="card">
          <div style={{ fontWeight:600, marginBottom:8 }}>Activity Heat Map</div>
          <select value={window} onChange={e=>setWindow(Number(e.target.value))} style={{ padding:6, borderRadius:8, border:'1px solid var(--stone)', marginBottom:8 }}>
            <option value={60}>1 min</option>
            <option value={300}>5 min</option>
            <option value={900}>15 min</option>
            <option value={1800}>30 min</option>
          </select>
          {heatImg ? <img src={heatImg} alt="heatmap" style={{ width:'100%', borderRadius:8 }} /> : <div className="empty">No data yet</div>}
          <div style={{ fontSize:12, opacity:.6, marginTop:8 }}>EXPERIMENTAL — activity density, not thermal.</div>
        </div>
        <div className="card">
          <div style={{ fontWeight:600, marginBottom:8 }}>Monitoring Zones</div>
          <div style={{ display:'flex', gap:8, marginBottom:10 }}>
            <input placeholder="Name" value={newZoneName} onChange={e=>setNewZoneName(e.target.value)} style={{ flex:1, padding:8, borderRadius:8, border:'1px solid var(--stone)' }} />
            <select value={newZoneType} onChange={e=>setNewZoneType(e.target.value)} style={{ padding:8, borderRadius:8, border:'1px solid var(--stone)' }}>
              <option value="observation">Observation</option>
              <option value="swimming">Swimming</option>
              <option value="restricted">Restricted</option>
              <option value="ignore">Ignore</option>
            </select>
            <button className="btn btn-primary" onClick={addZone}>Add</button>
          </div>
          {zones.length===0 ? <div className="empty">No zones</div> : (
            <table className="incident-table">
              <thead><tr><th>Name</th><th>Type</th><th>Enabled</th><th></th></tr></thead>
              <tbody>
                {zones.map((z:any) => (
                  <tr key={z.id}><td>{z.name}</td><td className="mono-val">{z.zone_type}</td><td>{z.enabled?'yes':'no'}</td>
                    <td><button onClick={()=>delZone(z.id)} style={{ background:'none', border:'none', color:'var(--coral)' }}>del</button></td></tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      <div className="card" style={{ marginTop:16 }}>
        <div style={{ fontWeight:600, marginBottom:8 }}>Behavior Observations</div>
        {observations.length===0 ? <div className="empty">No observations</div> : (
          <div style={{ display:'grid', gap:8 }}>
            {observations.slice(0,20).map((o:any) => (
              <div key={o.id} style={{ padding:10, border:'1px solid var(--stone)', borderRadius:8, fontSize:13 }}>
                <div style={{ fontWeight:600 }}>#{o.id} {o.obs_type} (level {o.level})</div>
                <div className="mono-val" style={{ fontSize:11, opacity:.6 }}>track {o.track_id ?? '—'} · {o.ts?.slice(0,19)}</div>
                <div style={{ marginTop:4, opacity:.8 }}>{o.explanation}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="card" style={{ marginTop:16 }}>
        <div style={{ fontWeight:600, marginBottom:8 }}>AI Status</div>
        <pre className="mono" style={{ fontSize:11, whiteSpace:'pre-wrap' }}>{JSON.stringify(aiStatus,null,2)}</pre>
      </div>
    </div>
  );
}
