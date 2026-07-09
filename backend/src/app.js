// src/app.js — Express principal
require('dotenv').config();
const express = require('express');
const cors    = require('cors');

const datosRoutes     = require('./routes/datos.routes');
const analisisRoutes  = require('./routes/analisis.routes');
const prediccionRoutes= require('./routes/prediccion.routes');
const gaRoutes        = require('./routes/ga.routes');
// Motor Inteligente de Planificación (nuevo módulo IA Clásica)
const plannerRoutes   = require('./routes/planner.routes');

const app  = express();
const PORT = process.env.PORT || 3001;

// ── Middleware ────────────────────────────────────────────
app.use(cors({
  origin: ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000', 'http://localhost:3001', 'http://localhost:8000', 'http://127.0.0.1:8000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept', 'Cache-Control', 'Range', 'X-Socket-Id'],
  exposedHeaders: ['Content-Disposition', 'Content-Length', 'Content-Range']
}));
app.use(express.json());

// ── Rutas ─────────────────────────────────────────────────
app.use('/api/datos',      datosRoutes);
app.use('/api/analisis',   analisisRoutes);
app.use('/api/prediccion', prediccionRoutes);
app.use('/api/ga',         gaRoutes);
app.use('/api/planner',    plannerRoutes);   // Motor Inteligente de Planificación

// Health check
app.get('/api/health', (_req, res) => res.json({ status: 'ok', port: PORT }));

// 404
app.use((_req, res) => res.status(404).json({ error: 'Ruta no encontrada' }));

// ── Start ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n✅ Backend Node.js corriendo en http://localhost:${PORT}`);
  console.log(`   ML Service esperado en ${process.env.ML_URL || 'http://localhost:8000'}\n`);
});

module.exports = app;
