// src/pages/Dashboard.jsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import KPICard from '../components/KPICard';
import Spinner from '../components/Spinner';

const HEADERS = ['Periodo', 'Asignatura', 'Pabellón', 'Turno', 'Capacidad', 'Matriculados'];
const FIELDS  = ['periodo', 'nombre_curso', 'pabellon', 'horario_seccion', 'capacidad_aula', 'alumnos_matriculados'];

export default function Dashboard() {
  const [kpis,      setKpis]      = useState(null);
  const [metricas,  setMetricas]  = useState(null);
  const [operativo, setOperativo] = useState(null);
  const [rows,      setRows]      = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get('/datos/kpis'),
      api.get('/prediccion/metricas'),
      api.get('/datos/historico?limit=100'),
      api.get('/datos/estado-operativo'),
    ])
      .then(([k, m, h, o]) => {
        setKpis(k.data);
        setMetricas(m.data);
        setRows(h.data.data);
        setOperativo(o.data);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner text="Cargando datos desde MySQL..." />;
  if (error)   return <div className="alert alert-danger">❌ {error}</div>;

  const sinHorarioGenerado = operativo?.periodo_activo && operativo.secciones_totales === 0;

  return (
    <div>
      <div className="page-header">
        <h2>Resumen General Académico</h2>
        <p>Estado operativo actual del sistema e indicadores históricos del modelo predictivo.</p>
      </div>

      {/* ═══════════════════════════════════════════════════
          ESTADO OPERATIVO ACTUAL — lo más accionable primero
          ═══════════════════════════════════════════════════ */}
      {!operativo?.periodo_activo ? (
        <div className="alert alert-warning">
          ⚠️ No hay un periodo activo configurado. No se puede mostrar el estado operativo.
        </div>
      ) : (
        <>
          {sinHorarioGenerado && (
            <div className="alert alert-warning">
              ⚠️ Todavía no se generó el horario administrativo del periodo <strong>{operativo.periodo_activo.codigo_periodo}</strong>.{' '}
              <Link to="/horarios" style={{ fontWeight: 600 }}>Ir a Horarios</Link> para generarlo.
            </div>
          )}

          <div className="kpi-grid">
            <KPICard
              label="Periodo Activo"
              value={operativo.periodo_activo.codigo_periodo}
              sub="catálogo real UTP Lima Sur"
            />
            <KPICard
              label="Cursos con Horario"
              value={`${operativo.cursos_con_seccion} / ${operativo.cursos_totales}`}
              sub="cursos reales del periodo"
            />
            <KPICard
              label="Aulas en Uso"
              value={`${operativo.aulas_usadas} / ${operativo.aulas_totales}`}
              sub="de las 288 aulas del campus"
            />
            <KPICard
              label="Secciones Generadas"
              value={operativo.secciones_totales}
              sub="pipeline IA (Regresión → AG#2 → asignación)"
            />
            <KPICard
              label="Estudiantes Matriculados"
              value={operativo.estudiantes_matriculados}
              sub="con al menos 1 sección elegida"
            />
          </div>
        </>
      )}

      {/* ═══════════════════════════════════════════════════
          KPIs DEL MODELO / DATASET HISTÓRICO
          ═══════════════════════════════════════════════════ */}
      <div className="page-header" style={{ marginTop: 32 }}>
        <h2>Dataset Histórico y Modelo Predictivo</h2>
        <p>Indicadores del dataset sintético usado para calibrar y entrenar los modelos de IA.</p>
      </div>

      <div className="kpi-grid">
        <KPICard
          label="Total Matrículas (Histórico)"
          value={Number(kpis?.total_matriculas).toLocaleString('es-PE')}
          sub={`${kpis?.total_registros} registros`}
        />
        <KPICard
          label="Aforo Promedio por Aula"
          value={`${Math.round(kpis?.aforo_promedio)} alumnos`}
          sub="capacidad física media"
        />
        <KPICard
          label="Margen de Error (MAE)"
          value={`± ${metricas?.lineal?.MAE?.toFixed(2)}`}
          sub="Regresión Lineal Múltiple"
        />
        <KPICard
          label="Penalización Error (RMSE)"
          value={metricas?.lineal?.RMSE?.toFixed(2)}
          sub="Regresión Lineal Múltiple"
        />
      </div>

      {/* ═══════════════════════════════════════════════════
          TABLA DE REGISTROS HISTÓRICOS — al final, es dato de referencia
          ═══════════════════════════════════════════════════ */}
      <div className="card" style={{ marginTop: 28 }}>
        <div className="card-header" style={{ padding: '10px 10px 10px 10px' }}>
          <h3>Últimos 100 Registros Históricos</h3>
        </div>
        <div className="card-body" style={{ padding: '0px 0px 0px 0px' }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>{HEADERS.map(h => <th key={h}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i}>
                    {FIELDS.map(f => <td key={f}>{row[f] ?? '—'}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
