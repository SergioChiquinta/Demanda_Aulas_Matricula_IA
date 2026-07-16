// controllers/horarios.controller.js
// Horario administrativo (persistido en `secciones`) y horario personal del estudiante.
const axios = require('axios');
const pool = require('../db/mysql');

const ML_URL = process.env.ML_URL || 'http://localhost:8000';
const GENERAR_TIMEOUT = 120_000; // el pipeline completo (78 cursos) puede tardar

const SELECT_SECCION = `
  SELECT
    s.id_seccion, s.codigo_seccion, s.aforo, s.alumnos_estimados, s.duracion_semanas,
    c.id_curso, c.nombre_curso, c.creditos, c.es_laboratorio,
    d.id_docente, d.nombre_docente,
    a.id_aula, a.codigo_aula, a.pabellon, a.piso, a.numero_salon,
    b.id_bloque, b.dia_semana, b.hora_inicio, b.hora_fin, b.orden,
    p.id_periodo, p.codigo_periodo
  FROM secciones s
  JOIN cursos c            ON c.id_curso = s.curso_id
  JOIN docentes d          ON d.id_docente = s.docente_id
  JOIN aulas a             ON a.id_aula = s.aula_id
  JOIN bloques_horario b   ON b.id_bloque = s.bloque_id
  JOIN periodos p          ON p.id_periodo = s.periodo_id
`;

const getPeriodoActivoId = async () => {
  const [rows] = await pool.query('SELECT id_periodo, codigo_periodo FROM periodos WHERE activo = 1 LIMIT 1');
  return rows[0];
};

/**
 * GET /api/horarios/periodo-activo
 */
const getPeriodoActivo = async (_req, res) => {
  try {
    const periodo = await getPeriodoActivoId();
    if (!periodo) return res.status(404).json({ error: 'No hay periodo activo configurado' });
    res.json(periodo);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * GET /api/horarios/administrativo?periodo_id=&carrera_id=&ciclo=
 * Accesible por admin y estudiante (solo lectura para estudiante).
 */
const getHorarioAdministrativo = async (req, res) => {
  try {
    let periodoId = req.query.periodo_id;
    if (!periodoId) {
      const activo = await getPeriodoActivoId();
      if (!activo) return res.json({ periodo: null, secciones: [] });
      periodoId = activo.id_periodo;
    }

    const { carrera_id, ciclo } = req.query;
    let sql = SELECT_SECCION;
    const params = [periodoId];

    if (carrera_id || ciclo) {
      sql += ' JOIN malla_cursos mc ON mc.curso_id = c.id_curso ';
      sql += ' WHERE s.periodo_id = ? ';
      if (carrera_id) { sql += ' AND mc.carrera_id = ? '; params.push(carrera_id); }
      if (ciclo)      { sql += ' AND mc.ciclo = ? ';      params.push(ciclo); }
    } else {
      sql += ' WHERE s.periodo_id = ? ';
    }
    sql += ' ORDER BY a.codigo_aula, b.orden, FIELD(b.dia_semana,"Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo") ';

    const [rows] = await pool.query(sql, params);
    res.json({ periodo_id: Number(periodoId), total: rows.length, secciones: rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * POST /api/horarios/generar-administrativo
 * Body: { periodo_id? }  — admin only.
 * Dispara el pipeline completo (Regresión -> AG#2 -> asignación global) en
 * ia_service y persiste el resultado en `secciones`, reemplazando lo anterior
 * para ese periodo.
 */
const generarHorarioAdministrativo = async (req, res) => {
  try {
    let periodoId = req.body.periodo_id;
    if (!periodoId) {
      const activo = await getPeriodoActivoId();
      if (!activo) return res.status(400).json({ error: 'No hay periodo activo configurado' });
      periodoId = activo.id_periodo;
    }

    const { data } = await axios.post(
      `${ML_URL}/ml/horario-administrativo/generar`,
      { periodo_id: periodoId },
      { timeout: GENERAR_TIMEOUT }
    );
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

/**
 * GET /api/horarios/estudiante — horario personal del estudiante autenticado,
 * más un arreglo `conflictos` con los id_bloque que se repiten (choque de horario).
 */
const getHorarioEstudiante = async (req, res) => {
  try {
    const idEstudiante = req.user.id_estudiante;
    const selectConMatricula = SELECT_SECCION
      .replace('SELECT\n', 'SELECT\n    m.id_matricula,')
      .replace('FROM secciones s', 'FROM matriculas m JOIN secciones s ON s.id_seccion = m.seccion_id');
    const [rows] = await pool.query(
      `${selectConMatricula}
       WHERE m.estudiante_id = ?
       ORDER BY a.codigo_aula, b.orden`,
      [idEstudiante]
    );

    const conteoBloque = {};
    rows.forEach((r) => { conteoBloque[r.id_bloque] = (conteoBloque[r.id_bloque] || 0) + 1; });
    const conflictos = Object.entries(conteoBloque).filter(([, n]) => n > 1).map(([id]) => Number(id));

    res.json({ total: rows.length, secciones: rows, conflictos });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * POST /api/horarios/estudiante/matricular
 * Body: { seccion_id }
 */
const matricularEstudiante = async (req, res) => {
  try {
    const idEstudiante = req.user.id_estudiante;
    const { seccion_id } = req.body;
    if (!seccion_id) return res.status(400).json({ error: 'seccion_id es requerido' });

    const [secRows] = await pool.query('SELECT periodo_id FROM secciones WHERE id_seccion = ?', [seccion_id]);
    if (!secRows[0]) return res.status(404).json({ error: 'Sección no encontrada' });

    await pool.query(
      'INSERT INTO matriculas (estudiante_id, seccion_id, periodo_id) VALUES (?, ?, ?)',
      [idEstudiante, seccion_id, secRows[0].periodo_id]
    );
    res.status(201).json({ ok: true });
  } catch (err) {
    if (err.code === 'ER_DUP_ENTRY') {
      return res.status(409).json({ error: 'Ya estás matriculado en esa sección' });
    }
    res.status(500).json({ error: err.message });
  }
};

/**
 * DELETE /api/horarios/estudiante/matricula/:id
 */
const desmatricularEstudiante = async (req, res) => {
  try {
    const idEstudiante = req.user.id_estudiante;
    const { id } = req.params;
    const [result] = await pool.query(
      'DELETE FROM matriculas WHERE id_matricula = ? AND estudiante_id = ?',
      [id, idEstudiante]
    );
    if (result.affectedRows === 0) return res.status(404).json({ error: 'Matrícula no encontrada' });
    res.json({ ok: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

module.exports = {
  getPeriodoActivo,
  getHorarioAdministrativo,
  generarHorarioAdministrativo,
  getHorarioEstudiante,
  matricularEstudiante,
  desmatricularEstudiante,
};
