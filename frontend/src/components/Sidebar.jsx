// src/components/Sidebar.jsx
import { NavLink } from 'react-router-dom';

const NAV = [
  {
    section: 'Principal',
    items: [
      { to: '/',           icon: '📊', label: 'Dashboard Resumen' },
      { to: '/analisis',   icon: '📈', label: 'Análisis de Aforos' },
      { to: '/prediccion', icon: '🤖', label: 'Predicción IA' },
      { to: '/secciones',  icon: '🏫', label: 'Secciones' },
      { to: '/horarios',   icon: '🗓️', label: 'Horarios' },
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
