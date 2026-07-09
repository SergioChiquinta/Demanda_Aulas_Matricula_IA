// src/pages/Horarios.jsx
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { usePrediccion } from '../context/PrediccionContext';
import OcupacionBadge from '../components/OcupacionBadge';
import Spinner from '../components/Spinner';

export default function Horarios() {
  const { state: predState, derived } = usePrediccion();
  const { hasValidResult, demandaPlan, ocupacionPromedio, aulasRecomendadas, ga2Result, hasGa2Result } = derived;

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const ejecutandoRef = useRef(false);
  const lastParamsRef = useRef(null);

  const ejecutar = () => {
    if (ejecutandoRef.current) return;
    ejecutandoRef.current = true;
    setError(null);
    setLoading(true);
    const body = hasGa2Result
      ? { secciones: ga2Result.secciones, curso_nombre: `Curso simulado (${predState.form.escenario})` }
      : {};
    api.post('/ga/horarios', body)
      .then(r => {
        setResult(r.data);
        lastParamsRef.current = hasGa2Result ? JSON.stringify(ga2Result.secciones) : 'top30';
      })
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => { setLoading(false); ejecutandoRef.current = false; });
  };

  // Auto-ejecutar al montar y cada vez que cambie el resultado de Secciones (pipeline)
  useEffect(() => {
    const paramsKey = hasGa2Result ? JSON.stringify(ga2Result.secciones) : 'top30';
    if (lastParamsRef.current === paramsKey) return;
    ejecutar();
  }, [hasGa2Result, ga2Result]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="page-header">
        <h2>Optimizador de Horarios</h2>
        <p>
          {hasGa2Result
            ? 'Asigna aula y turno reales exactamente a las secciones decididas en Secciones, minimizando conflictos y hacinamiento.'
            : 'Asigna automáticamente los top-30 cursos más demandados a aulas y turnos, minimizando conflictos de aula, conflictos de docente y hacinamiento.'}
        </p>
      </div>

      {/* Banner contextual SSOT */}
      {hasGa2Result ? (
        <div className="alert alert-success" style={{ marginBottom: 20 }}>
          🔗 <strong>Modo pipeline</strong> — usando las <strong>{ga2Result.n_secciones}</strong> secciones
          calculadas en Secciones (demanda: <strong>{demandaPlan}</strong>,
          escenario: <strong>{predState.result.escenario}</strong>).
        </div>
      ) : hasValidResult ? (
        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          📊 Predicción activa —
          Demanda: <strong>{demandaPlan}</strong> |
          Aulas recomendadas: <strong>{aulasRecomendadas}</strong> |
          Ocupación: <strong>{(ocupacionPromedio * 100).toFixed(1)}%</strong> |
          Escenario: <strong>{predState.result.escenario}</strong>
          {' — '}
          <Link to="/secciones" style={{ fontWeight: 600 }}>Ejecuta Secciones</Link> para encadenar el resultado aquí.
        </div>
      ) : (
        <div className="alert alert-warning" style={{ marginBottom: 20 }}>
          ⚠️ No hay predicción ejecutada.{' '}
          <Link to="/prediccion" style={{ fontWeight: 600 }}>
            Ir a Predicción IA
          </Link>{' '}
          para establecer el contexto del escenario. Mientras tanto, opera en modo standalone
          sobre los top-30 cursos del dataset.
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 24, flexWrap: 'wrap' }}>
        <button
          className="btn btn-primary"
          onClick={ejecutar}
          disabled={loading}
          style={{ fontSize: 15, padding: '12px 28px' }}
        >
          {loading ? '⚙️ Ejecutando... (puede tardar ~20s)' : '🔄 Re-ejecutar Timetabling'}
        </button>

        {result && (
          <div style={{ display: 'flex', gap: 24, fontSize: 14, color: '#555' }}>
            <span>✅ <strong>{result.n_cursos}</strong> {result.modo === 'pipeline' ? 'secciones' : 'cursos'}</span>
            <span>🏫 <strong>{result.n_aulas}</strong> aulas</span>
            <span>🕐 <strong>{result.n_turnos}</strong> turnos</span>
            <span style={{ color: result.conflictos === 0 ? '#2E7D32' : '#E65100' }}>
              {result.conflictos === 0 ? '✔ Sin conflictos' : `⚠️ ${result.conflictos} conflicto(s)`}
            </span>
            <span style={{ color: '#888' }}>Fitness: {result.score}</span>
          </div>
        )}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <Spinner text="Ejecutando optimización de horarios..." />}

      {result && (
        <>
          {result.conflictos > 0 && (
            <div className="alert alert-warning">
              ⚠️ Se detectaron {result.conflictos} conflicto(s) de aula. El optimizador intentó minimizarlos pero
              podría no haberlos eliminado completamente. Verifica los turnos duplicados.
            </div>
          )}
          {result.conflictos === 0 && (
            <div className="alert alert-success">
              ✔ Asignación sin conflictos. Todos los cursos tienen aula y turno únicos.
            </div>
          )}

          <div className="card">
            <div className="card-header" style={{ padding: '10px 10px 10px 10px' }}>
              <h3>
                Asignación Óptima — {result.asignaciones.length}{' '}
                {result.modo === 'pipeline' ? 'Secciones (Secciones → Horarios)' : 'Cursos'}
              </h3>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Curso</th>
                      <th>Aula ID</th>
                      <th>Pabellón</th>
                      <th>Turno</th>
                      <th>Demanda</th>
                      <th>Capacidad</th>
                      <th>Ocupación</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.asignaciones.map((a, i) => (
                      <tr key={i}>
                        <td style={{ color: '#aaa', fontSize: 12 }}>{i + 1}</td>
                        <td style={{ fontWeight: 600, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {a.curso}
                        </td>
                        <td>{a.aula_id}</td>
                        <td>{a.pabellon}</td>
                        <td>{a.turno}</td>
                        <td>{a.demanda}</td>
                        <td>{a.capacidad}</td>
                        <td>{(a.ocupacion * 100).toFixed(1)}%</td>
                        <td><OcupacionBadge estado={a.estado} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="card">
          <div className="card-body" style={{ textAlign: 'center', padding: '60px 0', color: '#aaa' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🗓️</div>
            <p>Ejecutando automáticamente...</p>
            <p style={{ fontSize: 12, marginTop: 8 }}>Puede tardar entre 10 y 30 segundos.</p>
          </div>
        </div>
      )}
    </div>
  );
}
