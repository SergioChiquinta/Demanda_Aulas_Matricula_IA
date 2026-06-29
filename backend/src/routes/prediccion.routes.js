// routes/prediccion.routes.js
const { Router } = require('express');
const { simular, getMetricas } = require('../controllers/prediccion.controller');

const router = Router();
router.get('/metricas', getMetricas);
router.post('/simular', simular);

module.exports = router;
