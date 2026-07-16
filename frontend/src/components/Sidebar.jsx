// src/components/Sidebar.jsx
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ADMIN = [
  {
    section: 'Principal',
    items: [
      { to: '/',           icon: '📊', label: 'Dashboard Resumen' },
      { to: '/analisis',   icon: '📈', label: 'Análisis de Aforos' },
    ],
  },
  {
    // Flujo secuencial: Predicción IA -> Planificador IA -> (visto bueno) -> Horarios
    section: 'Flujo de Planificación',
    items: [
      { to: '/prediccion',   icon: '🤖', label: '1. Predicción IA' },
      { to: '/planificador', icon: '🧠', label: '2. Planificador IA' },
      { to: '/horarios',     icon: '🗓️', label: '3. Horarios' },
    ],
  },
];

const NAV_ESTUDIANTE = [
  {
    section: 'Principal',
    items: [
      { to: '/mi-horario', icon: '🗓️', label: 'Mi Horario' },
    ],
  },
];

export default function Sidebar() {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();
  const nav = usuario?.rol === 'estudiante' ? NAV_ESTUDIANTE : NAV_ADMIN;

  const salir = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>Demanda Aulas<br />Matrícula IA</h1>
        <span>Sistema Predictivo UTP</span>
      </div>

      {usuario && (
        <div className="sidebar-user">
          <div className="user-name">{usuario.nombre}</div>
          <span className="user-rol">{usuario.rol}</span>
          <button className="btn-logout" onClick={salir}>Cerrar sesión</button>
        </div>
      )}

      <nav className="sidebar-nav">
        {nav.map(({ section, items }) => (
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
