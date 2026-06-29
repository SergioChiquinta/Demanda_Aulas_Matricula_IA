// routes/ga.routes.js
const { Router } = require('express');
const { getCandidatas, gaVariables, gaSecciones, gaHorarios } = require('../controllers/ga.controller');

const router = Router();
router.get('/candidatas', getCandidatas);
router.post('/variables', gaVariables);
router.post('/secciones', gaSecciones);
router.post('/horarios',  gaHorarios);

module.exports = router;
