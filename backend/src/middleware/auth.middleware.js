// middleware/auth.middleware.js
// Autenticación JWT + autorización por rol (admin | estudiante).
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET;

/**
 * Verifica el header Authorization: Bearer <token> y adjunta el payload
 * decodificado (id_usuario, rol, email, nombre) en req.user.
 */
const verificarToken = (req, res, next) => {
  const header = req.headers.authorization || '';
  const [scheme, token] = header.split(' ');

  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({ error: 'Token no provisto' });
  }

  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Token inválido o expirado' });
  }
};

/**
 * Restringe la ruta a uno o más roles. Debe usarse después de verificarToken.
 * Uso: router.get('/x', verificarToken, requiereRol('admin'), controller)
 */
const requiereRol = (...roles) => (req, res, next) => {
  if (!req.user || !roles.includes(req.user.rol)) {
    return res.status(403).json({ error: 'No tienes permisos para acceder a este recurso' });
  }
  next();
};

module.exports = { verificarToken, requiereRol };
