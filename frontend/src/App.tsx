import { Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import AppShell from './pages/AppShell';
import Monitoring from './pages/Monitoring';
import Incidents from './pages/Incidents';
import CameraPage from './pages/CameraPage';
import AIPage from './pages/AIPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<AppShell />}>
        <Route index element={<Monitoring />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="camera" element={<CameraPage />} />
        <Route path="ai" element={<AIPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
