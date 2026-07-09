// routes/ga.routes.js
const { Router } = require('express');
const { gaSecciones, gaHorarios } = require('../controllers/ga.controller');

const router = Router();
router.post('/secciones', gaSecciones);
router.post('/horarios',  gaHorarios);

module.exports = router;
