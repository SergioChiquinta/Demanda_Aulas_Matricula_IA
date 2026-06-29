# Demanda Aulas Matrícula IA — Guía de Instalación y Arranque

Sistema web completo para predicción de demanda de aulas académicas con Algoritmos Genéticos.  
Stack: **React + Vite** (frontend) · **Node.js + Express** (backend) · **Python + FastAPI** (IA) · **MySQL** (base de datos)

---

## Requisitos previos

| Herramienta | Versión mínima | Verificar |
|-------------|---------------|-----------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node -v` |
| npm | 9+ | `npm -v` |
| XAMPP (MySQL) | cualquiera | Apache + MySQL activos |

---

## Estructura del proyecto

```
Demanda_Aulas_Matricula_IA/
├── demanda_aulas_matrícula_IA.py   ← App original Tkinter (intacta)
├── demanda_aulas_matricula_ia.sql  ← Script SQL de la base de datos
├── README.md                       ← (este archivo, original)
├── SETUP.md                        ← Esta guía
│
├── ia_service/                     ← Microservicio Python (FastAPI)
│   ├── main.py
│   ├── data_loader.py
│   ├── ml_model.py
│   ├── cluster_service.py
│   ├── ga_variables.py
│   ├── ga_secciones.py
│   ├── ga_horarios.py
│   ├── requirements.txt
│   └── .env
│
├── backend/                        ← API REST (Node.js + Express)
│   ├── src/
│   │   ├── app.js
│   │   ├── db/mysql.js
│   │   ├── routes/
│   │   └── controllers/
│   ├── package.json
│   └── .env
│
└── frontend/                       ← Interfaz Web (React + Vite)
    ├── src/
    │   ├── App.jsx
    │   ├── api/client.js
    │   ├── components/
    │   └── pages/
    └── package.json
```

---

## Paso 1 — Base de datos (XAMPP)

1. Abre **XAMPP Control Panel**
2. Inicia **Apache** y **MySQL**
3. Ve a `http://localhost/phpmyadmin`
4. Pestaña **Importar** → selecciona `demanda_aulas_matricula_ia.sql`
5. Ejecuta la importación → debe mostrar `total_registros = 1200`

> ⚠️ La base de datos debe estar activa antes de arrancar cualquier servicio.

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

| Paquete | Uso |
|---------|-----|
| `fastapi` | Framework API REST |
| `uvicorn[standard]` | Servidor ASGI |
| `pydantic` | Validación de datos |
| `mysql-connector-python` | Conexión a MySQL |
| `pandas` | Manejo de datos (DataFrame) |
| `numpy` | Operaciones numéricas |
| `scikit-learn` | KMeans, Ridge, LinearRegression |
| `python-dotenv` | Leer variables de entorno |

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
```

### 3.2 Instalar dependencias

```bash
cd backend
npm install
```

Paquetes que se instalan:

| Paquete | Uso |
|---------|-----|
| `express` | Framework web |
| `mysql2` | Pool de conexiones MySQL |
| `axios` | Llamadas HTTP al microservicio Python |
| `cors` | Habilitar CORS para el frontend |
| `dotenv` | Leer variables de entorno |
| `nodemon` | Recarga automática en desarrollo |

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

| Paquete | Uso |
|---------|-----|
| `react` + `react-dom` | Framework UI |
| `react-router-dom` | Navegación entre páginas |
| `recharts` | Gráficos (scatter, barras, líneas) |
| `axios` | Llamadas HTTP al backend |
| `vite` | Bundler y servidor de desarrollo |

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

Abre `http://localhost:5173` en tu navegador.

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

| Servicio | URL | Descripción |
|---------|-----|-------------|
| React (Frontend) | `http://localhost:5173` | Interfaz web principal |
| Node.js (Backend) | `http://localhost:3001` | API REST |
| FastAPI (IA) | `http://localhost:8000` | Microservicio de IA y GAs |
| FastAPI Docs | `http://localhost:8000/docs` | Swagger UI interactivo |
| MySQL | `localhost:3306` | Base de datos |

---

## Módulos disponibles en la interfaz

| Módulo | Ruta | Descripción |
|--------|------|-------------|
| Dashboard | `/` | KPIs históricos + tabla de matrículas |
| Análisis de Aforos | `/analisis` | Clustering K-Means K=3 con gráficos |
| Simulación IA | `/simulacion` | Predicción con Regresión Lineal/Ridge |
| AG-1 Variables | `/ga1` | Selección óptima de features (GA) |
| AG-2 Secciones | `/ga2` | Optimización de distribución de aulas |
| AG-3 Horarios | `/ga3` | Timetabling automático (top 30 cursos) |

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

## App original (Tkinter)

El archivo `demanda_aulas_matrícula_IA.py` **no fue modificado** y sigue funcionando de forma independiente:

```bash
# Requiere: pip install pandas numpy scikit-learn matplotlib mysql-connector-python
python demanda_aulas_matrícula_IA.py
```

Solo necesita XAMPP con MySQL activo.
