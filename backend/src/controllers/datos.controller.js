// controllers/datos.controller.js
const pool = require('../db/mysql');

const COLUMNAS_HISTORICO = [
  'periodo', 'nombre_curso', 'pabellon', 'horario_seccion',
  'capacidad_aula', 'alumnos_matriculados',
];

/**
 * GET /api/datos/kpis
 * Devuelve los KPIs del Dashboard calculados directamente desde MySQL.
 * MAE y RMSE se obtienen del microservicio ML.
 */
const getKpis = async (req, res) => {
  try {
    const [rows] = await pool.query(`
      SELECT
        SUM(alumnos_matriculados) AS total_matriculas,
        ROUND(AVG(capacidad_aula), 2) AS aforo_promedio,
        COUNT(*) AS total_registros
      FROM vw_dataset_prediccion_aulas
    `);
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * GET /api/datos/historico?limit=100
 */
const getHistorico = async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit) || 100, 1200);
  try {
    const cols = COLUMNAS_HISTORICO.join(', ');
    const [rows] = await pool.query(
      `SELECT ${cols} FROM vw_dataset_prediccion_aulas ORDER BY id_registro LIMIT ?`,
      [limit]
    );
    res.json({ data: rows, total: rows.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * GET /api/datos/variables
 * Lista de variables numéricas para el selector del Análisis.
 */
const getVariables = async (req, res) => {
  const vars = [
    'alumnos_matriculados', 'capacidad_aula', 'carga_academica_proyectada',
    'creditos_curso', 'alumnos_repitentes', 'tiempo_matricula_min',
    'alumnos_nuevos', 'veces_llevado', 'alumnos_prerrequisito',
    'duracion_semanas', 'ciclo_relativo',
  ];
  res.json({ variables: vars });
};

module.exports = { getKpis, getHistorico, getVariables };
