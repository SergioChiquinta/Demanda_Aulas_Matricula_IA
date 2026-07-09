"""
ml_model.py
Entrena y expone los modelos de Regresión Lineal y Ridge.
Mismo pipeline que el .py original (split 80/20, random_state=42).
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

FEATURES = [
    "alumnos_nuevos", "alumnos_prerrequisito", "alumnos_repitentes",
    "docente_disponible", "capacidad_aula", "duracion_semanas", "laboratorio",
]

_modelos: dict | None = None
_features_activas: list | None = None


def set_features_activas(features: list) -> None:
    """Fija el subconjunto de FEATURES elegido por AG #1 (calibración en el arranque)."""
    global _features_activas
    _features_activas = [f for f in features if f in FEATURES] or FEATURES


def _entrenar(df: pd.DataFrame) -> dict:
    features = _features_activas or FEATURES
    X = df[features].values
    y = df["alumnos_matriculados"].values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    resultado = {}
    for nombre, modelo in [
        ("Regresión Lineal Múltiple", LinearRegression()),
        ("Regresión Ridge", Ridge(alpha=1.0)),
    ]:
        modelo.fit(X_tr, y_tr)
        pred = modelo.predict(X_te)
        resultado[nombre] = {
            "modelo": modelo,
            "MAE":    float(mean_absolute_error(y_te, pred)),
            "RMSE":   float(np.sqrt(mean_squared_error(y_te, pred))),
        }
    return resultado


def get_modelos(df: pd.DataFrame) -> dict:
    """Entrena una vez y cachea."""
    global _modelos
    if _modelos is None:
        _modelos = _entrenar(df)
    return _modelos


def predecir(df: pd.DataFrame, payload: dict) -> dict:
    """
    Recibe los valores del formulario y devuelve predicción base,
    intervalo operativo y métricas del modelo activo.
    """
    modelos = get_modelos(df)
    modelo_activo = modelos["Regresión Lineal Múltiple"]["modelo"]
    mae = modelos["Regresión Lineal Múltiple"]["MAE"]
    rmse = modelos["Regresión Lineal Múltiple"]["RMSE"]
    features = _features_activas or FEATURES

    valores_completos = {
        "alumnos_nuevos":       payload.get("alumnos_nuevos", 0),
        "alumnos_prerrequisito": payload.get("alumnos_prerrequisito", 0),
        "alumnos_repitentes":   payload.get("alumnos_repitentes", 0),
        "docente_disponible":   1 if payload.get("docentes_disponibles", 1) > 0 else 0,
        "capacidad_aula":       payload.get("capacidad_aula", 40),
        "duracion_semanas":     payload.get("duracion_semanas", 18),
        "laboratorio":          payload.get("laboratorio", 0),
    }
    entrada = pd.DataFrame([{k: valores_completos[k] for k in features}])

    pred_base = max(0, int(round(float(modelo_activo.predict(entrada)[0]))))
    pred_min  = max(0, int(np.floor(pred_base - mae)))
    pred_max  = max(pred_base, int(np.ceil(pred_base + mae)))

    return {
        "pred_base": pred_base,
        "pred_min":  pred_min,
        "pred_max":  pred_max,
        "mae":       round(mae, 4),
        "rmse":      round(rmse, 4),
    }


def get_metricas(df: pd.DataFrame) -> dict:
    modelos = get_modelos(df)
    return {
        "lineal": {
            "MAE":  modelos["Regresión Lineal Múltiple"]["MAE"],
            "RMSE": modelos["Regresión Lineal Múltiple"]["RMSE"],
        },
        "ridge": {
            "MAE":  modelos["Regresión Ridge"]["MAE"],
            "RMSE": modelos["Regresión Ridge"]["RMSE"],
        },
    }
