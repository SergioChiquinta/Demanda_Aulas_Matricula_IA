"""
main.py — FastAPI microservicio IA
Expone todos los endpoints /ml que el backend Node.js consume.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging

from data_loader import cargar_datos, get_df
from ga_variables import ga_seleccion_variables
from ml_model import predecir, get_metricas, get_modelos, set_features_activas, FEATURES
from cluster_service import ejecutar_clustering
from ga_secciones import ga_optimizar_secciones
from ga_horarios import ga_horarios, ga_horarios_secciones
# ── Motor Inteligente de Planificación (nuevo módulo IA Clásica) ──
from planner import PlanificadorInteligente
# ── Orquestador del horario administrativo (catálogo real UTP Lima Sur) ──
from orquestador_horario import generar_horario_administrativo, _cargar_catalogo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga datos, calibra variables (AG #1) y entrena modelos al arrancar."""
    logger.info("Cargando datos desde MySQL...")
    df = cargar_datos()
    logger.info(f"Dataset cargado: {len(df)} registros.")

    logger.info("Calibrando variables del modelo (AG #1)...")
    calibracion = ga_seleccion_variables(df, candidatas=FEATURES)
    set_features_activas(calibracion["features_seleccionadas"])
    logger.info(
        f"Variables activas: {calibracion['features_seleccionadas']} "
        f"(MAE AG: {calibracion['mae_ga']})"
    )

    get_modelos(df)
    logger.info("Modelos entrenados y listos.")
    yield
    logger.info("Servicio detenido.")


