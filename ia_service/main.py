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
from ga_variables import COLUMNAS_FEATURES_GA, ga_seleccion_variables
from ml_model import predecir, get_metricas, get_modelos
from cluster_service import ejecutar_clustering
from ga_secciones import ga_optimizar_secciones
from ga_horarios import ga_horarios

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga datos y entrena modelos al arrancar."""
    logger.info("Cargando datos desde MySQL...")
    df = cargar_datos()
    logger.info(f"Dataset cargado: {len(df)} registros.")
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
@app.get("/ml/ga/candidatas")
def ga_candidatas():
    df = get_df()
    return {
        "candidatas": [
            {"nombre": c, "disponible": c in df.columns}
            for c in COLUMNAS_FEATURES_GA
        ]
    }


@app.post("/ml/ga/variables")
def ga1_variables():
    """GA #1 — Puede tardar 5-15 segundos."""
    try:
        df = get_df()
        metricas = get_metricas(df)
        resultado = ga_seleccion_variables(df)
        resultado["mae_base"] = metricas["lineal"]["MAE"]
        resultado["mejora"] = round(metricas["lineal"]["MAE"] - resultado["mae_ga"], 4)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
def ga3_horarios():
    """GA #3 — Timetabling. Puede tardar 10-30 segundos."""
    try:
        df = get_df()
        return ga_horarios(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
