// src/pages/MiHorario.jsx
import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import Spinner from '../components/Spinner';
import HorarioGrid from '../components/HorarioGrid';
import { exportarHorarioPDF } from '../utils/exportPdf';

export default function MiHorario() {
  const { usuario } = useAuth();

  const [disponibles, setDisponibles] = useState([]);
  const [misSecciones, setMisSecciones] = useState([]);
  const [conflictos, setConflictos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [vista, setVista] = useState('disponible'); // 'disponible' | 'mio'
  const [busqueda, setBusqueda] = useState('');
  const [accionEnCurso, setAccionEnCurso] = useState(null);
  const gridRef = useRef(null);

  const cargar = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.get('/horarios/administrativo', { params: { carrera_id: usuario.carrera_id, ciclo: usuario.ciclo_actual } }),
      api.get('/horarios/estudiante'),
    ])
      .then(([admin, mio]) => {
        setDisponibles(admin.data.secciones || []);
        setMisSecciones(mio.data.secciones || []);
        setConflictos(mio.data.conflictos || []);
      })
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setLoading(false));
  }, [usuario.carrera_id, usuario.ciclo_actual]);

  useEffect(() => { cargar(); }, [cargar]);

  const misSeccionIds = useMemo(() => new Set(misSecciones.map(s => s.id_seccion)), [misSecciones]);
  const misCursoIds = useMemo(() => new Set(misSecciones.map(s => s.id_curso)), [misSecciones]);
  const misBloqueIds = useMemo(() => new Set(misSecciones.map(s => s.id_bloque)), [misSecciones]);
  const conflictoBloqueIds = useMemo(() => new Set(conflictos), [conflictos]);

  const cursosDisponibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const porCurso = new Map();
    disponibles.forEach(s => {
      if (q && !s.nombre_curso.toLowerCase().includes(q)) return;
      if (!porCurso.has(s.nombre_curso)) porCurso.set(s.nombre_curso, []);
      porCurso.get(s.nombre_curso).push(s);
    });
    return [...porCurso.entries()];
  }, [disponibles, busqueda]);

  const matricular = (seccionId) => {
    setAccionEnCurso(seccionId);
    api.post('/horarios/estudiante/matricular', { seccion_id: seccionId })
      .then(cargar)
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setAccionEnCurso(null));
  };

  const desmatricular = (idMatricula) => {
    setAccionEnCurso(idMatricula);
    api.delete(`/horarios/estudiante/matricula/${idMatricula}`)
      .then(cargar)
      .catch(e => setError(e.response?.data?.error || e.message))
      .finally(() => setAccionEnCurso(null));
  };

  const exportarPDF = () => {
    exportarHorarioPDF(gridRef.current, {
      titulo: `Mi Horario — ${usuario.nombre}`,
      subtitulo: `${usuario.carrera_nombre} · Ciclo ${usuario.ciclo_actual} · Código ${usuario.codigo_universitario}`,
      nombreArchivo: 'mi_horario.pdf',
    });
  };

  const seccionesGrilla = vista === 'mio' ? misSecciones : disponibles;

  return (
    <div>
      <div className="page-header">
        <h2>Mi Horario</h2>
        <p>
          Arma tu horario eligiendo secciones del horario administrativo vigente para tu carrera y ciclo.
          Las secciones que ya elegiste se resaltan con borde rojo; si dos caen en el mismo bloque, se marcan en rojo como conflicto.
        </p>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {conflictos.length > 0 && (
        <div className="alert alert-danger">
          ⚠️ Tienes {conflictos.length} choque(s) de horario entre las secciones que elegiste. Revísalas abajo.
        </div>
      )}

      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="algo-selector" style={{ maxWidth: 320 }}>
          <button className={`algo-btn${vista === 'disponible' ? ' selected' : ''}`} onClick={() => setVista('disponible')}>
            <span className="algo-label">Horario disponible</span>
            <span className="algo-desc">Horario visualizado para ayuda</span>
          </button>
          <button className={`algo-btn${vista === 'mio' ? ' selected' : ''}`} onClick={() => setVista('mio')}>
            <span className="algo-label">Solo mi horario</span>
            <span className="algo-desc">{misSecciones.length} sección(es)</span>
          </button>
        </div>
        {vista === 'mio' && (
          <button className="btn btn-secondary" onClick={exportarPDF} disabled={seccionesGrilla.length === 0}>
            📄 Exportar a PDF
          </button>
        )}
      </div>

      {loading ? (
        <Spinner text="Cargando tu horario..." />
      ) : (
        <HorarioGrid
          ref={gridRef}
          secciones={seccionesGrilla}
          misSeccionIds={misSeccionIds}
          conflictoBloqueIds={conflictoBloqueIds}
          vacioTexto={vista === 'mio'
            ? 'Aún no te has matriculado en ninguna sección.'
            : 'El horario administrativo de tu carrera/ciclo todavía no fue generado.'}
        />
      )}

      <div className="horario-legend">
        <span><span className="lg-swatch" style={{ background: '#fff', border: '2px solid var(--rojo-utp)' }} /> Sección elegida por ti</span>
        <span><span className="lg-swatch" style={{ background: '#ffebee', border: '2px solid #B71C1C' }} /> Choque de horario</span>
      </div>

      <div className="page-header" style={{ marginTop: 36 }}>
        <h2>Cursos disponibles — {usuario.carrera_nombre}, Ciclo {usuario.ciclo_actual}</h2>
        <p>Elige las secciones que quieras agregar a tu horario personal.</p>
      </div>

      <div className="form-group" style={{ maxWidth: 320, marginBottom: 16 }}>
        <input type="text" placeholder="Buscar curso..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
      </div>

      <div className="card">
        <div className="card-body" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Curso</th>
                  <th>Sección</th>
                  <th>Aula</th>
                  <th>Docente</th>
                  <th>Día / Hora</th>
                  <th>Cupos</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cursosDisponibles.flatMap(([curso, secs]) => secs.map((s) => {
                  const yaElegida = misSeccionIds.has(s.id_seccion);
                  const miMatricula = misSecciones.find(m => m.id_seccion === s.id_seccion);
                  const mismoCursoOtraSeccion = !yaElegida && misCursoIds.has(s.id_curso);
                  const enCruce = !yaElegida && !mismoCursoOtraSeccion && misBloqueIds.has(s.id_bloque);
                  return (
                    <tr key={s.id_seccion}>
                      <td style={{ fontWeight: 600 }}>{curso}</td>
                      <td>{s.codigo_seccion}</td>
                      <td>{s.codigo_aula} (pab. {s.pabellon}, piso {s.piso})</td>
                      <td>{s.nombre_docente}</td>
                      <td>{s.dia_semana} {s.hora_inicio?.slice(0, 5)}-{s.hora_fin?.slice(0, 5)}</td>
                      <td>{s.alumnos_estimados}/{s.aforo}</td>
                      <td>
                        {yaElegida ? (
                          <button
                            className="btn btn-outline"
                            style={{ padding: '6px 12px', fontSize: 12 }}
                            disabled={accionEnCurso === miMatricula?.id_matricula}
                            onClick={() => desmatricular(miMatricula.id_matricula)}
                          >
                            Quitar
                          </button>
                        ) : mismoCursoOtraSeccion ? (
                          <button className="btn btn-blocked" style={{ padding: '6px 12px', fontSize: 12 }} disabled title="Ya elegiste otra sección de este curso">
                            Ya matriculado
                          </button>
                        ) : enCruce ? (
                          <button className="btn btn-blocked" style={{ padding: '6px 12px', fontSize: 12 }} disabled title="Choca con otra sección ya elegida">
                            En cruce
                          </button>
                        ) : (
                          <button
                            className="btn btn-primary"
                            style={{ padding: '6px 12px', fontSize: 12 }}
                            disabled={accionEnCurso === s.id_seccion}
                            onClick={() => matricular(s.id_seccion)}
                          >
                            Matricularme
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                }))}
                {cursosDisponibles.length === 0 && (
                  <tr><td colSpan={7} style={{ textAlign: 'center', color: '#aaa', padding: 30 }}>No hay secciones disponibles.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
