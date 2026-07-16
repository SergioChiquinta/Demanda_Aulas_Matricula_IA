// src/components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Protege una ruta por autenticación y, opcionalmente, por rol.
 * Uso: <ProtectedRoute roles={['admin']}><Dashboard /></ProtectedRoute>
 */
export default function ProtectedRoute({ roles, children }) {
  const { usuario } = useAuth();

  if (!usuario) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(usuario.rol)) {
    return <Navigate to={usuario.rol === 'admin' ? '/' : '/mi-horario'} replace />;
  }
  return children;
}
