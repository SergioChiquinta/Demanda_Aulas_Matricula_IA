# Modelo relacional — Demanda Aulas Matrícula IA (v2)

## 1. Contexto

La base de datos original (`demanda_aulas_matricula_ia.sql`) contenía 6 tablas + 1 vista con un
**dataset sintético de 1200 registros** (`Curso_0`...`Curso_49`, aulas sin código estructurado,
docentes sin datos, sin usuarios). Ese dataset es el que calibra los modelos de ML
(Regresión Lineal/Ridge, AG#1 de selección de variables) desde el arranque de `ia_service`.

Para no romper el pipeline de entrenamiento, esas 6 tablas **se conservan intactas**, solo
renombradas con el sufijo `_historico`:

- `cursos` → `cursos_historico`
- `docentes` → `docentes_historico`
- `aulas` → `aulas_historico`
- `horarios` → `horarios_historico`
- `demanda_matricula` → `demanda_matricula_historico`
- `periodos` se mantiene igual (es un catálogo de periodos académico compartido; también
  usan el sistema operativo nuevo).

La vista `vw_dataset_prediccion_aulas` se actualiza para apuntar a las tablas `_historico`,
manteniendo exactamente las mismas columnas de salida. **`ia_service/data_loader.py`,
`ml_model.py`, `ga_variables.py` y `cluster_service.py` no requieren ningún cambio.**

## 2. Esquema operativo nuevo (sistema real)

```
carreras (2 filas: ISI, ISW)
   │ 1
   │
   │ N
malla_cursos ──────── N:1 ──── cursos (78 filas, nombres reales, creditos aleatorios 2-5)
   │ (curso_id, carrera_id, ciclo)
   │
docentes (≈70) ── N:N ── docente_curso ── cursos
   │
   │
usuarios (rol: admin | estudiante)
   │ 1:1 (rol=estudiante)
   ▼
estudiantes (carrera_id, ciclo_actual, codigo_universitario)
   │ N
   │
matriculas ── N:1 ── secciones (horario administrativo persistido)
                          │ N:1 cada uno
                          ├── curso_id     → cursos
                          ├── docente_id   → docentes
                          ├── aula_id      → aulas (288 filas, 4 pabellones × 8 pisos × 9 salones)
                          ├── bloque_id    → bloques_horario (día + franja horaria)
                          └── periodo_id   → periodos
```

### 2.1 `carreras`
| columna | tipo | nota |
|---|---|---|
| id_carrera | INT PK | |
| nombre | VARCHAR(80) UNIQUE | "Ingeniería de Sistemas e Informática", "Ingeniería de Software" |
| codigo | VARCHAR(6) | `ISI`, `ISW` |

### 2.2 `cursos`
78 cursos únicos (Anexo A de la malla). `creditos` se genera aleatorio 2-5 por curso, según
lo pedido explícitamente (se ignoran los créditos reales del PDF).

| columna | tipo | nota |
|---|---|---|
| id_curso | INT PK | |
| nombre_curso | VARCHAR(120) UNIQUE | |
| creditos | TINYINT | 2–5, aleatorio |
| es_laboratorio | TINYINT(1) | heurística por nombre (Laboratorio/Taller) → afecta AG#2/orquestador |

### 2.3 `malla_cursos`
Relaciona un curso con la(s) carrera(s) y ciclo en que se dicta. Un curso "Ambas" genera
2 filas (una por carrera), **sin duplicar el curso** en la tabla `cursos`.

| columna | tipo | nota |
|---|---|---|
| id_malla | INT PK | |
| curso_id | FK → cursos | |
| carrera_id | FK → carreras | |
| ciclo | TINYINT (1-10) | |
| UNIQUE(curso_id, carrera_id) | | |

### 2.4 `aulas`
288 filas generadas por triple bucle pabellón(A-D) × piso(1-8) × salón(1-9).
Código = `{pabellon}{piso}{salon:02d}` (ej. `A101`, `D809`). Aforo **fijo en 40**, sin excepciones.

| columna | tipo | nota |
|---|---|---|
| id_aula | INT PK | |
| codigo_aula | VARCHAR(4) UNIQUE | `A101`...`D809` |
| pabellon | CHAR(1) | A, B, C, D |
| piso | TINYINT | 1-8 |
| numero_salon | TINYINT | 1-9 |
| aforo | SMALLINT DEFAULT 40 | constante, no editable por seed |

### 2.5 `docentes` / `docente_curso`
~70 docentes generados (nombres de prueba). `docente_curso` relaciona qué docentes pueden
dictar qué cursos (usado por el orquestador para no asignar un curso a un docente no
calificado y para calcular `docentes_disponibles` por curso, insumo real de AG#2).

### 2.6 `bloques_horario`
Catálogo de franjas día+hora (mismo patrón que ya usaba el modal estático de `Horarios.jsx`:
lunes a domingo, 10 franjas de 07:30 a 22:30). 7 × 10 = 70 filas.

| columna | tipo |
|---|---|
| id_bloque | INT PK |
| dia_semana | ENUM('Lunes',...,'Domingo') |
| hora_inicio / hora_fin | TIME |
| orden | TINYINT (orden de la franja en el día, para ordenar la grilla) |

### 2.7 `usuarios` / `estudiantes`
| `usuarios` | tipo | nota |
|---|---|---|
| id_usuario | INT PK | |
| nombre | VARCHAR(120) | |
| email | VARCHAR(150) UNIQUE | |
| password_hash | VARCHAR(60) | bcrypt, nunca texto plano |
| rol | ENUM('admin','estudiante') | |

`estudiantes` extiende `usuarios` 1:1 cuando `rol='estudiante'`: `codigo_universitario`,
`carrera_id`, `ciclo_actual`. Los admins no tienen tabla adicional (no tienen datos extra).

### 2.8 `secciones` (horario administrativo persistido)
Resultado **guardado** del pipeline de IA (Regresión → AG#2 → asignación global de
aula/docente/bloque). Es la fuente única de verdad que consume tanto la vista dinámica de
horarios como la comparación del estudiante.

| columna | tipo | nota |
|---|---|---|
| id_seccion | INT PK | |
| periodo_id | FK → periodos | |
| curso_id | FK → cursos | |
| docente_id | FK → docentes | |
| aula_id | FK → aulas | |
| bloque_id | FK → bloques_horario | |
| codigo_seccion | VARCHAR(10) | `S1`, `S2`... por curso |
| aforo | SMALLINT DEFAULT 40 | |
| alumnos_estimados | SMALLINT | salida de AG#2/regresión |
| duracion_semanas | TINYINT DEFAULT 18 | constante |
| UNIQUE(aula_id, bloque_id, periodo_id) | | evita choque de aula |
| UNIQUE(docente_id, bloque_id, periodo_id) | | evita choque de docente |

### 2.9 `matriculas`
Horario personal del estudiante: subconjunto de `secciones` que el estudiante eligió.

| columna | tipo |
|---|---|
| id_matricula | INT PK |
| estudiante_id | FK → estudiantes |
| seccion_id | FK → secciones |
| periodo_id | FK → periodos |
| UNIQUE(estudiante_id, seccion_id) | |

## 3. Decisiones de diseño (criterio propio, documentadas)

- **`demanda_matricula` se mantiene como tabla histórica separada** (`_historico`), no se
  migra al nuevo catálogo: los modelos de regresión ya están calibrados sobre sus variables
  numéricas (no dependen del nombre del curso), así que siguen siendo válidos para estimar
  demanda de los 78 cursos reales sin reentrenar con datos ficticios nuevos.
- **Docentes: 70. Estudiantes: 600** (repartidos entre ambas carreras y los 10 ciclos),
  suficiente para poblar secciones de los 78 cursos en varias franjas sin saturar el seed.
- **JWT** para autenticación (no sesiones): el frontend es una SPA sin server-side rendering,
  JWT evita mantener estado de sesión en el backend y es trivial de validar en cada request
  proxy hacia `ia_service`.
- **Aforo 40 y duración 18 semanas son constantes de esquema** (`DEFAULT`), no se seedean
  valores variables como en el dataset histórico.
