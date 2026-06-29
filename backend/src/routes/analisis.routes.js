// routes/analisis.routes.js
const { Router } = require('express');
const { clustering, getVariables } = require('../controllers/analisis.controller');

const router = Router();
router.get('/variables',   getVariables);
router.post('/clustering', clustering);

module.exports = router;
