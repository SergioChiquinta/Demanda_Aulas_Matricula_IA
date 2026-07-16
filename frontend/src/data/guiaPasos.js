// src/data/guiaPasos.js
// Contenido de la Guía de inicio rápido, por rol.

export const PASOS_ADMIN = [
  {
    icono: '👋',
    titulo: '¡Bienvenido, Administrador!',
    texto: 'Desde acá gestionas la demanda de aulas y generas el horario oficial de la UTP Campus Lima Sur usando IA.',
  },
  {
    icono: '🤖',
    titulo: 'Paso 1 — Predicción IA',
    texto: 'Ajusta los parámetros del escenario (alumnos, docentes, capacidad) y presiona "EJECUTAR IA" para obtener la demanda estimada.',
  },
  {
    icono: '🧠',
    titulo: 'Paso 2 — Planificador IA',
    texto: 'Ejecuta el algoritmo "A*" y ejecútalo. Revisa la planificación: es tu "visto bueno" antes de publicar el horario.',
  },
  {
    icono: '🗓️',
    titulo: 'Paso 3 — Horarios',
    texto: 'Presiona "Generar Horario Administrativo (IA)" para publicar el horario real. Luego puedes exportarlo a PDF.',
  },
  {
    icono: '✅',
    titulo: '¡Listo!',
    texto: 'Los estudiantes ya pueden ver y matricularse en el horario que generaste. Puedes volver a esta guía cuando quieras desde este botón.',
  },
];

export const PASOS_ESTUDIANTE = [
  {
    icono: '👋',
    titulo: '¡Bienvenido!',
    texto: 'Desde "Mi Horario" puedes ver la oferta de cursos de tu carrera y ciclo, y armar tu horario personal.',
  },
  {
    icono: '📋',
    titulo: 'Horario disponible',
    texto: 'Es la vista por defecto: muestra todas las secciones ofrecidas para tu carrera y ciclo (solo de referencia, sin exportar).',
  },
  {
    icono: '✅',
    titulo: 'Matricúlate',
    texto: 'Presiona "Matricularme" en la sección que quieras. Si dice "Ya matriculado" o "En cruce", repites curso o chocas de horario.',
  },
  {
    icono: '🗓️',
    titulo: 'Solo mi horario',
    texto: 'Cambia a esta vista para ver únicamente tus secciones elegidas, con los choques resaltados en rojo.',
  },
  {
    icono: '📄',
    titulo: 'Exporta tu horario',
    texto: 'Desde "Solo mi horario" presiona "Exportar a PDF" para descargar tu horario personal.',
  },
];
