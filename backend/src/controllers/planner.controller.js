// controllers/planner.controller.js
// Motor Inteligente de Planificación — IA Clásica (Espacios de Estados)
//
// Proxy hacia el microservicio FastAPI Python.
// Sigue exactamente el mismo patrón que ga.controller.js para consistencia.
const axios = require('axios');

const ML_URL = process.env.ML_URL || 'http://localhost:8000';

// Timeout generoso: los algoritmos de búsqueda pueden tardar hasta 10s en casos complejos
const PLANNER_TIMEOUT = 30_000;

/**
 * POST /api/planner/bfs
 * Ejecuta BFS sobre el espacio de estados de asignación de aulas.
 * Body: { demanda_predicha, docentes_disponibles, aulas?, horarios? }
 */
const plannerBfs = async (req, res) => {
  try {
    const { data } = await axios.post(
      `${ML_URL}/ml/planner/bfs`,
      req.body,
      { timeout: PLANNER_TIMEOUT }
    );
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

/**
 * POST /api/planner/dfs
 * Ejecuta DFS sobre el espacio de estados de asignación de aulas.
 * Body: { demanda_predicha, docentes_disponibles, aulas?, horarios? }
 */
const plannerDfs = async (req, res) => {
  try {
    const { data } = await axios.post(
      `${ML_URL}/ml/planner/dfs`,
      req.body,
      { timeout: PLANNER_TIMEOUT }
    );
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

/**
 * POST /api/planner/astar
 * Ejecuta A* (f=g+h) sobre el espacio de estados de asignación de aulas.
 * Es el algoritmo recomendado: garantiza camino de menor costo con h admisible.
 * Body: { demanda_predicha, docentes_disponibles, aulas?, horarios? }
 */
const plannerAstar = async (req, res) => {
  try {
    const { data } = await axios.post(
      `${ML_URL}/ml/planner/astar`,
      req.body,
      { timeout: PLANNER_TIMEOUT }
    );
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

module.exports = { plannerBfs, plannerDfs, plannerAstar };
