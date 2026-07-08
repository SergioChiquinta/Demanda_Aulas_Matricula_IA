// src/components/Sidebar.jsx
import { NavLink } from 'react-router-dom';

const NAV = [
  {
    section: 'Principal',
    items: [
      { to: '/',         icon: '📊', label: 'Dashboard Resumen' },
      { to: '/analisis', icon: '📈', label: 'Análisis de Aforos' },
      { to: '/simulacion',icon: '🤖', label: 'Simulación IA' },
    ],
  },
  {
    section: 'Algoritmos Genéticos',
    items: [
      { to: '/ga1', icon: '🧬', label: 'AG-1 Variables' },
      { to: '/ga2', icon: '🧬', label: 'AG-2 Secciones' },
      { to: '/ga3', icon: '🧬', label: 'AG-3 Horarios' },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>Demanda Aulas<br />Matrícula IA</h1>
        <span>Sistema Predictivo UTP</span>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div key={section}>
            <div className="nav-section-label">{section}</div>
            {items.map(({ to, icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <span className="nav-icon">{icon}</span>
                {label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <p>main branch<br />Node.js · React · FastAPI · MySQL</p>
      </div>
    </aside>
  );
}
