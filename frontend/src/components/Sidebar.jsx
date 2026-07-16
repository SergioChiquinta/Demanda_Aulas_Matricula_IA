// src/components/Sidebar.jsx
import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import GuiaInicioModal from './GuiaInicioModal';
import { PASOS_ADMIN, PASOS_ESTUDIANTE } from '../data/guiaPasos';

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
  const esEstudiante = usuario?.rol === 'estudiante';
  const nav = esEstudiante ? NAV_ESTUDIANTE : NAV_ADMIN;
  const pasosGuia = esEstudiante ? PASOS_ESTUDIANTE : PASOS_ADMIN;

  const [guiaAbierta, setGuiaAbierta] = useState(false);
  const [menuAbierto, setMenuAbierto] = useState(false);

  const salir = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const cerrarMenu = () => setMenuAbierto(false);

  return (
    <>
      {/* Fuera del <aside>: si el toggle de menú va dentro y el aside se
          traslada fuera de pantalla (transform), un descendiente
          position:fixed se movería con él (el transform del ancestro le
          crea un containing block nuevo). Por eso viven como hermanos. */}
      <button
        className="sidebar-hamburger"
        onClick={() => setMenuAbierto((m) => !m)}
        aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
      >
        {menuAbierto ? '✕' : '☰'}
      </button>
      <div
        className={`sidebar-mobile-overlay${menuAbierto ? ' visible' : ''}`}
        onClick={cerrarMenu}
      />

      <aside className={`sidebar${menuAbierto ? ' mobile-open' : ''}`}>
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
                  onClick={cerrarMenu}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                >
                  <span className="nav-icon">{icon}</span>
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-guia">
          <button className="btn-guia" onClick={() => { setGuiaAbierta(true); cerrarMenu(); }}>
            📘 Guía de inicio rápido
          </button>
        </div>

        <div className="sidebar-footer">
          <p>main branch<br />Node.js · React · FastAPI · MySQL</p>
        </div>
      </aside>

      {/* También fuera del <aside> por la misma razón que el botón
          hamburguesa: el modal usa position:fixed sobre toda la pantalla,
          y un ancestro con transform (el .sidebar en mobile) le crearía
          un containing block propio, achicando el modal a los 240px del
          sidebar en vez de ocupar el viewport completo. */}
      <GuiaInicioModal
        abierto={guiaAbierta}
        onCerrar={() => setGuiaAbierta(false)}
        titulo={esEstudiante ? 'Guía de inicio rápido — Estudiante' : 'Guía de inicio rápido — Administrador'}
        pasos={pasosGuia}
      />
    </>
  );
}
