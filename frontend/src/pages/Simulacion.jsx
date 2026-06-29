// src/pages/Simulacion.jsx
import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';
import api from '../api/client';
import KPICard from '../components/KPICard';
import OcupacionBadge from '../components/OcupacionBadge';
import Spinner from '../components/Spinner';

const DEFAULT = {
  alumnos_nuevos: 25, alumnos_prerrequisito: 20, alumnos_repitentes: 8,
  capacidad_aula: 40, duracion_semanas: 18, docentes_disponibles: 2,
  laboratorio: 0, escenario: 'Conservador (+MAE)',
};

const colorEstado = (ocup) => {
  if (ocup > 1)     return '#D32F2F';
  if (ocup >= 0.90) return '#E65100';
  if (ocup >= 0.65) return '#2E7D32';
  if (ocup >= 0.45) return '#F57F17';
  return '#F9A825';
};

export default function Simulacion() {
  const [form,    setForm]    = useState(DEFAULT);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);
  const [showDetalle, setShowDetalle] = useState(false);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const ejecutar = () => {
    setError(null);
    setLoading(true);
    api.post('/prediccion/simular', form)
      .then(r => { setResult(r.data); setShowDetalle(false); })
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setLoading(false));
  };

  const resetear = () => { setForm(DEFAULT); setResult(null); setError(null); };

  const barData = result ? [
    { name: 'IA',         valor: result.pred_base,      fill: '#8B0000' },
    { name: 'Planificada',valor: result.demanda_plan,   fill: '#D32F2F' },
    { name: 'Cupos',      valor: result.capacidad_total,fill: '#2E7D32' },
  ] : [];

  const ocup = result?.ocupacion_promedio ?? 0;
  const estadoGeneral =
    result?.deficit_docentes > 0  ? '🔴 CRÍTICO OPERATIVO' :
    ocup > 1                       ? '🔴 CRÍTICO POR AFORO' :
    ocup >= 0.90                   ? '🟠 AJUSTADO' :
    ocup >= 0.65                   ? '🟢 ÓPTIMO' :
    ocup >= 0.45                   ? '🟡 BAJA OCUPACIÓN' :
                                     '🟡 SUBUTILIZADO';

  return (
    <div>
      <div className="page-header">
        <h2>Simulador Predictivo de Carga de Aulas</h2>
        <p>Evalúa demanda estimada, aulas necesarias, ocupación y disponibilidad docente.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 24 }}>
        {/* Form */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div className="card-header"><h3>Parámetros del escenario</h3></div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                ['alumnos_nuevos',        'Alumnos nuevos',           0, 120],
                ['alumnos_prerrequisito', 'Con prerrequisito',        0, 120],
                ['alumnos_repitentes',    'Repitentes',               0, 80],
                ['capacidad_aula',        'Capacidad por aula',       1, 120],
                ['duracion_semanas',      'Duración (semanas)',        1, 24],
                ['docentes_disponibles',  'Docentes disponibles',     0, 20],
              ].map(([key, label, min, max]) => (
                <div className="form-group" key={key}>
                  <label>{label}</label>
                  <input
                    type="number" min={min} max={max} value={form[key]}
                    onChange={e => set(key, parseInt(e.target.value) || 0)}
                  />
                </div>
              ))}

              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={form.laboratorio === 1}
                    onChange={e => set('laboratorio', e.target.checked ? 1 : 0)}
                  />
                  Requiere laboratorio (−15% capacidad)
                </label>
              </div>

              <div className="form-group">
                <label>Escenario de planificación</label>
                <select value={form.escenario} onChange={e => set('escenario', e.target.value)}>
                  <option>Conservador (+MAE)</option>
                  <option>Base IA</option>
                  <option>Optimista (-MAE)</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={ejecutar} disabled={loading}>
                  {loading ? '⚙️ Procesando...' : 'EJECUTAR IA'}
                </button>
                <button className="btn btn-secondary" onClick={resetear}>Reset</button>
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {error && <div className="alert alert-danger">{error}</div>}
          {loading && <Spinner text="Ejecutando predicción IA..." />}

          {result && (
            <>
              {/* Estado banner */}
              <div className="card">
                <div className="card-body">
                  <div style={{ fontSize: 22, fontWeight: 800, color: colorEstado(ocup), marginBottom: 6 }}>
                    {estadoGeneral} — {result.demanda_plan} alumnos a planificar
                  </div>
                  <p style={{ fontSize: 13, color: '#666' }}>
                    Predicción base: {result.pred_base} | Intervalo: {result.pred_min}–{result.pred_max} |
                    Escenario: {result.escenario}
                  </p>
                </div>
              </div>

              {/* KPIs */}
              <div className="kpi-grid">
                <KPICard label="Demanda IA"           value={result.pred_base} />
                <KPICard label="Demanda a planificar" value={result.demanda_plan} />
                <KPICard label="Aulas recomendadas"   value={result.aulas_recomendadas} accent={colorEstado(ocup)} />
                <KPICard label="Ocupación promedio"   value={`${(ocup * 100).toFixed(1)}%`} accent={colorEstado(ocup)} />
              </div>

              {/* Gráfico */}
              <div className="card">
                <div className="card-header"><h3>Demanda vs Capacidad Operativa</h3></div>
                <div className="card-body">
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={barData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <ReferenceLine y={result.capacidad_efectiva} stroke="#888" strokeDasharray="4 4"
                        label={{ value: `Cap. efectiva: ${result.capacidad_efectiva}`, fontSize: 11, fill: '#888' }} />
                      {barData.map(d => (
                        <Bar key={d.name} dataKey="valor" fill={d.fill} radius={[4,4,0,0]} isAnimationActive />
                      ))}
                      <Bar dataKey="valor" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Tabla secciones */}
              <div className="card">
                <div className="card-header"><h3>Distribución sugerida por sección</h3></div>
                <div className="card-body" style={{ padding: 0 }}>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Sección</th><th>Alumnos</th><th>Capacidad</th>
                          <th>Ocupación</th><th>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.secciones.map(s => (
                          <tr key={s.seccion}>
                            <td>{s.seccion}</td>
                            <td>{s.alumnos}</td>
                            <td>{s.capacidad}</td>
                            <td>{(s.ocupacion * 100).toFixed(1)}%</td>
                            <td><OcupacionBadge estado={
                              s.ocupacion > 1 ? 'Excede aforo' :
                              s.ocupacion >= 0.90 ? 'Ajustado' :
                              s.ocupacion >= 0.65 ? 'Óptimo' :
                              s.ocupacion >= 0.45 ? 'Baja ocupación' : 'Subutilizado'
                            } /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Informe detallado */}
              <button className="btn btn-outline" style={{ alignSelf: 'flex-start' }}
                onClick={() => setShowDetalle(s => !s)}>
                {showDetalle ? '🔙 Ocultar informe' : '📄 Ver Informe Detallado'}
              </button>

              {showDetalle && (
                <div className="card">
                  <div className="card-body">
                    <pre style={{ fontSize: 13, lineHeight: 1.8, color: '#444', whiteSpace: 'pre-wrap', fontFamily: 'Inter, sans-serif' }}>
{`📊 RESULTADO EJECUTIVO
Estado: ${estadoGeneral}

📌 DEMANDA ESTIMADA
• Predicción base IA: ${result.pred_base} alumnos
• MAE: ± ${result.mae?.toFixed(2)}
• Intervalo: ${result.pred_min} – ${result.pred_max}
• Escenario: ${result.escenario}
• Demanda planificada: ${result.demanda_plan}

🏫 PLANIFICACIÓN DE AULAS
• Capacidad efectiva: ${result.capacidad_efectiva}
• Capacidad segura (90%): ${result.capacidad_segura}
• Aulas recomendadas: ${result.aulas_recomendadas}
• Cupos totales: ${result.capacidad_total}
• Cupos libres: ${result.cupos_libres}
• Ocupación promedio: ${(ocup * 100).toFixed(1)}%

👨‍🏫 RECURSOS DOCENTES
• Deficit docentes: ${result.deficit_docentes}`}
                    </pre>
                  </div>
                </div>
              )}
            </>
          )}

          {!result && !loading && (
            <div className="card">
              <div className="card-body spinner-wrap">
                <p>Configura los parámetros y ejecuta la simulación.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
