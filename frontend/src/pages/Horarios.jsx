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

  //Preview modal state de horarios
  const [showPreview, setShowPreview] = useState(false);

  // Aula actualmente mostrada
  const [previewIndex, setPreviewIndex] = useState(0);

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

  // =======================================================
  // Simulación estática de horarios generados por IA
  // (En el futuro será reemplazado por el resultado real)
  // =======================================================

  const scheduleColors = {
    green: "#D1FAE5",
    blue: "#DBEAFE",
    yellow: "#FEF3C7",
    pink: "#FCE7F3",
    purple: "#E9D5FF",
    cyan: "#E0F2FE"
  };

  const previewAulas = [
    {
      aula: "A203",
      pabellon: "Pabellón A",
      capacidad: 40,
      ocupacion: 91,
      conflictos: 0,
      bloques: [
        { hora: "07:30 - 09:00", lunes: { curso: "Programación I", seccion: "SEC-01", color: "green" }, martes: null, miercoles: { curso: "Base de Datos", seccion: "SEC-02", color: "blue" }, jueves: null, viernes: { curso: "IA Clásica", seccion: "SEC-01", color: "pink" }, sabado: { curso: "Redes I", seccion: "SEC-03", color: "cyan" }, domingo: null },
        { hora: "09:00 - 10:30", lunes: null, martes: { curso: "Ingeniería Software", seccion: "SEC-01", color: "yellow" }, miercoles: null, jueves: { curso: "Matemática", seccion: "SEC-02", color: "purple" }, viernes: null, sabado: null, domingo: { curso: "Física", seccion: "SEC-01", color: "green" } },
        { hora: "10:30 - 12:00", lunes: { curso: "Arquitectura", seccion: "SEC-01", color: "blue" }, martes: null, miercoles: { curso: "POO", seccion: "SEC-03", color: "green" }, jueves: null, viernes: { curso: "Estadística", seccion: "SEC-01", color: "yellow" }, sabado: { curso: "Sistemas Operativos", seccion: "SEC-02", color: "yellow" }, domingo: null },
        { hora: "12:00 - 13:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: null, domingo: null },
        { hora: "13:30 - 15:00", lunes: { curso: "Laboratorio IA", seccion: "LAB-01", color: "pink" }, martes: null, miercoles: null, jueves: { curso: "Minería de Datos", seccion: "SEC-01", color: "purple" }, viernes: null, sabado: null, domingo: null },
        { hora: "15:00 - 16:30", lunes: null, martes: { curso: "Algoritmos", seccion: "SEC-04", color: "green" }, miercoles: null, jueves: null, viernes: { curso: "Testing", seccion: "SEC-01", color: "cyan" }, sabado: null, domingo: null },
        { hora: "16:30 - 18:00", lunes: null, martes: null, miercoles: { curso: "Proyecto Software", seccion: "SEC-02", color: "blue" }, jueves: null, viernes: null, sabado: null, domingo: null },
        { hora: "18:00 - 19:30", lunes: { curso: "Cloud Computing", seccion: "SEC-01", color: "purple" }, martes: null, miercoles: null, jueves: { curso: "DevOps", seccion: "SEC-02", color: "green" }, viernes: null, sabado: null, domingo: null },
        { hora: "19:30 - 21:00", lunes: null, martes: { curso: "Machine Learning", seccion: "SEC-01", color: "pink" }, miercoles: null, jueves: null, viernes: { curso: "Seguridad", seccion: "SEC-02", color: "cyan" }, sabado: null, domingo: null },
        { hora: "21:00 - 22:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: { curso: "Electivo", seccion: "SEC-01", color: "yellow" }, domingo: null }
      ]
    },
    { aula: "A204", pabellon: "Pabellón A", capacidad: 35, ocupacion: 83, conflictos: 0, 
      bloques: [
        { hora: "07:30 - 09:00", lunes: { curso: "Programación I", seccion: "SEC-01", color: "green" }, martes: null, miercoles: { curso: "Base de Datos", seccion: "SEC-02", color: "blue" }, jueves: null, viernes: { curso: "IA Clásica", seccion: "SEC-01", color: "pink" }, sabado: { curso: "Redes I", seccion: "SEC-03", color: "cyan" }, domingo: null },
        { hora: "09:00 - 10:30", lunes: null, martes: { curso: "Ingeniería Software", seccion: "SEC-01", color: "yellow" }, miercoles: null, jueves: { curso: "Matemática", seccion: "SEC-02", color: "purple" }, viernes: null, sabado: null, domingo: { curso: "Física", seccion: "SEC-01", color: "green" } },
        { hora: "10:30 - 12:00", lunes: { curso: "Arquitectura", seccion: "SEC-01", color: "blue" }, martes: null, miercoles: { curso: "POO", seccion: "SEC-03", color: "green" }, jueves: null, viernes: { curso: "Estadística", seccion: "SEC-01", color: "yellow" }, sabado: { curso: "Sistemas Operativos", seccion: "SEC-02", color: "yellow" }, domingo: null },
        { hora: "12:00 - 13:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: null, domingo: null },
        { hora: "13:30 - 15:00", lunes: { curso: "Laboratorio IA", seccion: "LAB-01", color: "pink" }, martes: null, miercoles: null, jueves: { curso: "Minería de Datos", seccion: "SEC-01", color: "purple" }, viernes: null, sabado: null, domingo: null },
        { hora: "15:00 - 16:30", lunes: null, martes: { curso: "Algoritmos", seccion: "SEC-04", color: "green" }, miercoles: null, jueves: null, viernes: { curso: "Testing", seccion: "SEC-01", color: "cyan" }, sabado: null, domingo: null },
        { hora: "21:00 - 22:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: { curso: "Electivo", seccion: "SEC-01", color: "yellow" }, domingo: null }
      ]  
    },
    { aula: "LAB301", pabellon: "Laboratorios", capacidad: 30, ocupacion: 96, conflictos: 0, 
      bloques: [
        { hora: "07:30 - 09:00", lunes: { curso: "Programación I", seccion: "SEC-01", color: "green" }, martes: null, miercoles: { curso: "Base de Datos", seccion: "SEC-02", color: "blue" }, jueves: null, viernes: { curso: "IA Clásica", seccion: "SEC-01", color: "pink" }, sabado: { curso: "Redes I", seccion: "SEC-03", color: "cyan" }, domingo: null },
        { hora: "09:00 - 10:30", lunes: null, martes: { curso: "Ingeniería Software", seccion: "SEC-01", color: "yellow" }, miercoles: null, jueves: { curso: "Matemática", seccion: "SEC-02", color: "purple" }, viernes: null, sabado: null, domingo: { curso: "Física", seccion: "SEC-01", color: "green" } },
        { hora: "10:30 - 12:00", lunes: { curso: "Arquitectura", seccion: "SEC-01", color: "blue" }, martes: null, miercoles: { curso: "POO", seccion: "SEC-03", color: "green" }, jueves: null, viernes: { curso: "Estadística", seccion: "SEC-01", color: "yellow" }, sabado: { curso: "Sistemas Operativos", seccion: "SEC-02", color: "yellow" }, domingo: null },
        { hora: "12:00 - 13:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: null, domingo: null },
        { hora: "13:30 - 15:00", lunes: { curso: "Laboratorio IA", seccion: "LAB-01", color: "pink" }, martes: null, miercoles: null, jueves: { curso: "Minería de Datos", seccion: "SEC-01", color: "purple" }, viernes: null, sabado: null, domingo: null },
        { hora: "15:00 - 16:30", lunes: null, martes: { curso: "Algoritmos", seccion: "SEC-04", color: "green" }, miercoles: null, jueves: null, viernes: { curso: "Testing", seccion: "SEC-01", color: "cyan" }, sabado: null, domingo: null },
        { hora: "21:00 - 22:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: { curso: "Electivo", seccion: "SEC-01", color: "yellow" }, domingo: null }
      ]  
    },
    { aula: "B105", pabellon: "Pabellón B", capacidad: 45, ocupacion: 88, conflictos: 0,
      bloques: [
        { hora: "07:30 - 09:00", lunes: { curso: "Programación I", seccion: "SEC-01", color: "green" }, martes: null, miercoles: { curso: "Base de Datos", seccion: "SEC-02", color: "blue" }, jueves: null, viernes: { curso: "IA Clásica", seccion: "SEC-01", color: "pink" }, sabado: { curso: "Redes I", seccion: "SEC-03", color: "cyan" }, domingo: null },
        { hora: "09:00 - 10:30", lunes: null, martes: { curso: "Ingeniería Software", seccion: "SEC-01", color: "yellow" }, miercoles: null, jueves: { curso: "Matemática", seccion: "SEC-02", color: "purple" }, viernes: null, sabado: null, domingo: { curso: "Física", seccion: "SEC-01", color: "green" } },
        { hora: "10:30 - 12:00", lunes: { curso: "Arquitectura", seccion: "SEC-01", color: "blue" }, martes: null, miercoles: { curso: "POO", seccion: "SEC-03", color: "green" }, jueves: null, viernes: { curso: "Estadística", seccion: "SEC-01", color: "yellow" }, sabado: { curso: "Sistemas Operativos", seccion: "SEC-02", color: "yellow" }, domingo: null },
        { hora: "12:00 - 13:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: null, domingo: null },
        { hora: "13:30 - 15:00", lunes: { curso: "Laboratorio IA", seccion: "LAB-01", color: "pink" }, martes: null, miercoles: null, jueves: { curso: "Minería de Datos", seccion: "SEC-01", color: "purple" }, viernes: null, sabado: null, domingo: null },
        { hora: "15:00 - 16:30", lunes: null, martes: { curso: "Algoritmos", seccion: "SEC-04", color: "green" }, miercoles: null, jueves: null, viernes: { curso: "Testing", seccion: "SEC-01", color: "cyan" }, sabado: null, domingo: null },
        { hora: "21:00 - 22:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: { curso: "Electivo", seccion: "SEC-01", color: "yellow" }, domingo: null }
      ]  
    },
    { aula: "C204", pabellon: "Pabellón C", capacidad: 50, ocupacion: 79, conflictos: 0, 
      bloques: [
        { hora: "07:30 - 09:00", lunes: { curso: "Programación I", seccion: "SEC-01", color: "green" }, martes: null, miercoles: { curso: "Base de Datos", seccion: "SEC-02", color: "blue" }, jueves: null, viernes: { curso: "IA Clásica", seccion: "SEC-01", color: "pink" }, sabado: { curso: "Redes I", seccion: "SEC-03", color: "cyan" }, domingo: null },
        { hora: "09:00 - 10:30", lunes: null, martes: { curso: "Ingeniería Software", seccion: "SEC-01", color: "yellow" }, miercoles: null, jueves: { curso: "Matemática", seccion: "SEC-02", color: "purple" }, viernes: null, sabado: null, domingo: { curso: "Física", seccion: "SEC-01", color: "green" } },
        { hora: "10:30 - 12:00", lunes: { curso: "Arquitectura", seccion: "SEC-01", color: "blue" }, martes: null, miercoles: { curso: "POO", seccion: "SEC-03", color: "green" }, jueves: null, viernes: { curso: "Estadística", seccion: "SEC-01", color: "yellow" }, sabado: { curso: "Sistemas Operativos", seccion: "SEC-02", color: "yellow" }, domingo: null },
        { hora: "12:00 - 13:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: null, domingo: null },
        { hora: "13:30 - 15:00", lunes: { curso: "Laboratorio IA", seccion: "LAB-01", color: "pink" }, martes: null, miercoles: null, jueves: { curso: "Minería de Datos", seccion: "SEC-01", color: "purple" }, viernes: null, sabado: null, domingo: null },
        { hora: "15:00 - 16:30", lunes: null, martes: { curso: "Algoritmos", seccion: "SEC-04", color: "green" }, miercoles: null, jueves: null, viernes: { curso: "Testing", seccion: "SEC-01", color: "cyan" }, sabado: null, domingo: null },
        { hora: "21:00 - 22:30", lunes: null, martes: null, miercoles: null, jueves: null, viernes: null, sabado: { curso: "Electivo", seccion: "SEC-01", color: "yellow" }, domingo: null }
      ]
    }
  ];

  const currentAula = previewAulas[previewIndex];

  // Base fija de horarios en caso el aula seleccionada no tenga bloques cargados
  const baseHoras = previewAulas[0].bloques.map(b => b.hora);

  const cambiarAula = (direccion) => {
    if (direccion === 'ant') {
      setPreviewIndex(prev => (prev > 0 ? prev - 1 : previewAulas.length - 1));
    } else {
      setPreviewIndex(prev => (prev < previewAulas.length - 1 ? prev + 1 : 0));
    }
  };

  const calcularHorasPorDia = (dia) => {
    if (!currentAula.bloques || currentAula.bloques.length === 0) return 0;
    return currentAula.bloques.filter(b => b[dia] !== null && b[dia] !== undefined).length * 1.5;
  };

  const diasSemana = [
    { id: 'lunes', label: 'Lunes' },
    { id: 'martes', label: 'Martes' },
    { id: 'miercoles', label: 'Miércoles' },
    { id: 'jueves', label: 'Jueves' },
    { id: 'viernes', label: 'Viernes' },
    { id: 'sabado', label: 'Sábado' },
    { id: 'domingo', label: 'Domingo' }
  ];

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

        <button
          className="btn"
          onClick={() => setShowPreview(true)}
          style={{
            background: "#4F46E5",
            color: "white",
            fontSize: 15,
            padding: "12px 24px",
            border: "none",
            borderRadius: 8,
            cursor: "pointer"
          }}
        >
          📅 Vista previa del horario semanal
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

      {/* Preview modal de horarios por Aula */}
      {showPreview && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.55)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 9999 }}>
          <div style={{ background: "white", width: "96%", maxWidth: 1400, maxHeight: "92vh", overflow: "auto", borderRadius: 16, padding: 25, boxShadow: "0 25px 60px rgba(0,0,0,.3)" }}>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 15 }}>
              <h2>📅 Simulación de Asignación de Horarios</h2>
              <button className="btn" onClick={() => setShowPreview(false)}>Cerrar</button>
            </div>

            {/* Selector e Información del Aula */}
            <div style={{ textAlign: "center", borderTop: "1px solid #e5e7eb", borderBottom: "1px solid #e5e7eb", padding: "15px 0", marginBottom: 20 }}>
              <h3 style={{ fontSize: 22, margin: 0, color: "#111827" }}>🏫 Aula {currentAula.aula} &nbsp;|&nbsp; <span style={{ fontWeight: 400, color: "#6b7280" }}>{currentAula.pabellon}</span></h3>

              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 20, margin: "12px 0" }}>
                <button className="btn" style={{ padding: "6px 16px" }} onClick={() => cambiarAula('ant')}>◀ Aula anterior</button>
                <span style={{ fontWeight: 600, color: "#374151" }}>Aula {previewIndex + 1} de {previewAulas.length}</span>
                <button className="btn" style={{ padding: "6px 16px" }} onClick={() => cambiarAula('sig')}>Aula siguiente ▶</button>
              </div>

              <div style={{ display: "flex", justifyContent: "center", gap: 40, fontSize: 14, color: "#4b5563" }}>
                <span><strong>Capacidad:</strong> {currentAula.capacidad}</span>
                <span><strong>Estado:</strong> <span style={{ color: "#16a34a", fontWeight: 600 }}>Disponible</span></span>
                <span><strong>Ocupación semanal:</strong> {currentAula.ocupacion}%</span>
              </div>
            </div>

            {/* Tabla del Calendario */}
            <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "6px", tableLayout: "fixed" }}>
              <thead>
                <tr>
                  <th style={{ width: 110, textAlign: "center", background: "#ad0000", padding: 8, borderRadius: 6 }}>Hora</th>
                  {diasSemana.map(d => <th key={d.id} style={{ textAlign: "center", background: "#ad0000", padding: 8, borderRadius: 6 }}>{d.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {baseHoras.map((horaLabel, idx) => {
                  const bloqueActual = currentAula.bloques && currentAula.bloques[idx];
                  return (
                    <tr key={idx}>
                      <td style={{ textAlign: "center", fontWeight: "bold", fontSize: 13, color: "#374151", background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 6, padding: "10px 4px" }}>
                        {horaLabel}
                      </td>
                      {diasSemana.map(d => {
                        const celda = bloqueActual ? bloqueActual[d.id] : null;
                        return (
                          <td key={d.id} style={{ border: "1px style dashed #e5e7eb", borderRadius: 8, height: 85, p: 0, verticalAlign: "top" }}>
                            {celda ? (
                              <div style={{ background: scheduleColors[celda.color] || "#E0F2FE", borderRadius: 8, padding: 8, height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", border: "1px solid rgba(0,0,0,0.05)" }}>
                                <div style={{ fontWeight: "bold", fontSize: 12, color: "#111827", lineHeight: "1.2", marginBottom: 3 }}>{celda.curso}</div>
                                <div style={{ fontSize: 11, color: "#374151" }}>{celda.seccion}</div>
                              </div>
                            ) : (
                              <div style={{ height: "100%", background: "#fafafa", borderRadius: 8, border: "1px dashed #f3f4f6" }}></div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Resumen de uso de horas en el pie de página */}
            <div style={{ marginTop: 20, padding: 15, background: "#f9fafb", borderRadius: 10, border: "1px solid #e5e7eb" }}>
              <h4 style={{ margin: "0 0 10px 0", color: "#374151" }}>📊 Uso de Aula por Día:</h4>
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap", fontSize: 14 }}>
                {diasSemana.map(d => (
                  <div key={d.id} style={{ background: "white", padding: "6px 12px", borderRadius: 6, border: "1px solid #e5e7eb" }}>
                    <strong>{d.label}:</strong> {calcularHorasPorDia(d.id).toFixed(1)} horas
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
