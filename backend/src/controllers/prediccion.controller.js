// controllers/prediccion.controller.js
const axios = require('axios');

const ML_URL = process.env.ML_URL || 'http://localhost:8000';

/**
 * POST /api/prediccion/simular
 * Body: { alumnos_nuevos, alumnos_prerrequisito, alumnos_repitentes,
 *         capacidad_aula, duracion_semanas, docentes_disponibles, laboratorio, escenario }
 */
const simular = async (req, res) => {
  try {
    const payload = req.body;

    // 1. Predicción IA
    const { data: pred } = await axios.post(`${ML_URL}/ml/predict`, payload);
    const { pred_base, pred_min, pred_max, mae } = pred;

    // 2. Aplicar escenario
    const escenario = payload.escenario || 'Conservador (+MAE)';
    let demanda_plan =
      escenario === 'Optimista (-MAE)'  ? pred_min :
      escenario === 'Base IA'           ? pred_base : pred_max;
    demanda_plan = Math.max(1, demanda_plan);

    // 3. Capacidad y secciones (lógica del .py original)
    const laboratorio      = payload.laboratorio || 0;
    const capacidad        = payload.capacidad_aula || 40;
    const docentes_disp    = payload.docentes_disponibles || 1;
    const factor_lab       = laboratorio === 1 ? 0.85 : 1.0;
    const cap_efectiva     = Math.max(1, Math.floor(capacidad * factor_lab));
    const cap_segura       = Math.max(1, Math.floor(cap_efectiva * 0.90));
    const aulas_recom      = Math.max(1, Math.ceil(demanda_plan / cap_segura));
    const cap_total        = aulas_recom * cap_efectiva;
    const ocupacion        = demanda_plan / cap_total;
    const cupos_libres     = cap_total - demanda_plan;
    const deficit_docentes = Math.max(0, aulas_recom - docentes_disp);

    // 4. Distribución
    const base_sec  = Math.floor(demanda_plan / aulas_recom);
    const resto_sec = demanda_plan % aulas_recom;
    const secciones = Array.from({ length: aulas_recom }, (_, i) => {
      const alumnos = base_sec + (i < resto_sec ? 1 : 0);
      const ocu     = cap_efectiva > 0 ? alumnos / cap_efectiva : 0;
      return { seccion: `S${i + 1}`, alumnos, capacidad: cap_efectiva, ocupacion: ocu };
    });

    res.json({
      pred_base, pred_min, pred_max, mae,
      demanda_plan, escenario,
      capacidad_efectiva: cap_efectiva,
      capacidad_segura:   cap_segura,
      aulas_recomendadas: aulas_recom,
      capacidad_total:    cap_total,
      cupos_libres,
      ocupacion_promedio: ocupacion,
      deficit_docentes,
      secciones,
    });
  } catch (err) {
    const msg = err.response?.data?.detail || err.message;
    res.status(err.response?.status || 500).json({ error: msg });
  }
};

/**
 * GET /api/prediccion/metricas
 */
const getMetricas = async (req, res) => {
  try {
    const { data } = await axios.get(`${ML_URL}/ml/metricas`);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

module.exports = { simular, getMetricas };
