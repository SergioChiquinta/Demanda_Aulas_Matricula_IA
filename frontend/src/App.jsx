// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { PrediccionProvider } from './context/PrediccionContext';
import Sidebar from './components/Sidebar';
import Dashboard    from './pages/Dashboard';
import Analisis     from './pages/Analisis';
import PrediccionIA from './pages/PrediccionIA';
import Secciones    from './pages/Secciones';
import Horarios     from './pages/Horarios';
// Motor Inteligente de Planificación (nuevo módulo IA Clásica)
import PlanificadorIA from './pages/PlanificadorIA';

export default function App() {
  return (
    <BrowserRouter>
      <PrediccionProvider>
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/"           element={<Dashboard />} />
              <Route path="/analisis"   element={<Analisis />} />
              <Route path="/prediccion" element={<PrediccionIA />} />
              <Route path="/secciones"  element={<Secciones />} />
              <Route path="/horarios"   element={<Horarios />} />
              {/* Motor Inteligente de Planificación (nuevo módulo IA Clásica) */}
              <Route path="/planificador" element={<PlanificadorIA />} />
            </Routes>
          </main>
        </div>
      </PrediccionProvider>
    </BrowserRouter>
  );
}
