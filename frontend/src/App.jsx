// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SimulacionProvider } from './context/SimulacionContext';
import Sidebar from './components/Sidebar';
import Dashboard   from './pages/Dashboard';
import Analisis    from './pages/Analisis';
import Simulacion  from './pages/Simulacion';
import GA1Variables from './pages/GA1Variables';
import GA2Secciones from './pages/GA2Secciones';
import GA3Horarios  from './pages/GA3Horarios';

export default function App() {
  return (
    <BrowserRouter>
      <SimulacionProvider>
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/"         element={<Dashboard />} />
              <Route path="/analisis" element={<Analisis />} />
              <Route path="/simulacion" element={<Simulacion />} />
              <Route path="/ga1"      element={<GA1Variables />} />
              <Route path="/ga2"      element={<GA2Secciones />} />
              <Route path="/ga3"      element={<GA3Horarios />} />
            </Routes>
          </main>
        </div>
      </SimulacionProvider>
    </BrowserRouter>
  );
}
