// src/pages/GA1Variables.jsx
import { useEffect, useState } from 'react';
import api from '../api/client';
import Spinner from '../components/Spinner';

export default function GA1Variables() {
  const [candidatas, setCandidatas] = useState([]);
  const [result,     setResult]     = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  useEffect(() => {
    api.get('/ga/candidatas')
      .then(r => setCandidatas(r.data.candidatas))
      .catch(() => {});
  }, []);

  const ejecutar = () => {
    setError(null);
    setLoading(true);
    api.post('/ga/variables')
      .then(r => setResult(r.data))
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setLoading(false));
  };

  const mejora = result ? result.mejora : null;

  return (
    <div>
      <div className="page-header">
        <h2>AG #1 — Selección Óptima de Variables Predictoras</h2>
        <p>
          Busca el subconjunto de {candidatas.length} variables candidatas que minimiza el MAE
          del modelo Ridge (split 80/20) usando un Algoritmo Genético evolutivo.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Candidatas */}
        <div className="card">
          <div className="card-header">
            <h3>Variables Candidatas ({candidatas.length} cromosoma)</h3>
          </div>
          <div className="card-body">
            <div className="feature-list">
              {candidatas.map(c => {
                const selected = result?.features_seleccionadas?.includes(c.nombre);
                const clase = result
                  ? (selected ? 'feature-item selected' : 'feature-item unselected')
                  : 'feature-item';
                return (
                  <div key={c.nombre} className={clase}>
                    <span>{result ? (selected ? '✔' : '○') : (c.disponible ? '●' : '○')}</span>
                    <span>{c.nombre.replace(/_/g, ' ')}</span>
                    {!c.disponible && <span style={{ marginLeft: 'auto', fontSize: 11, color: '#aaa' }}>no disponible</span>}
                  </div>
                );
              })}
            </div>

            <button
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 20 }}
              onClick={ejecutar}
              disabled={loading}
            >
              {loading ? '⚙️ Ejecutando AG... (puede tardar ~10s)' : '🧬 Ejecutar AG #1'}
            </button>
          </div>
        </div>

        {/* Resultado */}
        <div className="card">
          <div className="card-header"><h3>Resultado del AG</h3></div>
          <div className="card-body">
            {error  && <div className="alert alert-danger">{error}</div>}
            {loading && <Spinner text="Ejecutando Algoritmo Genético..." />}

            {!result && !loading && (
              <p style={{ color: '#888', fontStyle: 'italic' }}>
                Ejecuta el AG para ver qué variables selecciona el algoritmo genético.
              </p>
            )}

            {result && (
              <>
                <div
                  className={`alert ${mejora >= 0 ? 'alert-success' : 'alert-warning'}`}
                  style={{ marginBottom: 20 }}
                >
                  MAE AG: <strong>±{result.mae_ga}</strong> vs MAE base:{' '}
                  <strong>±{result.mae_base?.toFixed(4)}</strong>
                  &nbsp;&nbsp;
                  {mejora >= 0
                    ? `↓ Mejora de ${Math.abs(mejora).toFixed(4)} alumnos`
                    : `↑ Aumentó ${Math.abs(mejora).toFixed(4)} alumnos`}
                </div>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>
                    {result.n_seleccionadas} de {result.n_candidatas} variables seleccionadas:
                  </div>
                  <div className="feature-list">
                    {result.features_seleccionadas.map(f => (
                      <div key={f} className="feature-item selected">
                        <span>✔</span>
                        <span>{f.replace(/_/g, ' ')}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Historia convergencia */}
                {result.historia?.length > 0 && (
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: '#555' }}>
                      Convergencia por generación
                    </div>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {result.historia.filter((_, i) => i % 5 === 0 || i === result.historia.length - 1).map(h => (
                        <div key={h.gen} style={{
                          fontSize: 11, padding: '3px 8px', background: '#f5f5f5',
                          borderRadius: 6, color: '#666'
                        }}>
                          Gen {h.gen}: ±{h.mejor_mae}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
