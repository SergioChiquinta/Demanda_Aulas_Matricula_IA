// src/pages/GA2Secciones.jsx
import { useState } from 'react';
import api from '../api/client';
import KPICard from '../components/KPICard';
import OcupacionBadge from '../components/OcupacionBadge';
import Spinner from '../components/Spinner';

const DEFAULT = { demanda: 60, capacidad: 40, docentes: 3, laboratorio: false };

export default function GA2Secciones() {
  const [form,    setForm]    = useState(DEFAULT);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const ejecutar = () => {
    setError(null);
    setLoading(true);
    const capEf = Math.max(1, Math.floor(form.capacidad * (form.laboratorio ? 0.85 : 1.0)));
    api.post('/ga/secciones', {
      demanda_plan:        form.demanda,
      capacidad_efectiva:  capEf,
      docentes_disponibles: form.docentes,
    })
      .then(r => setResult({ ...r.data, cap_ef: capEf }))
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setLoading(false));
  };

  // Clásico: ceil(demanda / cap_segura)
  const capEf     = Math.max(1, Math.floor(form.capacidad * (form.laboratorio ? 0.85 : 1.0)));
  const capSegura = Math.max(1, Math.floor(capEf * 0.90));
  const clasico   = Math.max(1, Math.ceil(form.demanda / capSegura));

  const ocup = result?.ocupacion ?? 0;
  const colorOcup = ocup >= 0.65 && ocup <= 0.90 ? '#2E7D32' : '#E65100';

  return (
    <div>
      <div className="page-header">
        <h2>AG #2 — Optimización de Distribución de Secciones</h2>
        <p>Optimiza el número de secciones y el factor de ocupación para minimizar hacinamiento y subutilización.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24 }}>
        {/* Form */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div className="card-header"><h3>Parámetros de entrada</h3></div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                ['demanda',   'Demanda total',     1, 300],
                ['capacidad', 'Capacidad por aula',1, 120],
                ['docentes',  'Docentes disponibles',0, 20],
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
                    checked={form.laboratorio}
                    onChange={e => set('laboratorio', e.target.checked)}
                  />
                  Requiere laboratorio (−15% capacidad)
                </label>
              </div>

              <div style={{ padding: '10px 0', borderTop: '1px solid #eee', fontSize: 12, color: '#888' }}>
                Cap. efectiva: <strong>{capEf}</strong> | Cap. segura (90%): <strong>{capSegura}</strong>
                <br/>Clásico (ceil): <strong>{clasico} secciones</strong>
              </div>

              <button className="btn btn-primary" onClick={ejecutar} disabled={loading}>
                {loading ? '⚙️ Ejecutando AG #2...' : '🧬 Ejecutar AG #2'}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {error   && <div className="alert alert-danger">{error}</div>}
          {loading && <Spinner text="Optimizando distribución de secciones..." />}

          {result && (
            <>
              <div className={`alert ${result.n_secciones === clasico ? 'alert-info' : 'alert-success'}`}>
                {result.n_secciones === clasico
                  ? `El AG confirma el resultado clásico: ${result.n_secciones} secciones.`
                  : `AG sugiere ${result.n_secciones} secciones vs ${clasico} del método clásico.`}
                {' '}Factor de ocupación óptimo: {(result.factor_ocupacion * 100).toFixed(0)}%
              </div>

              <div className="kpi-grid">
                <KPICard label="Secciones (AG)"      value={result.n_secciones} accent="#8B0000" />
                <KPICard label="Secciones (Clásico)" value={clasico}             accent="#888" />
                <KPICard label="Ocupación AG"         value={`${(ocup * 100).toFixed(1)}%`} accent={colorOcup} />
                <KPICard label="Total Cupos AG"       value={result.total_cupos} accent="#8B0000" />
              </div>

              {result.deficit_docentes > 0 && (
                <div className="alert alert-danger">
                  ⚠️ Déficit de {result.deficit_docentes} docente(s). El AG calculó {result.n_secciones} secciones pero solo hay {form.docentes} disponibles.
                </div>
              )}

              <div className="card">
                <div className="card-header"><h3>Distribución sugerida</h3></div>
                <div className="card-body" style={{ padding: 0 }}>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr><th>Sección</th><th>Alumnos</th><th>Capacidad</th><th>Ocupación</th><th>Estado</th></tr>
                      </thead>
                      <tbody>
                        {result.secciones?.map(s => {
                          const estado =
                            s.ocupacion > 1     ? 'Excede aforo' :
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
                Fitness AG: {result.fitness} | Cap. segura AG: {result.cap_segura}
              </div>
            </>
          )}

          {!result && !loading && (
            <div className="card">
              <div className="card-body" style={{ textAlign: 'center', padding: '40px 0', color: '#aaa' }}>
                Ejecuta el AG para ver la distribución óptima de secciones.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
