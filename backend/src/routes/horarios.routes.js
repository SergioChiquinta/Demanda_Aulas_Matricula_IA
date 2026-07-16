// routes/horarios.routes.js
const { Router } = require('express');
const {
  getPeriodoActivo,
  getHorarioAdministrativo,
  generarHorarioAdministrativo,
  getHorarioEstudiante,
  matricularEstudiante,
  desmatricularEstudiante,
} = require('../controllers/horarios.controller');
const { verificarToken, requiereRol } = require('../middleware/auth.middleware');

const router = Router();

router.use(verificarToken);

router.get('/periodo-activo', getPeriodoActivo);
router.get('/administrativo', getHorarioAdministrativo);
router.post('/generar-administrativo', requiereRol('admin'), generarHorarioAdministrativo);

router.get('/estudiante', requiereRol('estudiante'), getHorarioEstudiante);
router.post('/estudiante/matricular', requiereRol('estudiante'), matricularEstudiante);
router.delete('/estudiante/matricula/:id', requiereRol('estudiante'), desmatricularEstudiante);

module.exports = router;
