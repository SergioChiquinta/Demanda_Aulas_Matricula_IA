"""
data_loader.py
Carga el dataset desde MySQL (vista vw_dataset_prediccion_aulas)
y lo mantiene en memoria para todos los servicios ML.
"""
import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "127.0.0.1"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "1234"),
    "database": os.getenv("DB_NAME", "demanda_aulas_matricula_ia"),
    "charset":  "utf8mb4",
    "use_pure": True,
}

COLUMNAS_DATASET = [
    "periodo", "id_curso", "nombre_curso", "ciclo_relativo", "creditos_curso",
    "docente_id", "docente_disponible", "aula_id", "capacidad_aula", "pabellon",
    "horario_seccion", "alumnos_nuevos", "alumnos_prerrequisito", "alumnos_repitentes",
    "veces_llevado", "carga_academica_proyectada", "cursos_comun", "duracion_semanas",
    "laboratorio", "tiempo_matricula_min", "alumnos_matriculados",
]

COLUMNAS_NUMERICAS = [
    "id_curso", "ciclo_relativo", "creditos_curso", "docente_id", "docente_disponible",
    "aula_id", "capacidad_aula", "alumnos_nuevos", "alumnos_prerrequisito",
    "alumnos_repitentes", "veces_llevado", "carga_academica_proyectada", "cursos_comun",
    "duracion_semanas", "laboratorio", "tiempo_matricula_min", "alumnos_matriculados",
]

_df_cache: pd.DataFrame | None = None


def cargar_datos(force_reload: bool = False) -> pd.DataFrame:
    """Carga el dataset una vez y lo cachea en memoria."""
    global _df_cache
    if _df_cache is not None and not force_reload:
        return _df_cache

    conexion = None
    cursor = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        cols_sql = ", ".join(COLUMNAS_DATASET)
        cursor.execute(f"SELECT {cols_sql} FROM vw_dataset_prediccion_aulas ORDER BY id_registro")
        filas = cursor.fetchall()

        df = pd.DataFrame(filas, columns=COLUMNAS_DATASET)
        if df.empty:
            raise ValueError("La vista SQL no devolvió registros.")

        for col in COLUMNAS_NUMERICAS:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if df[COLUMNAS_NUMERICAS].isnull().any().any():
            raise ValueError("Existen valores numéricos nulos en la vista SQL.")

        df[COLUMNAS_NUMERICAS] = df[COLUMNAS_NUMERICAS].astype(int)
        _df_cache = df
        return df

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


def get_df() -> pd.DataFrame:
    """Acceso rápido al DataFrame cacheado."""
    if _df_cache is None:
        return cargar_datos()
    return _df_cache
