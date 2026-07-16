# Demanda Aulas Matrícula IA — Guía de Instalación y Arranque

Sistema web completo para predicción de demanda de aulas académicas con Algoritmos Genéticos.  
Stack: **React + Vite** (frontend) · **Node.js + Express** (backend) · **Python + FastAPI** (IA) · **MySQL** (base de datos)

---

## Requisitos previos

| Herramienta | Versión mínima |        Verificar       |
|-------------|----------------|------------------------|
|    Python   |     3.10+      |  `python --version`    |
|   Node.js   |      18+       |      `node -v`         |
|     npm     |       9+       |       `npm -v`         |
|XAMPP (MySQL)|   cualquiera   | Apache + MySQL activos |

---

## Estructura del proyecto

```
Demanda_Aulas_Matricula_IA/
├── demanda_aulas_matrícula_IA.py   ← App original Tkinter (intacta)
├── demanda_aulas_matricula_ia.sql  ← Script SQL único (dataset histórico + esquema operativo)
├── README.md                       ← (este archivo, original)
├── SETUP.md                        ← Esta guía
├── docs/
│   └── MODELO_BD.md                ← Modelo entidad-relación completo (v2)
│
├── ia_service/                     ← Microservicio Python (FastAPI)
│   ├── main.py
│   ├── data_loader.py
│   ├── ml_model.py
│   ├── cluster_service.py
│   ├── ga_variables.py
│   ├── ga_secciones.py
│   ├── ga_horarios.py
│   ├── orquestador_horario.py      ← Pipeline que genera y persiste el horario administrativo
│   ├── planner/
│   ├── requirements.txt
│   └── .env
│
├── backend/                        ← API REST (Node.js + Express)
│   ├── src/
│   │   ├── app.js
│   │   ├── db/mysql.js
│   │   ├── middleware/auth.middleware.js  ← JWT + roles
│   │   ├── routes/                 ← incluye auth.routes.js, horarios.routes.js
│   │   └── controllers/            ← incluye auth.controller.js, horarios.controller.js
│   ├── scripts/generar_seed_operativo.js  ← Generador del seed (carreras/cursos/aulas/docentes/usuarios)
│   ├── package.json
│   └── .env
│
└── frontend/                       ← Interfaz Web (React + Vite)
    ├── src/
    │   ├── App.jsx
    │   ├── api/client.js           ← inyecta el JWT en cada request
    │   ├── context/AuthContext.jsx
    │   ├── components/             ← incluye ProtectedRoute.jsx, HorarioGrid.jsx
    │   ├── utils/                  ← horarioGrid.js, exportPdf.js
    │   └── pages/                  ← incluye Login.jsx, MiHorario.jsx
    └── package.json
```

---

## Paso 1 — Base de datos (XAMPP)

1. Abre **XAMPP Control Panel**
2. Inicia **Apache** y **MySQL**
3. Ve a `http://localhost/phpmyadmin`
4. Pestaña **Importar** → selecciona `demanda_aulas_matricula_ia.sql`
5. Ejecuta la importación → al final debe mostrar dos validaciones:
   - `total_registros = 1200` (dataset histórico, usado solo para entrenar los modelos de ML)
   - `total_cursos = 78`, `total_aulas = 288`, `total_docentes = 70`, `total_estudiantes = 600` (catálogo real operativo)

> ⚠️ La base de datos debe estar activa antes de arrancar cualquier servicio.
> El archivo es único (compatible con importación directa vía phpMyAdmin) y ya incluye tanto el
> dataset histórico como el esquema operativo nuevo (carreras, cursos reales, aulas, docentes,
> usuarios, secciones). El detalle del modelo entidad-relación está en [`docs/MODELO_BD.md`](docs/MODELO_BD.md).

---

## Paso 2 — Microservicio IA (Python + FastAPI)

### 2.1 Configurar credenciales

