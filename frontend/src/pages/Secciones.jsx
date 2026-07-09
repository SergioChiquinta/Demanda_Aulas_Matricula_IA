// src/pages/Secciones.jsx
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { usePrediccion } from '../context/PrediccionContext';
import KPICard from '../components/KPICard';
import OcupacionBadge from '../components/OcupacionBadge';
import Spinner from '../components/Spinner';

export default function Secciones() {
  const { state: predState, derived, setGa2Result } = usePrediccion();
  const { hasValidResult, capacidadEfectiva, demandaPlan, docentesDisponibles } = derived;

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Clave de los parámetros SSOT usados en la última ejecución
  const lastParamsRef = useRef(null);
  const ejecutandoRef = useRef(false);

  const ejecutar = (dp, ce, dd) => {
    if (ejecutandoRef.current) return;
    ejecutandoRef.current = true;
    setError(null);
    setLoading(true);
    api.post('/ga/secciones', {
      demanda_plan: dp,
      capacidad_efectiva: ce,
      docentes_disponibles: dd,
    })
      .then(r => {
        setResult({ ...r.data, cap_ef: ce });
        setGa2Result(r.data);
        lastParamsRef.current = `${dp}-${ce}-${dd}`;
      })
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => { setLoading(false); ejecutandoRef.current = false; });
  };

  // Auto-ejecutar cuando los parámetros SSOT estén disponibles o cambien
  useEffect(() => {
    if (!hasValidResult) return;
    const paramsKey = `${demandaPlan}-${capacidadEfectiva}-${docentesDisponibles}`;
    if (lastParamsRef.current === paramsKey) return; // mismos parámetros, no re-ejecutar
    ejecutar(demandaPlan, capacidadEfectiva, docentesDisponibles);
  }, [hasValidResult, demandaPlan, capacidadEfectiva, docentesDisponibles]); // eslint-disable-line react-hooks/exhaustive-deps

  // Clásico: ceil(demanda / cap_segura)
  const capSegura = hasValidResult ? Math.max(1, Math.floor(capacidadEfectiva * 0.90)) : 0;
  const clasico = hasValidResult ? Math.max(1, Math.ceil(demandaPlan / capSegura)) : 0;

  const ocup = result?.ocupacion ?? 0;
  const colorOcup = ocup >= 0.65 && ocup <= 0.90 ? '#2E7D32' : '#E65100';

  return (
    <div>
      <div className="page-header">
        <h2>Optimización de Distribución de Secciones</h2>
        <p>Optimiza el número de secciones y el factor de ocupación para minimizar hacinamiento y subutilización.</p>
      </div>

      {/* Banner SSOT — requiere predicción ejecutada */}
      {!hasValidResult ? (
        <div className="alert alert-warning" style={{ marginBottom: 24 }}>
          ⚠️ <strong>Predicción IA requerida.</strong> Este módulo consume los resultados de la predicción
          como fuente única de datos (SSOT).{' '}
          <Link to="/prediccion" style={{ fontWeight: 600 }}>
            Ir a Predicción IA →
          </Link>
        </div>
      ) : (
        <div className="alert alert-info" style={{ marginBottom: 24 }}>
          📊 Datos sincronizados desde Predicción IA —
          Demanda: <strong>{demandaPlan}</strong> |
          Cap. efectiva: <strong>{capacidadEfectiva}</strong> |
          Docentes: <strong>{docentesDisponibles}</strong> |
          Escenario: <strong>{predState.result.escenario}</strong>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24 }}>
        {/* Panel de parámetros (solo lectura, derivados del SSOT) */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div className="card-header"><h3>Parámetros (desde Predicción IA)</h3></div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                ['Demanda planificada', demandaPlan ?? '—'],
                ['Capacidad efectiva', capacidadEfectiva],
                ['Docentes disponibles', docentesDisponibles],
              ].map(([label, value]) => (
                <div className="form-group" key={label}>
                  <label>{label}</label>
                  <input
                    type="number"
                    value={value}
                    readOnly
                    disabled
                    style={{ opacity: 0.7, cursor: 'not-allowed' }}
                  />
                </div>
              ))}

              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={predState.form.laboratorio === 1}
                    disabled
                    style={{ cursor: 'not-allowed' }}
                  />
                  Laboratorio (−15% capacidad)
                </label>
              </div>

              {hasValidResult && (
                <div style={{ padding: '10px 0', borderTop: '1px solid #eee', fontSize: 12, color: '#888' }}>
                  Cap. segura (90%): <strong>{capSegura}</strong>
                  <br />Clásico (ceil): <strong>{clasico} secciones</strong>
                </div>
              )}

              <button
                className="btn btn-primary"
                onClick={() => hasValidResult && ejecutar(demandaPlan, capacidadEfectiva, docentesDisponibles)}
                disabled={loading || !hasValidResult}
              >
                {loading ? '⚙️ Optimizando secciones...' : '🔄 Re-ejecutar optimización'}
              </button>

              {!hasValidResult && (
                <p style={{ fontSize: 12, color: '#aaa', textAlign: 'center', marginTop: 4 }}>
                  Ejecuta la Predicción IA primero.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {error && <div className="alert alert-danger">{error}</div>}
          {loading && <Spinner text="Optimizando distribución de secciones..." />}

          {result && (
            <>
              <div className={`alert ${result.n_secciones === clasico ? 'alert-info' : 'alert-success'}`}>
                {result.n_secciones === clasico
                  ? `El optimizador confirma el resultado clásico: ${result.n_secciones} secciones.`
                  : `El optimizador sugiere ${result.n_secciones} secciones vs ${clasico} del método clásico.`}
                {' '}Factor de ocupación óptimo: {(result.factor_ocupacion * 100).toFixed(0)}%
              </div>

              <div className="kpi-grid">
                <KPICard label="Secciones (óptimo)" value={result.n_secciones} accent="#8B0000" />
                <KPICard label="Secciones (Clásico)" value={clasico} accent="#888" />
                <KPICard label="Ocupación óptima" value={`${(ocup * 100).toFixed(1)}%`} accent={colorOcup} />
                <KPICard label="Total Cupos" value={result.total_cupos} accent="#8B0000" />
              </div>

              {result.deficit_docentes > 0 && (
                <div className="alert alert-danger">
                  ⚠️ Déficit de {result.deficit_docentes} docente(s). Se calcularon {result.n_secciones} secciones pero solo hay {docentesDisponibles} disponibles.
                </div>
              )}

              <div className="card">
                <div className="card-header" style={{ padding: '10px 10px 10px 10px' }}><h3>Distribución sugerida</h3></div>
                <div className="card-body" style={{ padding: 0 }}>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr><th>Sección</th><th>Alumnos</th><th>Capacidad</th><th>Ocupación</th><th>Estado</th></tr>
                      </thead>
                      <tbody>
                        {result.secciones?.map(s => {
                          const estado =
                            s.ocupacion > 1 ? 'Excede aforo' :
                              s.ocupacion >= 0.90 ? 'Ajustado' :
                                s.ocupacion >= 0.65 ? 'Óptimo' :
                                  s.ocupacion >= 0.45 ? 'Baja ocupación' : 'Subutilizado';
                          return (
                            <tr key={s.seccion}>
                              <td>{s.seccion}</td>
                              <td>{s.alumnos}</td>
                              <td>{s.capacidad}</td>
                              <td>{(s.ocupacion * 100).toFixed(1)}%</td>
                              <td><OcupacionBadge estado={estado} /></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div style={{ fontSize: 12, color: '#aaa' }}>
                Fitness: {result.fitness} | Cap. segura: {result.cap_segura}
              </div>
            </>
          )}

          {!result && !loading && hasValidResult && (
            <div className="card">
              <div className="card-body" style={{ textAlign: 'center', padding: '40px 0', color: '#aaa' }}>
                Ejecutando automáticamente...
              </div>
            </div>
          )}

          {!result && !loading && !hasValidResult && (
            <div className="card">
              <div className="card-body" style={{ textAlign: 'center', padding: '40px 0', color: '#aaa' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🔒</div>
                <p>Los parámetros se sincronizan desde <strong>Predicción IA</strong>.</p>
                <p style={{ fontSize: 12, marginTop: 8 }}>
                  Ejecuta primero una predicción para habilitar este módulo.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
