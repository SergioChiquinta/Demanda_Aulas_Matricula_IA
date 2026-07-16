// routes/datos.routes.js
const { Router } = require('express');
const { getKpis, getHistorico, getVariables, getEstadoOperativo } = require('../controllers/datos.controller');

const router = Router();
router.get('/kpis',             getKpis);
router.get('/historico',        getHistorico);
router.get('/variables',        getVariables);
router.get('/estado-operativo', getEstadoOperativo);

module.exports = router;
