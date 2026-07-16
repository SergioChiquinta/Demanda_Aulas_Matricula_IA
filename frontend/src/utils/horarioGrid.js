// src/utils/horarioGrid.js
// Utilidades compartidas para renderizar la grilla de horario
// (administrativo y personal del estudiante) a partir de `secciones`
// reales devueltas por /api/horarios/*.

export const DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'];
export const DIAS_LABEL = { Lunes: 'Lunes', Martes: 'Martes', Miercoles: 'Miércoles', Jueves: 'Jueves', Viernes: 'Viernes', Sabado: 'Sábado', Domingo: 'Domingo' };

const PALETA = [
  '#FDE68A', '#BFDBFE', '#FBCFE8', '#C7D2FE', '#A7F3D0',
  '#FCA5A5', '#FDBA74', '#DDD6FE', '#99F6E4', '#FEF08A',
];

/** Color determinístico (mismo curso -> mismo color siempre) */
export function colorForCurso(nombre) {
  let hash = 0;
  for (let i = 0; i < nombre.length; i++) hash = (hash * 31 + nombre.charCodeAt(i)) >>> 0;
  return PALETA[hash % PALETA.length];
}

/**
 * Agrupa secciones en una matriz [orden][dia] -> array de secciones
 * (más de 1 en la misma celda = choque de horario).
 */
export function construirGrilla(secciones) {
  const ordenes = [...new Set(secciones.map((s) => s.orden))].sort((a, b) => a - b);
  const horaPorOrden = {};
  secciones.forEach((s) => { horaPorOrden[s.orden] = `${s.hora_inicio?.slice(0, 5)} - ${s.hora_fin?.slice(0, 5)}`; });

  const filas = ordenes.map((orden) => {
    const celdas = {};
    DIAS.forEach((dia) => { celdas[dia] = secciones.filter((s) => s.orden === orden && s.dia_semana === dia); });
    return { orden, hora: horaPorOrden[orden], celdas };
  });

  return filas;
}
