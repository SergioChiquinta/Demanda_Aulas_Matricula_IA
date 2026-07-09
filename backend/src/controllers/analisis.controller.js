// controllers/analisis.controller.js
const axios = require('axios');

const ML_URL = process.env.ML_URL || 'http://localhost:8000';

/**
 * POST /api/analisis/clustering
 * Body: { var_x: string, var_y: string }
 */
const clustering = async (req, res) => {
  try {
    const { var_x, var_y } = req.body;
    if (!var_x || !var_y) {
      return res.status(400).json({ error: 'Se requieren var_x y var_y' });
    }
    const { data } = await axios.post(`${ML_URL}/ml/cluster`, { var_x, var_y });
    res.json(data);
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

/**
 * GET /api/analisis/variables
 */
const getVariables = async (req, res) => {
  try {
    const { data } = await axios.get(`${ML_URL}/ml/variables`);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

module.exports = { clustering, getVariables };
