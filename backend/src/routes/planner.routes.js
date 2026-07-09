// routes/planner.routes.js
// Motor Inteligente de Planificación — Rutas de la API
// Sigue el mismo patrón que ga.routes.js para consistencia arquitectónica.
const { Router } = require('express');
const { plannerBfs, plannerDfs, plannerAstar } = require('../controllers/planner.controller');

const router = Router();

router.post('/bfs',   plannerBfs);
router.post('/dfs',   plannerDfs);
router.post('/astar', plannerAstar);

module.exports = router;
