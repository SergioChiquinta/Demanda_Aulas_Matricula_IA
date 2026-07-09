// controllers/ga.controller.js
const axios = require('axios');

const ML_URL = process.env.ML_URL || 'http://localhost:8000';

const GA_TIMEOUT = 60_000; // 60 s — los GAs pueden ser lentos

/**
 * POST /api/ga/secciones — AG #2
 * Body: { demanda_plan, capacidad_efectiva, docentes_disponibles }
 */
const gaSecciones = async (req, res) => {
  try {
    const { data } = await axios.post(
      `${ML_URL}/ml/ga/secciones`, req.body, { timeout: GA_TIMEOUT }
    );
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

/**
 * POST /api/ga/horarios — AG #3
 * Body opcional: { secciones, curso_nombre } — salida de AG #2 para modo pipeline.
 */
const gaHorarios = async (req, res) => {
  try {
    const { data } = await axios.post(
      `${ML_URL}/ml/ga/horarios`, req.body || {}, { timeout: GA_TIMEOUT }
    );
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

module.exports = { gaSecciones, gaHorarios };
