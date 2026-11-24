import { useEffect, useState } from 'react';
const API = 'http://127.0.0.1:8000';

export default function Incidents() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [filter, setFilter] = useState<string>('');

  const load = async () => {
    const url = filter ? `${API}/api/v1/incidents?status=${encodeURIComponent(filter)}` : `${API}/api/v1/incidents`;
    const j = await fetch(url).then(r=>r.json());
    setIncidents(j.incidents || []);
  };
  useEffect(() => { load(); const t=setInterval(load,3000); return ()=>clearInterval(t); }, [filter]);

  const open = async (id: number) => {
    const j = await fetch(`${API}/api/v1/incidents/${id}`).then(r=>r.json());
    setSelected(j);
  };

  const act = async (id: number, action: string, body?: any) => {
    await fetch(`${API}/api/v1/incidents/${id}/${action}`, { method:'POST', headers:{'Content-Type':'application/json'}, body: body?JSON.stringify(body):undefined });
    open(id); load();
  };

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
        <h2 style={{ margin:0, fontFamily:'Instrument Serif, serif', fontSize:28 }}>Incident Desk</h2>
        <select value={filter} onChange={e=>setFilter(e.target.value)} style={{ padding:8, borderRadius:8, border:'1px solid var(--stone)' }}>
          <option value="">All</option>
          <option value="NEW">NEW</option>
          <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
          <option value="RESOLVED">RESOLVED</option>
          <option value="FALSE ALARM">FALSE ALARM</option>
        </select>
      </div>
      <div style={{ display:'grid', gridTemplateColumns: selected?'1.2fr 1fr':'1fr', gap:16 }}>
        <div className="card" style={{ padding:0 }}>
          {incidents.length===0 ? <div className="empty">No incidents</div> : (
            <table className="incident-table">
              <thead><tr><th>ID</th><th>Severity</th><th>Status</th><th>Track</th><th>Created</th></tr></thead>
              <tbody>
                {incidents.map(i => (
                  <tr key={i.id} style={{ cursor:'pointer' }} onClick={()=>open(i.id)}>
                    <td className="mono-val">#{i.id}</td>
                    <td>{i.severity}</td>
                    <td><span className={`badge badge-${i.status==='NEW'?'new':i.status==='ACKNOWLEDGED'?'ack':'res'}`}>{i.status}</span></td>
                    <td className="mono-val">{i.track_id ?? '—'}</td>
                    <td className="mono-val" style={{ fontSize:11 }}>{i.created_at?.slice(0,19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {selected && (
          <div className="card">
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <div className="serif" style={{ fontSize:22 }}>Incident #{selected.id}</div>
              <button onClick={()=>setSelected(null)} style={{ background:'none', border:'none', fontSize:18 }}>×</button>
            </div>
            <div className="inspector" style={{ marginTop:12 }}>
              <div className="row"><span>Status</span><span className="mono-val">{selected.status}</span></div>
              <div className="row"><span>Severity</span><span className="mono-val">{selected.severity}</span></div>
              <div className="row"><span>Track</span><span className="mono-val">{selected.track_id ?? '—'}</span></div>
              <div className="row"><span>AI version</span><span className="mono-val">{selected.ai_version}</span></div>
              <div className="row"><span>Created</span><span className="mono-val">{selected.created_at}</span></div>
            </div>
            {selected.frame_ref && (
              <div style={{ marginTop:12 }}>
                <img src={`${API}/data/evidence/${selected.frame_ref}`} alt="evidence" style={{ width:'100%', borderRadius:8 }} onError={(e)=>{(e.target as any).style.display='none';}} />
              </div>
            )}
            <div style={{ marginTop:12, display:'flex', gap:8, flexWrap:'wrap' }}>
              <button className="btn btn-ghost" onClick={()=>act(selected.id,'acknowledge')}>Acknowledge</button>
              <button className="btn btn-ghost" onClick={()=>act(selected.id,'resolve')}>Resolve</button>
              <button className="btn btn-ghost" onClick={()=>act(selected.id,'false-alarm')}>False Alarm</button>
            </div>
            <div style={{ marginTop:12 }}>
              <input placeholder="Add note" onKeyDown={async (e)=>{ if(e.key==='Enter'){ await act(selected.id,'notes',{note:(e.target as any).value}); (e.target as any).value=''; } }} style={{ width:'100%', padding:8, borderRadius:8, border:'1px solid var(--stone)' }} />
            </div>
            <div style={{ marginTop:12 }}>
              <div style={{ fontWeight:600, marginBottom:6, fontSize:13 }}>Timeline</div>
              {(selected.timeline||[]).map((t:any)=>(
                <div key={t.id} style={{ fontSize:12, padding:'6px 0', borderBottom:'1px solid var(--stone)' }}>
                  <span className="mono-val">{t.ts?.slice(0,19)}</span> — <b>{t.action}</b> {t.detail}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
