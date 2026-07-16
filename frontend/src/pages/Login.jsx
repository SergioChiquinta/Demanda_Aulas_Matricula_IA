// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [rol, setRol] = useState('admin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const usuario = await login(rol, email, password);
      navigate(usuario.rol === 'admin' ? '/' : '/mi-horario', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-brand">
          <h1>Demanda Aulas<br />Matrícula IA</h1>
          <span>Sistema Predictivo UTP · Campus Lima Sur</span>
        </div>

        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab${rol === 'admin' ? ' active' : ''}`}
            onClick={() => setRol('admin')}
          >
            🛡️ Administrativo
          </button>
          <button
            type="button"
            className={`login-tab${rol === 'estudiante' ? ' active' : ''}`}
            onClick={() => setRol('estudiante')}
          >
            🎓 Estudiante
          </button>
        </div>

        <form onSubmit={submit} className="login-form">
          <div className="form-group">
            <label>Correo institucional</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="u00000000@utp.edu.pe"
            />
          </div>
          <div className="form-group">
            <label>Contraseña</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && <div className="alert alert-danger">{error}</div>}

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '12px' }}>
            {loading ? 'Ingresando...' : `Ingresar como ${rol === 'admin' ? 'Administrativo' : 'Estudiante'}`}
          </button>
        </form>

        <p className="login-hint">
          Demo: {rol === 'admin'
            ? 'u22201712@utp.edu.pe / sergio123*'
            : 'u20250001@utp.edu.pe / estudiante123*'}
        </p>
      </div>
    </div>
  );
}
