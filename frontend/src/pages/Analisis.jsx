// src/pages/Analisis.jsx
import { useEffect, useState } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  LineChart, Line, Bar, BarChart, Legend, YAxis as YAxisR,
  ComposedChart, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import api from '../api/client';
import Spinner from '../components/Spinner';

const ROL_COLOR = {
  subutilizado: '#FFD700',
  optimo:       '#2E7D32',
  sobrepoblado: '#D32F2F',
};

const ROL_LABEL = {
  subutilizado: 'Subutilización',
  optimo:       'Eficiencia',
  sobrepoblado: 'Hacinamiento',
};

const INTERPRETACION = {
  subutilizado: 'Aulas con capacidad muy superior a la demanda. Costo operativo innecesario. Recomendación: Mover a pabellones menores.',
  optimo:       'Relación de ocupación equilibrada. Uso ideal del activo físico. Recomendación: Escalar este modelo.',
  sobrepoblado: 'Demanda ≥ capacidad. Deterioro de calidad académica y riesgo de seguridad. Recomendación: División de secciones.',
};

export default function Analisis() {
  const [variables, setVariables] = useState([]);
  const [varX, setVarX] = useState('alumnos_matriculados');
  const [varY, setVarY] = useState('capacidad_aula');
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);
  const [showInterp, setShowInterp] = useState(false);

  useEffect(() => {
    api.get('/analisis/variables')
      .then(r => setVariables(r.data.variables))
      .catch(() => {});
  }, []);

  const ejecutar = () => {
    if (varX === varY) { setError('Selecciona variables distintas para X e Y.'); return; }
    setError(null);
    setLoading(true);
    setResult(null);
    api.post('/analisis/clustering', { var_x: varX, var_y: varY })
      .then(r => setResult(r.data))
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setLoading(false));
  };

  // Build codo data (inercias + mejora marginal)
  const codoData = result
    ? result.inercias.map((v, i) => ({
        k: i + 1,
        inercia: Math.round(v),
        mejora:  i > 0 ? result.mejora_pct[i - 1] : null,
      }))
    : [];

  return (
    <div>
      <div className="page-header">
        <h2>Análisis de Eficiencia de Infraestructura</h2>
        <p>Clustering K-Means K=3 sobre variables académicas. Identifica subutilización, eficiencia y hacinamiento.</p>
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body" style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="form-group">
            <label>Variable X</label>
            <select value={varX} onChange={e => setVarX(e.target.value)}>
              {variables.map(v => <option key={v} value={v}>{v.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Variable Y</label>
            <select value={varY} onChange={e => setVarY(e.target.value)}>
              {variables.map(v => <option key={v} value={v}>{v.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <button className="btn btn-primary" onClick={ejecutar} disabled={loading}>
            {loading ? '⚙️ Procesando...' : '🔄 Actualizar Análisis'}
          </button>
          {result && (
            <button className="btn btn-outline" onClick={() => setShowInterp(s => !s)}>
              {showInterp ? '📊 Ver Gráfico' : '📝 Ver Interpretación'}
            </button>
          )}
        </div>
      </div>

      {error  && <div className="alert alert-danger">{error}</div>}
      {loading && <Spinner text="Ejecutando K-Means K=3..." />}

      {result && !showInterp && (
        <div className="grid-2col" style={{ gap: 20 }}>
          {/* Scatter */}
          <div className="card">
            <div className="card-header">
              <h3>K=3: {varX.replace(/_/g, ' ')} vs {varY.replace(/_/g, ' ')}</h3>
              <p style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                Silhouette: {result.silhouette} — {result.interpretacion}
              </p>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={370}>
                <ScatterChart margin={{
                    top: 20,
                    right: 25,
                    left: 30,
                    bottom: 10
                }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" name={varX} type="number" label={{ value: varX.replace(/_/g,' '), position: 'bottom', offset: 0, fontSize: 11 }} />
                  <YAxis dataKey="y" name={varY} type="number" label={{ value: varY.replace(/_/g,' '), angle: -90, position: 'left', fontSize: 11 }} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  {result.clusters.map(c => (
                    <Scatter
                      key={c.cluster_id}
                      name={ROL_LABEL[c.rol]}
                      data={c.puntos}
                      fill={ROL_COLOR[c.rol]}
                      opacity={0.75}
                    />
                  ))}
                  <Legend height={30} 
                    verticalAlign="bottom"
                    align="center"
                    iconType="circle"
                    wrapperStyle={{
                        paddingTop: 15
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Codo */}
          <div className="card">
            <div className="card-header">
              <h3>Método del Codo — Validación de K=3</h3>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={370}>
                <ComposedChart data={codoData} margin={{
                    top: 20,
                    right: 20,
                    left: 30,
                    bottom: 0
                }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="k" label={{ value: 'Clusters (K)', position: 'bottom', offset: 0, fontSize: 11 }} />
                  <YAxis yAxisId="left" label={{ value: 'Inercia', angle: -90, position: 'left', offset: 20, fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" label={{ value: 'Mejora %', angle: 90, position: 'right', offset: 0, fontSize: 11 }} />
                  <Tooltip />
                  <Legend height={30} 
                    verticalAlign="bottom"
                    align="center"
                    iconType="circle"
                    wrapperStyle={{
                        paddingTop: 15
                    }}
                  />
                  <ReferenceLine yAxisId="left" x={3} stroke="#2E7D32" strokeDasharray="4 4" />
                  <Line yAxisId="left" type="monotone" dataKey="inercia" stroke="#8B0000" strokeWidth={2} dot={{ r: 4 }} name="Inercia" />
                  <Bar yAxisId="right" dataKey="mejora" fill="#2E7D32" opacity={0.3} name="Mejora %" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Interpretación */}
      {result && showInterp && (
        <div className="card">
          <div className="card-header">
            <h3>Interpretación Administrativa — K=3</h3>
            <p style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
              Silhouette: {result.silhouette} → {result.interpretacion}
            </p>
          </div>
          <div className="card-body">
            {result.clusters.map(c => (
              <div key={c.cluster_id} style={{ marginBottom: 20 }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: ROL_COLOR[c.rol], paddingTop: 10, marginBottom: 1 }}>
                  {ROL_LABEL[c.rol]} (Cluster {c.cluster_id})
                </div>
                <p style={{ fontSize: 13, color: '#555', lineHeight: 1.7, marginBottom: 4 }}>
                  {INTERPRETACION[c.rol]}
                </p>
                <p style={{ fontSize: 12, color: '#888' }}>
                  Centroide → {varX.replace(/_/g,' ')}: {c.centroid_x.toFixed(1)} | {varY.replace(/_/g,' ')}: {c.centroid_y.toFixed(1)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