Crea y edita el archivo `ia_service/.env`:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=          ← tu contraseña de MySQL (vacío si no tienes)
DB_NAME=demanda_aulas_matricula_ia
```

### 2.2 Instalar dependencias

```bash
cd ia_service
pip install -r requirements.txt
```

Paquetes que se instalan:

|          Paquete         |                Uso              |
|--------------------------|---------------------------------|
|         `fastapi`        |       Framework API REST        |
|    `uvicorn[standard]`   |          Servidor ASGI          |
|         `pydantic`       |        Validación de datos      |
| `mysql-connector-python` |         Conexión a MySQL        |
|          `pandas`        |     Manejo de datos (DataFrame) |
|          `numpy`         |       Operaciones numéricas     |
|      `scikit-learn`      | KMeans, Ridge, LinearRegression |
|      `python-dotenv`     |    Leer variables de entorno    |

### 2.3 Arrancar el servicio

```bash
cd ia_service
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Salida esperada:**
```
INFO: Cargando datos desde MySQL...
INFO: Dataset cargado: 1200 registros.
INFO: Modelos entrenados y listos.
INFO: Uvicorn running on http://0.0.0.0:8000
```

> Documentación interactiva disponible en `http://localhost:8000/docs`

---

## Paso 3 — Backend API (Node.js + Express)

### 3.1 Configurar variables de entorno

Edita el archivo `backend/.env`:

```env
PORT=3001
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=          ← tu contraseña de MySQL
DB_NAME=demanda_aulas_matricula_ia
ML_URL=http://localhost:8000
JWT_SECRET=demanda_aulas_ia_dev_secret_cambiar_en_produccion
JWT_EXPIRES_IN=8h
```

### 3.2 Instalar dependencias

```bash
cd backend
npm install
```

Paquetes que se instalan:

|    Paquete      |                 Uso                   |
|-----------------|---------------------------------------|
| `express`       |             Framework web             |
| `mysql2`        |        Pool de conexiones MySQL       |
| `axios`         | Llamadas HTTP al microservicio Python |
| `cors`          |    Habilitar CORS para el frontend    |
| `dotenv`        |       Leer variables de entorno       |
| `bcryptjs`       | Hash de contraseñas (login admin/estudiante) |
| `jsonwebtoken`  |          Autenticación JWT            |
| `nodemon`       |    Recarga automática en desarrollo   |

### 3.3 Arrancar el servidor

```bash
cd backend
npm run dev
```

**Salida esperada:**
```
✅ Backend Node.js corriendo en http://localhost:3001
   ML Service esperado en http://localhost:8000
```

---

## Paso 4 — Frontend (React + Vite)

### 4.1 Instalar dependencias

```bash
cd frontend
npm install
```

Paquetes principales:

|        Paquete        |                     Uso                     |
|-----------------------|---------------------------------------------|
| `react` + `react-dom` |                 Framework UI                |
|  `react-router-dom`   |          Navegación entre páginas           |
|       `recharts`      |     Gráficos (scatter, barras, líneas)      |
|        `axios`        |            Llamadas HTTP al backend         |
|        `jspdf`        |          Generación de PDF (horarios)       |
|     `html2canvas`     | Captura de la grilla de horario para el PDF |
|        `vite`         |        Bundler y servidor de desarrollo     |

### 4.2 Arrancar el servidor de desarrollo

```bash
cd frontend
npm run dev
```

**Salida esperada:**
```
VITE v8.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

Abre `http://localhost:5173` en tu navegador. Te recibirá la pantalla de **login** (hay dos pestañas:
Administrativo / Estudiante — ver credenciales de prueba más abajo).

---

## Paso 5 — Generar el horario administrativo (primer uso)

La base de datos trae el catálogo (cursos, aulas, docentes, estudiantes) pero **no** trae secciones
generadas de fábrica. Después del primer login como admin:

