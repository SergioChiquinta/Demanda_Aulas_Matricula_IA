// controllers/auth.controller.js
// Login separado para Admin y Estudiante + JWT.
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const pool = require('../db/mysql');

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '8h';

const firmarToken = (usuario) =>
  jwt.sign(
    {
      id_usuario: usuario.id_usuario, email: usuario.email, nombre: usuario.nombre, rol: usuario.rol,
      // Solo presente para rol=estudiante (viene del JOIN con `estudiantes` en loginEstudiante).
      id_estudiante: usuario.id_estudiante ?? undefined,
      carrera_id: usuario.carrera_id ?? undefined,
      ciclo_actual: usuario.ciclo_actual ?? undefined,
    },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );

/**
 * POST /api/auth/login/admin
 * Body: { email, password }
 */
const loginAdmin = async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: 'email y password son requeridos' });
  }
  try {
    const [rows] = await pool.query(
      "SELECT * FROM usuarios WHERE email = ? AND rol = 'admin'",
      [email]
    );
    const usuario = rows[0];
    if (!usuario || !(await bcrypt.compare(password, usuario.password_hash))) {
      return res.status(401).json({ error: 'Credenciales inválidas' });
    }
    const token = firmarToken(usuario);
    res.json({
      token,
      usuario: { id_usuario: usuario.id_usuario, nombre: usuario.nombre, email: usuario.email, rol: usuario.rol },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * POST /api/auth/login/estudiante
 * Body: { email, password }
 */
const loginEstudiante = async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: 'email y password son requeridos' });
  }
  try {
    const [rows] = await pool.query(
      `SELECT u.*, e.id_estudiante, e.codigo_universitario, e.ciclo_actual, e.carrera_id, c.nombre AS carrera_nombre
       FROM usuarios u
       JOIN estudiantes e ON e.usuario_id = u.id_usuario
       JOIN carreras c ON c.id_carrera = e.carrera_id
       WHERE u.email = ? AND u.rol = 'estudiante'`,
      [email]
    );
    const usuario = rows[0];
    if (!usuario || !(await bcrypt.compare(password, usuario.password_hash))) {
      return res.status(401).json({ error: 'Credenciales inválidas' });
    }
    const token = firmarToken(usuario);
    res.json({
      token,
      usuario: {
        id_usuario: usuario.id_usuario,
        nombre: usuario.nombre,
        email: usuario.email,
        rol: usuario.rol,
        id_estudiante: usuario.id_estudiante,
        codigo_universitario: usuario.codigo_universitario,
        ciclo_actual: usuario.ciclo_actual,
        carrera_id: usuario.carrera_id,
        carrera_nombre: usuario.carrera_nombre,
      },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

/**
 * GET /api/auth/me — devuelve el payload del token vigente (para rehidratar sesión en el frontend).
 */
const me = (req, res) => {
  res.json({ usuario: req.user });
};

module.exports = { loginAdmin, loginEstudiante, me };
