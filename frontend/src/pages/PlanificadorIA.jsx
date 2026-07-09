// src/pages/PlanificadorIA.jsx
// Motor Inteligente de Planificación — Página principal
// Nueva pantalla que no modifica ni afecta ninguna página existente.
import { useState, useCallback } from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { usePrediccion } from '../context/PrediccionContext';
import api from '../api/client';
import Spinner from '../components/Spinner';
import OcupacionBadge from '../components/OcupacionBadge';

// ── Constantes ────────────────────────────────────────────────────
const ALGORITMOS = [
  {
    key: 'bfs',
    label: 'BFS',
    icon: '🌊',
    desc: 'Menor nº pasos',
    titulo: 'Búsqueda en Anchura',
    detalle: 'Explora nivel a nivel. Garantiza el camino con menor número de acciones.',
  },
  {
    key: 'dfs',
    label: 'DFS',
    icon: '🔍',
    desc: 'Búsqueda rápida',
    titulo: 'Búsqueda en Profundidad',
    detalle: 'Explora el árbol en profundidad. Rápido pero no garantiza optimalidad.',
  },
  {
    key: 'astar',
    label: 'A*',
    icon: '⭐',
    desc: 'Óptimo f=g+h',
    titulo: 'A* (f = g + h)',
    detalle: 'Usa heurística admisible. Garantiza el camino de MENOR COSTO TOTAL.',
  },
];

const ACCION_ICONS = {
  asignar_aula:    '🏫',
  abrir_seccion:   '➕',
  asignar_docente: '👨‍🏫',
  cambiar_horario: '🗓️',
  cerrar_seccion:  '❌',
};

const ACCION_DESC = {
  asignar_aula:    'Aula asignada con alumnos y turno',
  abrir_seccion:   'Nueva sección creada',
  asignar_docente: 'Docente asignado a sección',
  cambiar_horario: 'Horario reconfigurado',
  cerrar_seccion:  'Sección consolidada',
};

// ── Helpers del tab de Precisión (definidos a nivel de módulo, fuera del componente) ──
const scoreColor = (v) =>
  v >= 0.9 ? '#2E7D32' : v >= 0.7 ? '#1565C0' : v >= 0.5 ? '#E65100' : '#8B0000';

function GaugeSVG({ value, label, color }) {
  const pct  = Math.min(1, Math.max(0, Number(value) || 0));
  const r = 36, cx = 44, cy = 44;
  const circ = 2 * Math.PI * r;
  const dash  = pct * circ;
  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={88} height={88}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#ddd" strokeWidth={8} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={8}
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
        />
        <text x={cx} y={cy + 5} textAnchor="middle" fontSize={13} fontWeight="700" fill={color}>
          {(pct * 100).toFixed(0)}%
        </text>
      </svg>
      <div style={{ fontSize: 11, fontWeight: 700, color: '#555', marginTop: 2 }}>{label}</div>
    </div>
  );
}