1. Entra a **Horarios** → sección "Horario Administrativo"
2. Click en **"🚀 Generar Horario Administrativo (IA)"**
3. Esto ejecuta el pipeline completo (Regresión → AG#2 → asignación global de aula/docente/bloque)
   sobre los 78 cursos reales y persiste el resultado (tarda 1-3 segundos)
4. A partir de ahí, tanto la vista administrativa como "Mi Horario" (estudiante) muestran datos reales

---

## Credenciales de prueba

|                       Rol                         |          Email         |    Contraseña    |
|---------------------------------------------------|------------------------|------------------|
|             Administrativo (Sergio)               | `u22201712@utp.edu.pe` |   `sergio123*`   |
| Estudiante — Ing. Sistemas e Informática, ciclo 1 | `u20250001@utp.edu.pe` | `estudiante123*` |
|      Estudiante — Ing. de Software, ciclo 1       | `u20250301@utp.edu.pe` | `estudiante123*` |

Los 600 estudiantes semilla siguen el patrón `u2025####@utp.edu.pe` (correlativo `20250001`–`20250600`,
los primeros 300 son de Ingeniería de Sistemas e Informática y los siguientes 300 de Ingeniería de
Software, 30 por ciclo) y todos comparten la contraseña `estudiante123*`. El detalle de cómo se generan
está en `backend/scripts/generar_seed_operativo.js`.

---

## Orden de arranque (importante)

> Siempre seguir este orden. Necesitas **3 terminales** abiertas simultáneamente.

```
┌─────────────────────────────────────────┐
│  1. XAMPP → MySQL activo                │
│  2. Terminal 1 → ia_service (Python)    │
│  3. Terminal 2 → backend (Node.js)      │
│  4. Terminal 3 → frontend (React)       │
└─────────────────────────────────────────┘
```

### Resumen rápido (copiar y pegar)

**Terminal 1:**
```bash
cd ia_service
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2:**
```bash
cd backend
npm run dev
```

**Terminal 3:**
```bash
cd frontend
npm run dev
```

---

## Puertos y URLs

|     Servicio      |             URL              |        Descripción        |
|-------------------|------------------------------|---------------------------|
| React (Frontend)  |   `http://localhost:5173`    |   Interfaz web principal  |
| Node.js (Backend) |   `http://localhost:3001`    |          API REST         |
|    FastAPI (IA)   |   `http://localhost:8000`    | Microservicio de IA y GAs |
|    FastAPI Docs   | `http://localhost:8000/docs` |   Swagger UI interactivo  |
|        MySQL      |      `localhost:3306`        |        Base de datos      |

---

## Módulos disponibles en la interfaz

### Rol Administrativo

|       Módulo       |       Ruta      |                                     Descripción                                       |
|--------------------|-----------------|---------------------------------------------------------------------------------------|
|      Dashboard     |       `/`       |                        KPIs históricos + tabla de matrículas                          |
| Análisis de Aforos |  `/analisis`    |                         Clustering K-Means K=3 con gráficos                           |
|    Predicción IA   | `/prediccion`   |                        Predicción con Regresión Lineal/Ridge                          |
|     Secciones      |  `/secciones`   |                    AG#2 — Optimización de distribución de aulas                       |
|     Horarios       |   `/horarios`   | AG#3 standalone/pipeline + **Horario Administrativo real** (generar/ver/exportar PDF) |
|  Planificador IA   | `/planificador` |         Motor de espacios de estados (BFS/DFS/A*) sobre las 288 aulas reales          |

### Rol Estudiante

|   Módulo   |      Ruta     |                                                            Descripción                                                           |
|------------|---------------|----------------------------------------------------------------------------------------------------------------------------------|
| Mi Horario | `/mi-horario` | Ver horario administrativo de su carrera/ciclo, matricularse/desmatricularse, comparación con resaltado de choques, exportar PDF |

El estudiante **no** tiene acceso a Dashboard/Análisis/Predicción/Secciones/Planificador (son
herramientas administrativas de calibración de IA); intentar acceder por URL lo redirige a `/mi-horario`.

---

## Solución de problemas

### ❌ Error de conexión a MySQL

```
No se pudo cargar el dataset desde MySQL
```

- Verifica que XAMPP tenga MySQL activo (indicador verde)
- Revisa que la contraseña en `ia_service/.env` y `backend/.env` sea correcta
- Confirma que la BD `demanda_aulas_matricula_ia` existe en phpMyAdmin

### ❌ FastAPI no arranca (`uvicorn` no encontrado)

```bash
# Opción 1: agregar al PATH
python -m uvicorn main:app --port 8000

# Opción 2: instalar en el Python del sistema
pip install uvicorn --user
```

### ❌ Frontend no carga datos (pantalla en blanco o spinner infinito)

- Asegúrate de que el **backend Node.js** esté corriendo en el puerto 3001
- Asegúrate de que el **microservicio Python** esté corriendo en el puerto 8000
- Revisa la consola del navegador (F12) para ver el error exacto

### ❌ Los GAs tardan mucho

Es normal. Tiempos aproximados:
- AG-1 Variables: ~5–15 segundos
- AG-2 Secciones: ~3–8 segundos
- AG-3 Horarios: ~10–30 segundos

---

## Decisiones de diseño (criterio propio)

Resumen de los puntos donde hubo margen de decisión al evolucionar el sistema (login, base de
datos real, IA a escala) — detalle ampliado del modelo de datos en [`docs/MODELO_BD.md`](docs/MODELO_BD.md#3-decisiones-de-diseño-criterio-propio-documentadas):

- **JWT en vez de sesiones**: el frontend es una SPA sin backend de sesiones; JWT es stateless y
  se valida igual en cada proxy hacia `ia_service`. Los tokens llevan `rol` (y `id_estudiante`,
  `carrera_id`, `ciclo_actual` cuando aplica) para no repetir consultas a MySQL en cada request.
- **jsPDF + html2canvas para exportar horarios**: enfoque 100% client-side — captura el DOM real
  de la grilla (con los mismos colores/datos que ve el usuario) sin tocar el backend ni generar
  PDFs server-side.
- **`demanda_matricula` se mantiene como tabla histórica separada** (`demanda_matricula_historico`),
  no se migra al catálogo real: el modelo de regresión no usa el nombre del curso como feature
  (usa variables numéricas: alumnos nuevos/repitentes/prerrequisito, capacidad, duración,
  docentes, laboratorio), así que sigue siendo válido para estimar demanda de los 78 cursos reales
  sin reentrenar con datos ficticios nuevos. La demanda real de entrada al modelo se deriva del
  conteo real de `estudiantes` por carrera/ciclo.
- **AG#3 standalone mantiene su cap (ahora configurable, default 30)**: el dataset histórico tiene
  **1200 nombres de curso distintos** (no ~50 como parecía a primera vista) — sin recorte, el
  fitness O(n_cursos²) del GA vuelve el endpoint interactivo impracticable (se comprobó: >60s y
  cuelga el servicio). El requisito de "operar sobre todos los cursos reales, sin recorte" se
  resuelve con el **nuevo endpoint orquestador** (`/ml/horario-administrativo/generar`), que sí
  procesa los 78 cursos reales completos, porque usa una asignación global por restricciones
  (no una búsqueda GA combinatoria conjunta) — mismo motivo por el que el código original ya
  limitaba a top-30/20 aulas.
- **Planificador BFS/DFS/A\*** sí se escaló sin recorte: ahora usa las 288 aulas y 70 bloques reales
  por defecto (antes limitaba a 20 aulas del dataset histórico) porque `MAX_NODOS_ASTAR` ya acota
  el costo de búsqueda independientemente del tamaño del catálogo de aulas.
- **70 docentes / 600 estudiantes** de seed: suficiente para poblar secciones de los 78 cursos en
  varias franjas horarias sin saturar el script SQL ni la demo.
- **No se construyó un CRUD de administración de cursos/docentes/aulas/usuarios**: no estaba en la
  lista de entregables concretos del encargo (solo se menciona como capacidad general de "acceso
  total" del admin); el foco fue el flujo end-to-end de horario administrativo + horario del
  estudiante. Quedaría como siguiente iteración natural.

---

## App original (Tkinter)

El archivo `demanda_aulas_matrícula_IA.py` **no fue modificado** y sigue funcionando de forma independiente:

```bash
# Requiere: pip install pandas numpy scikit-learn matplotlib mysql-connector-python
python demanda_aulas_matrícula_IA.py
```

Solo necesita XAMPP con MySQL activo.
