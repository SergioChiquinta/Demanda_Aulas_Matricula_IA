// routes/auth.routes.js
const { Router } = require('express');
const { loginAdmin, loginEstudiante, me } = require('../controllers/auth.controller');
const { verificarToken } = require('../middleware/auth.middleware');

const router = Router();

router.post('/login/admin', loginAdmin);
router.post('/login/estudiante', loginEstudiante);
router.get('/me', verificarToken, me);

module.exports = router;