function InterpRow({ icon, label, value, pct, interp, color }) {
  return (
    <div style={{ display: 'flex', gap: 14, padding: '12px 0', borderBottom: '1px solid #f0f0f0', alignItems: 'flex-start' }}>
      <div style={{ fontSize: 24, lineHeight: 1, flexShrink: 0, marginTop: 2 }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
          <span style={{ fontWeight: 700, fontSize: 13, color: '#222' }}>{label}</span>
          <span style={{ fontWeight: 800, fontSize: 15, color }}>{value}</span>
        </div>
        <div style={{ background: '#e8e8e8', borderRadius: 99, height: 7, marginBottom: 5 }}>
          <div style={{ width: `${Math.min(100, pct)}%`, height: '100%', borderRadius: 99, background: color, transition: 'width .6s ease' }} />
        </div>
        <div style={{ fontSize: 12, color: '#666', lineHeight: 1.55 }}>{interp}</div>
      </div>
    </div>
  );
}

// ── Componente principal ──────────────────────────────────────────
export default function PlanificadorIA() {
  const { derived } = usePrediccion();

  // ── Estado local ───────────────────────────────────────────────
  const [algoritmo, setAlgoritmo]   = useState('astar');
  const [demanda, setDemanda]       = useState('');
  const [docentes, setDocentes]     = useState(3);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
  const [resultado, setResultado]   = useState(null);
  const [tabActiva, setTabActiva]   = useState('planificacion');

  // Usar la predicción del contexto como valor por defecto si existe
  const demandaEfectiva = demanda !== ''
    ? parseInt(demanda)
    : (derived.demandaPlan ?? 45);

  // ── Ejecutar planificación ─────────────────────────────────────
  const ejecutar = useCallback(async () => {
    setError(null);
    setLoading(true);
    setResultado(null);
    setTabActiva('planificacion');
    try {
      const payload = {
        demanda_predicha:    demandaEfectiva,
        docentes_disponibles: docentes,
        // aulas y horarios = null → el backend usa los reales de MySQL
      };
      const { data } = await api.post(`/planner/${algoritmo}`, payload);
      setResultado(data);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  }, [algoritmo, demandaEfectiva, docentes]);

  const resetear = () => {
    setResultado(null);
    setError(null);
    setDemanda('');
    setDocentes(3);
  };

  // ── Datos derivados para gráficos ──────────────────────────────
  const algoInfo = ALGORITMOS.find(a => a.key === algoritmo);
  const stats = resultado?.estadisticas;

  const radarData = stats ? [
    { subject: 'Nodos exp.',  value: Math.min(100, (stats.nodos_expandidos / 10) * 10) },
    { subject: 'Profundidad', value: Math.min(100, (stats.profundidad / 20) * 100) },
    { subject: 'Velocidad',   value: Math.max(0, 100 - (stats.tiempo_ms / 2)) },
    { subject: 'Eficiencia',  value: resultado.encontrado ? 90 : 20 },
    { subject: 'Costo',       value: Math.max(0, 100 - (resultado.costo * 5)) },
  ] : [];

  const maxHDiag = resultado?.heuristica_diagnostico
    ? Math.max(1, ...Object.values(resultado.heuristica_diagnostico).filter(v => typeof v === 'number'))
    : 1;

  return (
    <div>
      {/* ── Encabezado ─────────────────────────────────────────── */}
      <div className="page-header">
        <h2>🧠 Planificador IA — Motor Inteligente</h2>
        <p>
          IA Clásica basada en Espacios de Estados. Utiliza BFS, DFS o A* para encontrar
          la asignación óptima de aulas a partir de la predicción del modelo ML.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24, alignItems: 'start' }}>

        {/* ════ PANEL DE CONFIGURACIÓN ════════════════════════════ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Predicción del contexto */}
          {derived.hasValidResult && (
            <div className="alert alert-info" style={{ margin: 0 }}>
              <strong>🤖 Predicción ML activa:</strong> {derived.demandaPlan} alumnos
              <br />
              <span style={{ fontSize: 12, opacity: .85 }}>
                Puedes usarla directamente o sobreescribir el valor.
              </span>
            </div>
          )}

          {/* Selector de algoritmo */}
          <div className="card">
            <div className="card-header"><h3>Seleccionar Algoritmo</h3></div>
            <div className="card-body">
              <div className="algo-selector">
                {ALGORITMOS.map(algo => (
                  <button
                    key={algo.key}
                    id={`btn-algo-${algo.key}`}
                    className={`algo-btn${algoritmo === algo.key ? ' selected' : ''}`}
                    onClick={() => setAlgoritmo(algo.key)}
                    title={algo.detalle}
                  >
                    <span className="algo-icon">{algo.icon}</span>
                    <span className="algo-label">{algo.label}</span>
                    <span className="algo-desc">{algo.desc}</span>
                  </button>
                ))}
              </div>
              {algoInfo && (
                <div className="alert alert-info" style={{ margin: '12px 0 0', fontSize: 12 }}>
                  <strong>{algoInfo.titulo}</strong><br />{algoInfo.detalle}
                </div>
              )}
            </div>
          </div>

          {/* Parámetros */}
          <div className="card">
            <div className="card-header"><h3>Parámetros</h3></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label>Demanda de alumnos</label>
                <input
                  id="input-demanda"
                  type="number"
                  min={1}
                  max={500}
                  placeholder={`Por defecto: ${derived.demandaPlan ?? 45}`}
                  value={demanda}
                  onChange={e => setDemanda(e.target.value)}
                />
                <span className="form-hint">
                  {derived.hasValidResult
                    ? `← Predicción ML: ${derived.demandaPlan} alumnos`
                    : 'Ingresa la demanda o ejecuta la Predicción IA primero'}
                </span>
              </div>

              <div className="form-group">
                <label>Docentes disponibles</label>
                <input
                  id="input-docentes"
                  type="number"
                  min={1}
                  max={20}
                  value={docentes}
                  onChange={e => setDocentes(parseInt(e.target.value) || 1)}
                />
              </div>

              <div className="alert alert-info" style={{ margin: 0, fontSize: 11 }}>
                🏫 Las aulas y horarios se cargan automáticamente desde la base de datos MySQL.
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  id="btn-ejecutar-planner"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  onClick={ejecutar}
                  disabled={loading}
                >
                  {loading ? '⚙️ Planificando...' : `🚀 Ejecutar ${algoInfo?.label}`}
                </button>
                <button className="btn btn-secondary" onClick={resetear}>Reset</button>
              </div>
            </div>
          </div>

          {/* Info flujo */}
          <div className="card">
            <div className="card-header"><h3>Flujo del Sistema</h3></div>
            <div className="card-body">
              {[
                { icon: '🗄️', step: 'MySQL', desc: 'Datos históricos' },
                { icon: '🤖', step: 'ML (Ridge/Lineal)', desc: 'Predicción alumnos' },
                { icon: '🔽', step: 'demanda_predicha', desc: 'Entrada al planificador' },
                { icon: '🧠', step: `Motor IA (${algoInfo?.label})`, desc: 'Búsqueda en espacio de estados' },
                { icon: '📋', step: 'Planificación óptima', desc: 'Aulas + Docentes + Horarios' },
              ].map(({ icon, step, desc }, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: i < 4 ? '1px solid #f0f0f0' : 'none' }}>
                  <span style={{ fontSize: 18, lineHeight: 1 }}>{icon}</span>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#333' }}>{step}</div>
                    <div style={{ fontSize: 11, color: '#888' }}>{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ════ PANEL DE RESULTADOS ════════════════════════════════ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {error && <div className="alert alert-danger">{error}</div>}
          {loading && <Spinner text={`Ejecutando ${algoInfo?.titulo}...`} />}

          {/* ── Estado vacío ──────────────────────────────────── */}
          {!resultado && !loading && (
            <div className="card">
              <div className="card-body spinner-wrap">
                <div style={{ fontSize: 48 }}>🧠</div>
                <p style={{ fontSize: 15, fontWeight: 600, color: '#555' }}>
                  Motor Inteligente de Planificación listo
                </p>
                <p style={{ fontSize: 13, color: '#888', textAlign: 'center', maxWidth: 400 }}>
                  Selecciona un algoritmo, configura los parámetros y pulsa <strong>Ejecutar</strong>.
                  El motor buscará la asignación óptima de aulas en el espacio de estados.
                </p>
              </div>
            </div>
          )}

          {resultado && (
            <>
              {/* ── Banner de resultado ───────────────────────── */}
              <div className={`search-result-banner ${resultado.encontrado ? 'success' : 'failure'}`}>
                <span className="banner-icon">{resultado.encontrado ? '✅' : '⚠️'}</span>
                <div>
                  <div className="banner-title">
                    {resultado.encontrado
                      ? `Solución encontrada — ${resultado.algoritmo_usado}`
                      : `Sin solución — ${resultado.algoritmo_usado}`}
                  </div>
                  <div className="banner-sub">
                    {resultado.encontrado
                      ? `${resultado.acciones.length} acciones · Costo total: ${resultado.costo} · ${stats?.tiempo_ms}ms`
                      : resultado.razon}
                  </div>
                </div>
              </div>

              {/* ── KPIs de métricas de búsqueda ──────────────── */}
              <div className="metrics-grid">
                {[
                  { label: 'Tiempo',      value: `${stats?.tiempo_ms}ms` },
                  { label: 'Nodos Exp.', value: stats?.nodos_expandidos },
                  { label: 'Nodos Gen.', value: stats?.nodos_generados },
                  { label: 'Profundidad', value: stats?.profundidad },
                  { label: 'Costo Total', value: resultado.costo },
                  { label: 'Acciones',   value: stats?.longitud_camino },
                ].map(({ label, value }) => (
                  <div key={label} className="metric-card">
                    <div className="metric-value">{value}</div>
                    <div className="metric-label">{label}</div>
                  </div>
                ))}
              </div>

              {/* ── KPIs de precisión (F1, Precision, Recall) ─── */}
              {resultado.metricas_precision && (
                <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(130px,1fr))' }}>
                  {[
                    { label: 'F1-Score',   value: (resultado.metricas_precision.f1_score * 100).toFixed(1) + '%',   color: resultado.metricas_precision.f1_score >= 0.7 ? 'var(--verde-optimo)' : resultado.metricas_precision.f1_score >= 0.5 ? '#E65100' : 'var(--rojo-utp)' },
                    { label: 'Precisión',  value: (resultado.metricas_precision.precision * 100).toFixed(1) + '%',  color: resultado.metricas_precision.precision >= 0.7 ? 'var(--verde-optimo)' : '#E65100' },
                    { label: 'Recall',     value: (resultado.metricas_precision.recall * 100).toFixed(1) + '%',     color: resultado.metricas_precision.recall >= 0.7 ? 'var(--verde-optimo)' : '#E65100' },
                    { label: 'Accuracy',   value: (resultado.metricas_precision.accuracy * 100).toFixed(1) + '%',   color: resultado.metricas_precision.accuracy >= 0.7 ? 'var(--verde-optimo)' : '#E65100' },
                    { label: 'Cobertura',  value: resultado.metricas_precision.cobertura_alumnos_pct.toFixed(1) + '%', color: resultado.metricas_precision.cobertura_alumnos_pct >= 90 ? 'var(--verde-optimo)' : '#E65100' },
                    { label: 'Ef. Búsq.', value: resultado.metricas_precision.eficiencia_busqueda + '%',            color: resultado.metricas_precision.eficiencia_busqueda >= 20 ? 'var(--verde-optimo)' : '#E65100' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="metric-card">
                      <div className="metric-value" style={{ color, fontSize: 22 }}>{value}</div>
                      <div className="metric-label">{label}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Tabs de contenido ─────────────────────────── */}
              <div className="card">
                <div className="card-header" style={{ paddingBottom: 0 }}>
                  <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', paddingBottom: 0 }}>
                    {[
                      { key: 'planificacion', label: '📋 Planificación' },
                      { key: 'estados',       label: '🔄 Estados' },
                      { key: 'acciones',      label: '⚡ Acciones' },
                      { key: 'precision',     label: '🎯 Precisión' },
                      { key: 'heuristica',    label: '📐 Heurística' },
                      { key: 'radar',         label: '📊 Radar' },
                    ].map(tab => (
                      <button
                        key={tab.key}
                        onClick={() => setTabActiva(tab.key)}
                        style={{
                          padding: '10px 14px',
                          border: 'none',
                          background: 'none',
                          cursor: 'pointer',
                          fontFamily: 'inherit',
                          fontSize: 13,
                          fontWeight: tabActiva === tab.key ? 700 : 500,
                          color: tabActiva === tab.key ? 'var(--rojo-utp)' : '#888',
                          borderBottom: tabActiva === tab.key ? '2px solid var(--rojo-utp)' : '2px solid transparent',
                          marginBottom: -1,
                          transition: 'all .15s',
                        }}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="card-body">

                  {/* TAB: Planificación final */}
                  {tabActiva === 'planificacion' && (
                    resultado.planificacion?.length > 0 ? (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Sección</th>
                              <th>Aula</th>
                              <th>Pabellón</th>
                              <th>Turno</th>
                              <th>Docente</th>
                              <th>Alumnos</th>
                              <th>Capacidad</th>
                              <th>Ocupación</th>
                              <th>Estado</th>
                            </tr>
                          </thead>
                          <tbody>
                            {resultado.planificacion.map(s => (
                              <tr key={s.seccion}>
                                <td>
                                  <div className="planificacion-seccion">
                                    <span className="seccion-badge">{s.seccion.replace('S', '')}</span>
                                    {s.seccion}
                                  </div>
                                </td>
                                <td><strong>{s.aula_id}</strong></td>
                                <td>{s.pabellon}</td>
                                <td>{s.turno}</td>
                                <td>{s.docente ?? <em style={{ color: '#bbb' }}>Sin asignar</em>}</td>
                                <td>{s.alumnos}</td>
                                <td>{s.capacidad}</td>
                                <td>{(s.ocupacion * 100).toFixed(1)}%</td>
                                <td><OcupacionBadge estado={s.estado_ocupacion} /></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="spinner-wrap">
                        <p>No hay planificación disponible (búsqueda sin solución).</p>
                      </div>
                    )
                  )}

                  {/* TAB: Estados inicial y final */}
                  {tabActiva === 'estados' && (
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                      {/* Estado inicial */}
                      <div className="state-card">
                        <div className="state-card-header">
                          <div className="state-dot inicial"></div>
                          <h4>Estado Inicial</h4>
                        </div>
                        {resultado.estado_inicial && Object.entries({
                          'Demanda total':      resultado.estado_inicial.demanda_total,
                          'Alumnos restantes':  resultado.estado_inicial.alumnos_restantes,
                          'Aulas disponibles':  resultado.estado_inicial.aulas_disponibles_count,
                          'Docentes':           resultado.estado_inicial.docentes_disponibles,
                          'Horarios':           resultado.estado_inicial.horarios_disponibles?.length,
                          'Secciones abiertas': resultado.estado_inicial.secciones_abiertas,
                          'g(n)':               resultado.estado_inicial.costo_acumulado,
                          'h(n)':               resultado.estado_inicial.heuristica,
                          'f(n)':               resultado.estado_inicial.f,
                        }).map(([k, v]) => (
                          <div key={k} className="state-row">
                            <span className="s-label">{k}</span>
                            <span className="s-value">{typeof v === 'number' ? v.toFixed?.(2) ?? v : v}</span>
                          </div>
                        ))}
                      </div>

                      {/* Estado final */}
                      <div className="state-card">
                        <div className="state-card-header">
                          <div className="state-dot final"></div>
                          <h4>Estado Final {resultado.encontrado ? '✅' : '⚠️'}</h4>
                        </div>
                        {resultado.estado_final ? Object.entries({
                          'Demanda total':      resultado.estado_final.demanda_total,
                          'Alumnos restantes':  resultado.estado_final.alumnos_restantes,
                          'Alumnos asignados':  resultado.estado_final.alumnos_asignados,
                          'Secciones abiertas': resultado.estado_final.secciones_abiertas,
                          'Docentes rest.':     resultado.estado_final.docentes_disponibles,
                          'Aulas asignadas':    resultado.estado_final.aulas_asignadas?.length,
                          'Cupos totales':      resultado.estado_final.cupos_totales,
                          'g(n)':               resultado.estado_final.costo_acumulado,
                          'h(n)':               resultado.estado_final.heuristica,
                          'f(n)':               resultado.estado_final.f,
                        }).map(([k, v]) => (
                          <div key={k} className="state-row">
                            <span className="s-label">{k}</span>
                            <span className="s-value">{typeof v === 'number' ? parseFloat(v).toFixed(2) : (v ?? '-')}</span>
                          </div>
                        )) : (
                          <p style={{ fontSize: 13, color: '#888', padding: '8px 0' }}>
                            No se alcanzó el estado objetivo.
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB: Timeline de acciones */}
                  {tabActiva === 'acciones' && (
                    resultado.acciones?.length > 0 ? (
                      <div className="planner-timeline">
                        {resultado.acciones.map((accion, i) => (
                          <div key={i} className="timeline-item">
                            <div className="timeline-dot">
                              {ACCION_ICONS[accion] ?? '🔧'}
                            </div>
                            <div className="timeline-content">
                              <div className="timeline-action">
                                Paso {i + 1}: {accion.replace(/_/g, ' ')}
                              </div>
                              <div className="timeline-detail">
                                {ACCION_DESC[accion] ?? 'Operador aplicado'}
                              </div>
                            </div>
                          </div>
                        ))}
                        <div className="timeline-item">
                          <div className="timeline-dot" style={{ background: 'var(--verde-optimo)' }}>
                            🏁
                          </div>
                          <div className="timeline-content" style={{ borderLeftColor: 'var(--verde-optimo)' }}>
                            <div className="timeline-action">Estado objetivo alcanzado</div>
                            <div className="timeline-detail">
                              Costo total: {resultado.costo} · Profundidad: {stats?.profundidad}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="spinner-wrap">
                        <p>No hay acciones registradas.</p>
                      </div>
                    )
                  )}

                  {/* TAB: Heurística diagnóstico */}
                  {tabActiva === 'heuristica' && resultado.heuristica_diagnostico && (
                    <div>
                      <div style={{ marginBottom: 16 }}>
                        <p style={{ fontSize: 13, color: '#666', lineHeight: 1.6 }}>
                          Desglose de <strong>h(n)</strong> en el estado inicial.
                          La heurística es <em>admisible</em>: nunca sobreestima el costo real,
                          lo que garantiza la optimalidad de A*.
                        </p>
                      </div>
                      <div className="heuristica-bars">
                        {[
                          { key: 'desperdicio_cupos',      label: 'Cupos desperdiciados' },
                          { key: 'sobreocupacion_alumnos', label: 'Sobreocupación' },
                          { key: 'deficit_docentes',       label: 'Déficit docentes' },
                          { key: 'conflictos_horario',     label: 'Conflictos horario' },
                          { key: 'alumnos_restantes',      label: 'Alumnos sin asignar' },
                          { key: 'secciones_abiertas',     label: 'Secciones abiertas' },
                        ].map(({ key, label }) => {
                          const val = resultado.heuristica_diagnostico[key] ?? 0;
                          const pct = Math.min(100, (val / maxHDiag) * 100);
                          return (
                            <div key={key} className="h-bar-row">
                              <span className="h-bar-label">{label}</span>
                              <div className="h-bar-track">
                                <div className="h-bar-fill" style={{ width: `${pct}%` }} />
                              </div>
                              <span className="h-bar-val">{typeof val === 'number' ? val.toFixed(1) : val}</span>
                            </div>
                          );
                        })}
                      </div>
                      <div style={{ marginTop: 16, padding: 12, background: '#f9f9f9', borderRadius: 8, fontSize: 12, color: '#666' }}>
                        <strong>h(n) total inicial:</strong> {resultado.heuristica_diagnostico.total} &nbsp;|&nbsp;
                        <strong>f(n) = g + h:</strong> {((resultado.estado_inicial?.costo_acumulado ?? 0) + (resultado.heuristica_diagnostico.total ?? 0)).toFixed(2)}
                      </div>
                    </div>
                  )}

                   {/* TAB: Métricas de Precisión */}
                   {tabActiva === 'precision' && (
                     resultado.metricas_precision ? (
                       <div>
                         {/* Caja de definiciones */}
                         <div style={{ background: '#EEF2FF', border: '1px solid #C7D2FE', borderRadius: 8, padding: '12px 16px', marginBottom: 20, fontSize: 12.5, color: '#1E3A8A', lineHeight: 1.7 }}>
                           <strong>📌 Definiciones adaptadas al dominio de planificación</strong><br />
                           <strong>TP (Verdadero Positivo):</strong> alumno asignado en aula con ocupación óptima (65–90%).<br />
                           <strong>FP (Falso Positivo):</strong> alumno asignado en aula fuera del rango óptimo.<br />
                           <strong>FN (Falso Negativo):</strong> alumno sin asignar (demanda no cubierta).<br />
                           <strong>F1-Score</strong> = 2 × Precisión × Recall / (Precisión + Recall)
                         </div>

                         {/* Gauges */}
                         <div style={{ display: 'flex', gap: 20, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 24, padding: '8px 0' }}>
                           <GaugeSVG value={resultado.metricas_precision.f1_score}  label="F1-Score"  color={scoreColor(resultado.metricas_precision.f1_score)} />
                           <GaugeSVG value={resultado.metricas_precision.precision} label="Precisión" color={scoreColor(resultado.metricas_precision.precision)} />
                           <GaugeSVG value={resultado.metricas_precision.recall}    label="Recall"    color={scoreColor(resultado.metricas_precision.recall)} />
                           <GaugeSVG value={resultado.metricas_precision.accuracy}  label="Accuracy"  color={scoreColor(resultado.metricas_precision.accuracy)} />
                         </div>

                         {/* Barras de interpretación */}
                         <InterpRow
                           icon="🎯" label="F1-Score — Balance general"
                           value={(resultado.metricas_precision.f1_score * 100).toFixed(1) + '%'}
                           pct={resultado.metricas_precision.f1_score * 100}
                           interp={resultado.metricas_precision.interpretaciones?.f1_score}
                           color={scoreColor(resultado.metricas_precision.f1_score)}
                         />
                         <InterpRow
                           icon="🏆" label="Precisión — Asignaciones en rango óptimo"
                           value={(resultado.metricas_precision.precision * 100).toFixed(1) + '%'}
                           pct={resultado.metricas_precision.precision * 100}
                           interp={resultado.metricas_precision.interpretaciones?.precision}
                           color={scoreColor(resultado.metricas_precision.precision)}
                         />
                         <InterpRow
                           icon="📡" label="Recall — Cobertura en condición óptima"
                           value={(resultado.metricas_precision.recall * 100).toFixed(1) + '%'}
                           pct={resultado.metricas_precision.recall * 100}
                           interp={resultado.metricas_precision.interpretaciones?.recall}
                           color={scoreColor(resultado.metricas_precision.recall)}
                         />
                         <InterpRow
                           icon="🎓" label="Cobertura total de alumnos"
                           value={resultado.metricas_precision.cobertura_alumnos_pct.toFixed(1) + '%'}
                           pct={resultado.metricas_precision.cobertura_alumnos_pct}
                           interp={resultado.metricas_precision.interpretaciones?.cobertura}
                           color={resultado.metricas_precision.cobertura_alumnos_pct >= 99 ? '#2E7D32' : resultado.metricas_precision.cobertura_alumnos_pct >= 90 ? '#1565C0' : '#E65100'}
                         />
                         <InterpRow
                           icon="⚡" label="Eficiencia del algoritmo de búsqueda"
                           value={resultado.metricas_precision.eficiencia_busqueda + '%'}
                           pct={Math.min(100, resultado.metricas_precision.eficiencia_busqueda * 2)}
                           interp={resultado.metricas_precision.interpretaciones?.eficiencia_busqueda}
                           color={resultado.metricas_precision.eficiencia_busqueda >= 20 ? '#2E7D32' : '#E65100'}
                         />

                         {/* Matriz de confusión */}
                         <div style={{ marginTop: 20 }}>
                           <div style={{ fontWeight: 700, fontSize: 13, color: '#333', marginBottom: 10 }}>Matriz de Confusión (adaptada al dominio)</div>
                           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                             {[
                               { label: '✅ Verdaderos Positivos (TP)', value: resultado.metricas_precision.verdaderos_positivos, desc: 'Alumnos en aulas con ocupación óptima', bg: '#E8F5E9', color: '#2E7D32' },
                               { label: '⚠️ Falsos Positivos (FP)',    value: resultado.metricas_precision.falsos_positivos,    desc: 'Alumnos en aulas fuera del rango óptimo', bg: '#FFF8E1', color: '#E65100' },
                               { label: '❌ Falsos Negativos (FN)',    value: resultado.metricas_precision.falsos_negativos,    desc: 'Alumnos que no pudieron ser asignados', bg: '#FFEBEE', color: '#8B0000' },
                               { label: '📊 Total analizado',          value: resultado.metricas_precision.alumnos_cubiertos + resultado.metricas_precision.alumnos_sin_cubrir, desc: 'Demanda total de alumnos a planificar', bg: '#F3F4F6', color: '#555' },
                             ].map(({ label, value, desc, bg, color }) => (
                               <div key={label} style={{ background: bg, borderRadius: 8, padding: '12px 14px' }}>
                                 <div style={{ fontSize: 10, fontWeight: 700, color: '#777', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '.04em' }}>{label}</div>
                                 <div style={{ fontSize: 26, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
                                 <div style={{ fontSize: 11, color: '#888', marginTop: 5 }}>{desc}</div>
                               </div>
                             ))}
                           </div>
                         </div>

                         {/* Pie de resumen */}
                         <div style={{ marginTop: 14, padding: '10px 16px', background: '#F9FAFB', borderRadius: 8, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10, fontSize: 12.5, color: '#555' }}>
                           <span>🏫 Secciones óptimas: <strong>{resultado.metricas_precision.secciones_optimas}</strong> / {resultado.metricas_precision.secciones_total}</span>
                           <span>👥 Alumnos bien ubicados: <strong>{resultado.metricas_precision.alumnos_bien_ubicados}</strong> / {resultado.metricas_precision.alumnos_cubiertos}</span>
                           <span>📉 Sin cubrir: <strong style={{ color: resultado.metricas_precision.alumnos_sin_cubrir > 0 ? '#8B0000' : '#2E7D32' }}>{resultado.metricas_precision.alumnos_sin_cubrir}</strong></span>
                           <span>📐 Ocupación prom.: <strong>{(resultado.metricas_precision.ocupacion_promedio * 100).toFixed(1)}%</strong></span>
                         </div>
                       </div>
                     ) : (
                       <div style={{ textAlign: 'center', padding: '40px 20px', color: '#888' }}>
                         <div style={{ fontSize: 36, marginBottom: 12 }}>🔄</div>
                         <p style={{ fontSize: 13 }}>Ejecuta la planificación para ver las métricas de precisión.</p>
                       </div>
                     )
                   )}


                  {tabActiva === 'radar' && stats && (
                    <div>
                      <ResponsiveContainer width="100%" height={300}>
                        <RadarChart data={radarData}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                          <Radar
                            name={resultado.algoritmo_usado}
                            dataKey="value"
                            stroke="var(--rojo-utp)"
                            fill="var(--rojo-utp)"
                            fillOpacity={0.25}
                          />
                          <Tooltip />
                        </RadarChart>
                      </ResponsiveContainer>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 16 }}>
                        {[
                          { label: 'Algoritmo', value: resultado.algoritmo_usado },
                          { label: 'Tiempo (ms)', value: stats.tiempo_ms },
                          { label: 'Nodos expandidos', value: stats.nodos_expandidos },
                          { label: 'Nodos generados', value: stats.nodos_generados },
                          { label: 'Profundidad', value: stats.profundidad },
                          { label: 'Costo final', value: resultado.costo },
                        ].map(({ label, value }) => (
                          <div key={label} style={{ padding: '10px 14px', background: 'var(--gris-fondo)', borderRadius: 8 }}>
                            <div style={{ fontSize: 11, color: '#888', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.05em' }}>{label}</div>
                            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--rojo-utp)', marginTop: 4 }}>{value}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              </div>

              {/* ── Árbol de búsqueda simplificado ───────────── */}
              {resultado.camino?.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h3>Árbol de Búsqueda — Camino Encontrado</h3>
                    <p style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                      Cada nodo representa un estado del problema. El camino va del estado inicial (azul) al objetivo (verde).
                    </p>
                  </div>
                  <div className="card-body">
                    <div className="tree-container">
                      {resultado.camino.map((nodo, i) => (
                        <div key={i} className="tree-level">
                          <div
                            className={`tree-node ${i === 0 ? 'explored' : i === resultado.camino.length - 1 ? 'goal' : ''}`}
                            style={{
                              animationDelay: `${i * 0.06}s`,
                              borderColor: i === 0
                                ? '#1976D2'
                                : i === resultado.camino.length - 1
                                  ? 'var(--verde-optimo)'
                                  : undefined,
                              background: i === 0
                                ? '#E3F2FD'
                                : i === resultado.camino.length - 1
                                  ? '#E8F5E9'
                                  : undefined,
                            }}
                          >
                            <div style={{ fontWeight: 700, fontSize: 12 }}>
                              {i === 0 ? '🔵 Inicio' : i === resultado.camino.length - 1 ? '🟢 Objetivo' : `Nodo ${i}`}
                            </div>
                            <div style={{ color: '#888', fontSize: 10, marginTop: 2 }}>
                              {nodo.accion
                                ? `${ACCION_ICONS[nodo.accion] ?? '🔧'} ${nodo.accion.replace(/_/g, ' ')}`
                                : 'Estado raíz'}
                            </div>
                            <div style={{ fontSize: 10, marginTop: 2, color: '#aaa' }}>
                              f={nodo.f?.toFixed(1)} · g={nodo.costo?.toFixed(1)}
                            </div>
                          </div>
                          {i < resultado.camino.length - 1 && (
                            <div style={{ textAlign: 'center', color: '#ccc', fontSize: 20, margin: '4px 0' }}>↓</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
