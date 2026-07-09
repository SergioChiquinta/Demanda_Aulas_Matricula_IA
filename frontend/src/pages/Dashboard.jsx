// src/pages/Dashboard.jsx
import { useEffect, useState } from 'react';
import api from '../api/client';
import KPICard from '../components/KPICard';
import Spinner from '../components/Spinner';

const HEADERS = ['Periodo', 'Asignatura', 'Pabellón', 'Turno', 'Capacidad', 'Matriculados'];
const FIELDS  = ['periodo', 'nombre_curso', 'pabellon', 'horario_seccion', 'capacidad_aula', 'alumnos_matriculados'];

export default function Dashboard() {
  const [kpis,    setKpis]    = useState(null);
  const [metricas,setMetricas]= useState(null);
  const [rows,    setRows]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get('/datos/kpis'),
      api.get('/prediccion/metricas'),
      api.get('/datos/historico?limit=100'),
    ])
      .then(([k, m, h]) => {
        setKpis(k.data);
        setMetricas(m.data);
        setRows(h.data.data);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner text="Cargando datos desde MySQL..." />;
  if (error)   return <div className="alert alert-danger">❌ {error}</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Resumen General Académico</h2>
        <p>Indicadores históricos de matrícula y precisión del modelo predictivo.</p>
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

      <div className="card">
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
