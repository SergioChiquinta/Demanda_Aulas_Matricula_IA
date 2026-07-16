// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { PrediccionProvider } from './context/PrediccionContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard    from './pages/Dashboard';
import Analisis     from './pages/Analisis';
import PrediccionIA from './pages/PrediccionIA';
import Horarios     from './pages/Horarios';
import MiHorario    from './pages/MiHorario';
// Motor Inteligente de Planificación (nuevo módulo IA Clásica)
import PlanificadorIA from './pages/PlanificadorIA';

function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<ProtectedRoute roles={['admin']}><Dashboard /></ProtectedRoute>} />
          <Route path="/analisis" element={<ProtectedRoute roles={['admin']}><Analisis /></ProtectedRoute>} />
          <Route path="/prediccion" element={<ProtectedRoute roles={['admin']}><PrediccionIA /></ProtectedRoute>} />
          <Route path="/planificador" element={<ProtectedRoute roles={['admin']}><PlanificadorIA /></ProtectedRoute>} />
          <Route path="/horarios" element={<ProtectedRoute roles={['admin']}><Horarios /></ProtectedRoute>} />
          <Route path="/mi-horario" element={<ProtectedRoute roles={['estudiante']}><MiHorario /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PrediccionProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/*" element={<AppShell />} />
          </Routes>
        </PrediccionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
