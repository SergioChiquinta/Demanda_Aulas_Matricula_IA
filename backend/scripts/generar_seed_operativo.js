/**
 * Genera el bloque de datos operativos (carreras, cursos reales, malla_cursos,
 * 288 aulas, docentes, docente_curso, bloques_horario, usuarios/estudiantes,
 * admin semilla) descrito en docs/MODELO_BD.md.
 *
 * Uso: node backend/scripts/generar_seed_operativo.js > seed_operativo.sql
 * El resultado se pega al final de demanda_aulas_matricula_ia.sql
 * (donde ya hay un comentario marcando el punto de inserción).
 */
const bcrypt = require('bcryptjs');

// PRNG determinista para que el seed sea reproducible entre corridas.
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rng = mulberry32(42);
const randInt = (min, max) => Math.floor(rng() * (max - min + 1)) + min;
const pick = (arr) => arr[Math.floor(rng() * arr.length)];
const esc = (s) => String(s).replace(/'/g, "''");

// ── Anexo A: catálogo real de cursos por ciclo/carrera ────────────────────
const AMBAS = ['ISI', 'ISW'];
const CURSOS = [
  // Ciclo 1
  ...['Principios de Algoritmos', 'Introducción a la Vida Universitaria', 'Matemática 1',
    'Comprensión y Redacción de Textos 1', 'Individuo y Medio Ambiente', 'Inglés 1']
    .map(n => ({ nombre: n, ciclo: 1, carreras: AMBAS })),
  // Ciclo 2
  ...['Introducción a las TIC', 'Matemática Discreta', 'Matemática 2',
    'Problemas y Desafíos en el Perú Actual', 'Comprensión y Redacción de Textos 2',
    'Estadística Descriptiva y Probabilidades', 'Inglés 2']
    .map(n => ({ nombre: n, ciclo: 2, carreras: AMBAS })),
  // Ciclo 3
  ...['Taller de Programación', 'Ciudadanía y Reflexión Ética', 'Cálculo 1',
    'Estadística Inferencial', 'Mecánica Clásica', 'Laboratorio de Mecánica Clásica', 'Inglés 3']
    .map(n => ({ nombre: n, ciclo: 3, carreras: AMBAS })),
  // Ciclo 4
  ...['Programación Orientada a Objetos', 'Análisis y Diseño de Algoritmos', 'Cálculo 2',
    'Investigación Académica', 'Base de Datos', 'Fundamentos de Electromagnetismo',
    'Laboratorio de Fundamentos de Electromagnetismo', 'Inglés 4']
    .map(n => ({ nombre: n, ciclo: 4, carreras: AMBAS })),
  // Ciclo 5
  ...['Algoritmos y Estructura de Datos', 'Diseño de Patrones', 'Taller de Programación Web',
    'Redes y Comunicación de Datos 1', 'Sistemas Operativos',
    'Herramientas Informáticas para la Toma de Decisiones', 'Base de Datos 2']
    .map(n => ({ nombre: n, ciclo: 5, carreras: AMBAS })),
  // Ciclo 6
  ...['Análisis y Diseño de Sistemas de Información', 'JavaScript Avanzado',
    'Marcos de Desarrollo Web', 'Hoja de Estilo en Cascada Avanzado', 'Gestión de Proyectos',
    'Administración y Organización de Empresas', 'Curso Integrador 1: Sistemas Software']
    .map(n => ({ nombre: n, ciclo: 6, carreras: AMBAS })),
  // Ciclo 7
  ...['Lenguajes de Programación', 'Desarrollo Web Integrado', 'Herramientas de Desarrollo',
    'Seguridad Informática', 'Diseño de Productos y Servicios']
    .map(n => ({ nombre: n, ciclo: 7, carreras: AMBAS })),
  { nombre: 'Teoría de Sistemas', ciclo: 7, carreras: ['ISI'] },
  { nombre: 'Liderazgo y Gestión de Equipos', ciclo: 7, carreras: ['ISI'] },
  { nombre: 'Teoría en Computación', ciclo: 7, carreras: ['ISW'] },
  { nombre: 'Desarrollo de Software', ciclo: 7, carreras: ['ISW'] },
  // Ciclo 8
  ...['Herramientas para la Comunicación Efectiva', 'Negociación y Narrativa',
    'Innovación y Transformación Digital', 'Inteligencia de Negocios']
    .map(n => ({ nombre: n, ciclo: 8, carreras: AMBAS })),
  { nombre: 'Herramientas de Prototipado', ciclo: 8, carreras: ['ISI'] },
  { nombre: 'Diseño e Implementación de Arquitectura Empresarial', ciclo: 8, carreras: ['ISI'] },
  { nombre: 'Gestión del Servicio TI', ciclo: 8, carreras: ['ISI'] },
  { nombre: 'Desarrollo de Aplicaciones Móviles', ciclo: 8, carreras: ['ISW'] },
  { nombre: 'Calidad de Software', ciclo: 8, carreras: ['ISW'] },
  { nombre: 'Desarrollo Full Stack', ciclo: 8, carreras: ['ISW'] },
  // Ciclo 9
  ...['Formación para la Investigación - Sistemas', 'Interacción Hombre Máquina',
    'Sistemas de Información Empresarial']
    .map(n => ({ nombre: n, ciclo: 9, carreras: AMBAS })),
  { nombre: 'Curso Integrador 2: Sistemas', ciclo: 9, carreras: ['ISI'] },
  { nombre: 'Planeamiento Estratégico de las TICs', ciclo: 9, carreras: ['ISI'] },
  { nombre: 'Gestión del Conocimiento', ciclo: 9, carreras: ['ISI'] },
  { nombre: 'Pruebas de Software', ciclo: 9, carreras: ['ISW'] },
  { nombre: 'Curso Integrador 2: Software', ciclo: 9, carreras: ['ISW'] },
  { nombre: 'Inteligencia Artificial', ciclo: 9, carreras: ['ISW'] },
  // Ciclo 10
  ...['Ética Profesional', 'Formación para la Empleabilidad', 'Servicios Cloud',
    'Ingeniería Económica', 'Herramientas de Desarrollo Profesional - TIC', 'Electivo 1']
    .map(n => ({ nombre: n, ciclo: 10, carreras: AMBAS })),
  { nombre: 'Taller de Investigación - Sistemas', ciclo: 10, carreras: ['ISI'] },
  { nombre: 'Taller de Investigación - Software', ciclo: 10, carreras: ['ISW'] },
];

const out = [];
const push = (s) => out.push(s);

// ── carreras ────────────────────────────────────────────────────────────
push('-- carreras');
push(`INSERT INTO carreras (nombre, codigo) VALUES
('Ingeniería de Sistemas e Informática', 'ISI'),
('Ingeniería de Software', 'ISW');`);

// ── cursos + malla_cursos ──────────────────────────────────────────────
push('\n-- cursos (78, créditos aleatorios 2-5)');
const cursoValues = CURSOS.map(c => {
  const creditos = randInt(2, 5);
  const esLab = /Laboratorio|Taller/.test(c.nombre) ? 1 : 0;
  c._creditos = creditos;
  c._esLab = esLab;
  return `('${esc(c.nombre)}', ${creditos}, ${esLab})`;
});
push(`INSERT INTO cursos (nombre_curso, creditos, es_laboratorio) VALUES\n${cursoValues.join(',\n')};`);

push('\n-- malla_cursos (relaciona curso -> carrera(s) -> ciclo, vía subconsulta por nombre)');
const mallaValues = [];
CURSOS.forEach(c => {
  c.carreras.forEach(carreraCodigo => {
    mallaValues.push(
      `((SELECT id_curso FROM cursos WHERE nombre_curso = '${esc(c.nombre)}'), ` +
      `(SELECT id_carrera FROM carreras WHERE codigo = '${carreraCodigo}'), ${c.ciclo})`
    );
  });
});
push(`INSERT INTO malla_cursos (curso_id, carrera_id, ciclo) VALUES\n${mallaValues.join(',\n')};`);

// ── aulas: 4 pabellones x 8 pisos x 9 salones = 288 ─────────────────────
push('\n-- aulas (288 = 4 pabellones x 8 pisos x 9 salones, aforo fijo 40)');
const aulaValues = [];
for (const pabellon of ['A', 'B', 'C', 'D']) {
  for (let piso = 1; piso <= 8; piso++) {
    for (let salon = 1; salon <= 9; salon++) {
      const codigo = `${pabellon}${piso}${String(salon).padStart(2, '0')}`;
      aulaValues.push(`('${codigo}', '${pabellon}', ${piso}, ${salon}, 40)`);
    }
  }
}
push(`INSERT INTO aulas (codigo_aula, pabellon, piso, numero_salon, aforo) VALUES\n${aulaValues.join(',\n')};`);

// ── docentes: 70 ──────────────────────────────────────────────────────
push('\n-- docentes (70)');
const NOMBRES = ['Carlos', 'María', 'José', 'Ana', 'Luis', 'Rosa', 'Jorge', 'Carmen', 'Miguel', 'Patricia',
  'Fernando', 'Lucía', 'Ricardo', 'Elena', 'Manuel', 'Sofía', 'Andrés', 'Claudia', 'Diego', 'Verónica',
  'Raúl', 'Gabriela', 'Alberto', 'Silvia', 'Enrique', 'Mónica', 'Pedro', 'Karen', 'Víctor', 'Daniela'];
const APELLIDOS = ['García', 'Rodríguez', 'Pérez', 'Gómez', 'Martínez', 'López', 'Sánchez', 'Fernández',
  'Torres', 'Flores', 'Vásquez', 'Ramírez', 'Chávez', 'Rojas', 'Mendoza', 'Castillo', 'Ortiz', 'Reyes',
  'Guerrero', 'Cruz', 'Salazar', 'Vargas', 'Herrera', 'Medina', 'Aguilar'];
const N_DOCENTES = 70;
const docenteValues = [];
for (let i = 1; i <= N_DOCENTES; i++) {
  const nombre = `${pick(NOMBRES)} ${pick(APELLIDOS)} ${pick(APELLIDOS)}`;
  const email = `docente${String(i).padStart(3, '0')}@utp.edu.pe`;
  docenteValues.push(`('${esc(nombre)}', '${email}')`);
}
push(`INSERT INTO docentes (nombre_docente, email) VALUES\n${docenteValues.join(',\n')};`);

// ── docente_curso: cada curso con 3-6 docentes habilitados ──────────────
push('\n-- docente_curso (3-6 docentes habilitados por curso)');
const dcValues = [];
CURSOS.forEach(c => {
  const n = randInt(3, 6);
  const docentesElegidos = new Set();
  while (docentesElegidos.size < n) docentesElegidos.add(randInt(1, N_DOCENTES));
  docentesElegidos.forEach(dId => {
    dcValues.push(`(${dId}, (SELECT id_curso FROM cursos WHERE nombre_curso = '${esc(c.nombre)}'))`);
  });
});
push(`INSERT INTO docente_curso (docente_id, curso_id) VALUES\n${dcValues.join(',\n')};`);

// ── bloques_horario: 7 días x 10 franjas de 1.5h (07:30-22:30) ─────────
push('\n-- bloques_horario (7 días x 10 franjas, igual patrón que el mock anterior de Horarios.jsx)');
const DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'];
const FRANJAS = [
  ['07:30', '09:00'], ['09:00', '10:30'], ['10:30', '12:00'], ['12:00', '13:30'],
  ['13:30', '15:00'], ['15:00', '16:30'], ['16:30', '18:00'], ['18:00', '19:30'],
  ['19:30', '21:00'], ['21:00', '22:30'],
];
const bloqueValues = [];
DIAS.forEach(dia => {
  FRANJAS.forEach(([ini, fin], idx) => {
    bloqueValues.push(`('${dia}', '${ini}:00', '${fin}:00', ${idx + 1})`);
  });
});
push(`INSERT INTO bloques_horario (dia_semana, hora_inicio, hora_fin, orden) VALUES\n${bloqueValues.join(',\n')};`);

// ── usuarios + estudiantes ───────────────────────────────────────────
push('\n-- admin semilla (Sergio) + 600 estudiantes de prueba');
const ADMIN_HASH = bcrypt.hashSync('sergio123*', 10);
const STUDENT_HASH = bcrypt.hashSync('estudiante123*', 10);

const usuarioValues = [];
const estudianteValues = [];
usuarioValues.push(`('Sergio', 'u22201712@utp.edu.pe', '${ADMIN_HASH}', 'admin')`);

const N_ESTUDIANTES_POR_BUCKET = 30; // 2 carreras x 10 ciclos x 30 = 600
let codigoSeq = 20250001;
['ISI', 'ISW'].forEach(carreraCodigo => {
  for (let ciclo = 1; ciclo <= 10; ciclo++) {
    for (let i = 0; i < N_ESTUDIANTES_POR_BUCKET; i++) {
      const nombre = `${pick(NOMBRES)} ${pick(APELLIDOS)}`;
      const codigo = `U${codigoSeq++}`;
      const email = `${codigo.toLowerCase()}@utp.edu.pe`;
      usuarioValues.push(`('${esc(nombre)}', '${email}', '${STUDENT_HASH}', 'estudiante')`);
      estudianteValues.push(
        `((SELECT id_usuario FROM usuarios WHERE email = '${email}'), '${codigo}', ` +
        `(SELECT id_carrera FROM carreras WHERE codigo = '${carreraCodigo}'), ${ciclo})`
      );
    }
  }
});
push(`INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES\n${usuarioValues.join(',\n')};`);
push(`INSERT INTO estudiantes (usuario_id, codigo_universitario, carrera_id, ciclo_actual) VALUES\n${estudianteValues.join(',\n')};`);

console.log(out.join('\n'));
console.error(`-- OK: ${CURSOS.length} cursos, ${aulaValues.length} aulas, ${N_DOCENTES} docentes, ${estudianteValues.length} estudiantes generados.`);
console.error(`-- Admin: u22201712@utp.edu.pe / sergio123*`);
console.error(`-- Estudiante demo ISI: u20250001@utp.edu.pe / estudiante123*`);
console.error(`-- Estudiante demo ISW: u20250301@utp.edu.pe / estudiante123*`);
