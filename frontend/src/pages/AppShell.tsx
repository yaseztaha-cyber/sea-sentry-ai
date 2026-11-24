import { NavLink, Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';

const API = 'http://127.0.0.1:8000';

export default function AppShell() {
  const [status, setStatus] = useState<any>(null);
  const [now, setNow] = useState(new Date());
  const [wsState, setWsState] = useState('connecting');

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    ws.onopen = () => setWsState('connected');
    ws.onclose = () => setWsState('disconnected');
    ws.onerror = () => setWsState('error');
    return () => ws.close();
  }, []);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const refresh = async () => {
    try {
      const r = await fetch(`${API}/api/v1/system/status`);
      const j = await r.json();
      setStatus(j);
    } catch { setStatus(null); }
  };
  useEffect(() => { refresh(); const t=setInterval(refresh,4000); return ()=>clearInterval(t); }, []);

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="serif" style={{ fontSize: 18, marginBottom: 24 }}>Sea Sentry</div>
        <NavLink to="/app" end className={({isActive})=>isActive?'active':''}>Monitoring</NavLink>
        <NavLink to="/app/incidents" className={({isActive})=>isActive?'active':''}>Incidents</NavLink>
        <NavLink to="/app/camera" className={({isActive})=>isActive?'active':''}>Camera & AI</NavLink>
        <NavLink to="/app/ai" className={({isActive})=>isActive?'active':''}>AI & Heat Map</NavLink>
        <div style={{ marginTop: 24, fontSize: 12, opacity: .5 }}>
          <a href="/" style={{ opacity: .7 }}>← Public site</a>
        </div>
      </aside>
      <div>
        <div className="statusbar">
          <span><span className={`dot ${status?'':'err'}`}></span>App: {status?'LIVE (local)':'OFFLINE'}</span>
          <span>Mode: LOCAL DEVELOPMENT</span>
          <span>Camera: {status?.camera?.state ?? '—'}</span>
          <span>AI: {status?.ai_running ? 'RUNNING' : 'STOPPED'}</span>
          <span>WS: {wsState}</span>
          <span className="mono-val">{now.toLocaleTimeString()}</span>
        </div>
        <main className="app-main">
          <Outlet context={{ api: API, refresh }} />
        </main>
      </div>
    </div>
  );
}