app = FastAPI(title="Demanda Aulas IA Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────────
class ClusterRequest(BaseModel):
    var_x: str
    var_y: str


class PredictRequest(BaseModel):
    alumnos_nuevos: int = 25
    alumnos_prerrequisito: int = 20
    alumnos_repitentes: int = 8
    capacidad_aula: int = 40
    duracion_semanas: int = 18
    docentes_disponibles: int = 2
    laboratorio: int = 0


class SeccionesRequest(BaseModel):
    demanda_plan: int
    capacidad_efectiva: int
    docentes_disponibles: int = 1


class SeccionItem(BaseModel):
    seccion: str
    alumnos: int
    capacidad: int | None = None
    ocupacion: float | None = None


class HorariosRequest(BaseModel):
    secciones: list[SeccionItem] | None = None
    curso_nombre: str | None = None
    # El dataset histórico standalone tiene 1200 nombres de curso distintos
    # (sintéticos): sin recorte, el fitness O(n_cursos^2) por generación
    # vuelve el GA impracticable. Se mantiene el default de 30 (comportamiento
    # original) pero ahora es un parámetro explícito y ajustable por el
    # caller — a diferencia de antes, que estaba fijo en el código. El
    # requisito de "operar sobre todos los cursos reales" se resuelve con el
    # catálogo real (78 cursos) vía /ml/horario-administrativo/generar, que
    # no sufre esta explosión porque no ejecuta este GA de forma global.
    top_n: int | None = 30


class GenerarHorarioRequest(BaseModel):
    periodo_id: int


# ── Endpoints ────────────────────────────────────────────────
@app.get("/ml/health")
def health():
    return {"status": "ok", "registros": len(get_df())}


@app.get("/ml/metricas")
def metricas():
    try:
        df = get_df()
        return get_metricas(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/variables")
def variables_disponibles():
    """Lista todas las variables numéricas disponibles para clustering."""
    df = get_df()
    vars_num = [
        "alumnos_matriculados", "capacidad_aula", "carga_academica_proyectada",
        "creditos_curso", "alumnos_repitentes", "tiempo_matricula_min",
        "alumnos_nuevos", "veces_llevado", "alumnos_prerrequisito",
        "duracion_semanas", "ciclo_relativo",
    ]
    disponibles = [v for v in vars_num if v in df.columns]
    return {"variables": disponibles}


@app.post("/ml/cluster")
def clustering(req: ClusterRequest):
    try:
        df = get_df()
        return ejecutar_clustering(df, req.var_x, req.var_y)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/predict")
def predict(req: PredictRequest):
    try:
        df = get_df()
        return predecir(df, req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GA Endpoints ──────────────────────────────────────────────
# AG #1 (variables) ya no se expone como endpoint: se ejecuta una sola vez
# al arrancar el servicio (ver lifespan) para calibrar el modelo de predicción.


@app.post("/ml/ga/secciones")
def ga2_secciones(req: SeccionesRequest):
    """GA #2 — Optimiza distribución de secciones."""
    try:
        return ga_optimizar_secciones(
            req.demanda_plan,
            req.capacidad_efectiva,
            req.docentes_disponibles,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/ga/horarios")
def ga3_horarios(req: HorariosRequest = HorariosRequest()):
    """
    GA #3 — Timetabling. Puede tardar 10-30 segundos.
    Si recibe `secciones` (salida de AG #2), asigna aula/turno real
    exactamente a esas secciones (modo pipeline, encadenado con AG #2).
    Si no, opera de forma standalone sobre el top-30 del dataset.
    """
    try:
        df = get_df()
        if req.secciones:
            secciones = [s.model_dump() for s in req.secciones]
            return ga_horarios_secciones(df, secciones, req.curso_nombre)
        return ga_horarios(df, top_n=req.top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
# HORARIO ADMINISTRATIVO — pipeline completo sobre el catálogo real
# (78 cursos x 288 aulas x 70 bloques). Regresión -> AG#2 -> asignación
# global. Persiste el resultado en la tabla `secciones`.
# ══════════════════════════════════════════════════════════════════
@app.post("/ml/horario-administrativo/generar")
def horario_administrativo_generar(req: GenerarHorarioRequest):
    """
    Ejecuta el pipeline completo para un periodo y persiste el resultado.
    Puede tardar decenas de segundos (recorre los ~78 cursos reales).
    """
    try:
        return generar_horario_administrativo(req.periodo_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
# MOTOR INTELIGENTE DE PLANIFICACIÓN — IA Clásica (Espacios de Estados)
# Nuevos endpoints que se activan DESPUÉS de la predicción ML.
# No modifican ningún endpoint existente.
# ══════════════════════════════════════════════════════════════════

# ── Pydantic Models del Planificador ─────────────────────────────
class AulaInput(BaseModel):
    id: str
    capacidad: int
    pabellon: str = "-"


class PlannerRequest(BaseModel):
    """Payload para los endpoints del Motor Inteligente de Planificación."""
    demanda_predicha: int = 45          # alumnos a planificar (viene del ML)
    docentes_disponibles: int = 3       # docentes con los que se cuenta
    aulas: list[AulaInput] | None = None       # None = usar aulas del dataset
    horarios: list[str] | None = None          # None = usar turnos del dataset


# ── Instancia singleton del planificador ──────────────────────────
_planificador = PlanificadorInteligente()


def _resolver_aulas(req: PlannerRequest) -> list[dict]:
    """
    Si el request no trae aulas, usa las 288 aulas reales del campus
    (4 pabellones x 8 pisos x 9 salones, aforo 40) desde la tabla
    operativa `aulas`. Sin recorte: MAX_NODOS_ASTAR ya acota la
    búsqueda independientemente de cuántas aulas se ofrezcan.
    """
    if req.aulas:
        return [a.model_dump() for a in req.aulas]
    catalogo = _cargar_catalogo()
    return [
        {"id": row["codigo_aula"], "capacidad": int(row["aforo"]), "pabellon": row["codigo_aula"][0]}
        for row in catalogo["aulas"]
    ]


def _resolver_horarios(req: PlannerRequest) -> list[str]:
    """
    Si el request no trae horarios, usa los 70 bloques reales
    (día + franja) de la tabla operativa `bloques_horario`.
    """
    if req.horarios:
        return req.horarios
    catalogo = _cargar_catalogo()
    return [f'{b["dia_semana"]} #{b["orden"]}' for b in catalogo["bloques"]]


@app.post("/ml/planner/bfs")
def planner_bfs(req: PlannerRequest):
    """
    Ejecuta BFS (Búsqueda en Anchura) sobre el espacio de estados
    del problema de asignación de aulas.
    Garantiza el camino de MENOR NÚMERO DE PASOS.
    """
    try:
        aulas = _resolver_aulas(req)
        horarios = _resolver_horarios(req)
        return _planificador.planificar(
            demanda_predicha=req.demanda_predicha,
            aulas=aulas,
            docentes_disponibles=req.docentes_disponibles,
            horarios=horarios,
            algoritmo="bfs",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/planner/dfs")
def planner_dfs(req: PlannerRequest):
    """
    Ejecuta DFS (Búsqueda en Profundidad) sobre el espacio de estados.
    Encuentra una solución rápidamente, no garantiza optimalidad.
    """
    try:
        aulas = _resolver_aulas(req)
        horarios = _resolver_horarios(req)
        return _planificador.planificar(
            demanda_predicha=req.demanda_predicha,
            aulas=aulas,
            docentes_disponibles=req.docentes_disponibles,
            horarios=horarios,
            algoritmo="dfs",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/planner/astar")
def planner_astar(req: PlannerRequest):
    """
    Ejecuta A* con f(n) = g(n) + h(n) sobre el espacio de estados.
    Con heurística admisible garantiza el camino de MENOR COSTO TOTAL.
    Es el algoritmo recomendado para planificación óptima.
    """
    try:
        aulas = _resolver_aulas(req)
        horarios = _resolver_horarios(req)
        return _planificador.planificar(
            demanda_predicha=req.demanda_predicha,
            aulas=aulas,
            docentes_disponibles=req.docentes_disponibles,
            horarios=horarios,
            algoritmo="astar",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
