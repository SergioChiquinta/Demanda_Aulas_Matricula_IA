"""
cluster_service.py
KMeans K=3 con StandardScaler — mismo pipeline que el .py original.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def _asignar_roles(centroids_real: np.ndarray, var_x: str, var_y: str) -> dict:
    usa_ratio = "alumno" in var_x.lower() and "capacidad" in var_y.lower()
    if usa_ratio:
        pares = [(i, c[0] / c[1] if c[1] > 0 else float("inf"))
                 for i, c in enumerate(centroids_real)]
    else:
        pares = [(i, c[0]) for i, c in enumerate(centroids_real)]
    pares.sort(key=lambda x: x[1])
    return {pares[0][0]: "subutilizado", pares[1][0]: "optimo", pares[2][0]: "sobrepoblado"}


def ejecutar_clustering(df: pd.DataFrame, var_x: str, var_y: str) -> dict:
    """
    Ejecuta K-Means K=3 sobre (var_x, var_y).
    Devuelve datos listos para consumir desde el frontend (no objetos numpy).
    """
    if var_x not in df.columns or var_y not in df.columns:
        raise ValueError(f"Columna no encontrada: '{var_x}' o '{var_y}'")
    if var_x == var_y:
        raise ValueError("var_x y var_y deben ser distintas")

    datos = df[[var_x, var_y]].dropna()
    if len(datos) < 9:
        raise ValueError("Se necesitan al menos 9 filas válidas")

    X_raw = datos[[var_x, var_y]].values

    # Inercias (sobre datos crudos, igual que el original)
    inercias = []
    for k in range(1, 11):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        km.fit(X_raw)
        inercias.append(float(km.inertia_))

    # KMeans K=3 sobre datos normalizados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    centroids_scaled = kmeans.cluster_centers_
    centroids_real = scaler.inverse_transform(centroids_scaled)

    try:
        sil_score = float(silhouette_score(X_scaled, labels))
    except Exception:
        sil_score = 0.0

    interp_sil = (
        "Excelente" if sil_score > 0.7 else
        "Bueno"     if sil_score > 0.5 else
        "Aceptable" if sil_score > 0.25 else "Débil"
    )

    roles = _asignar_roles(centroids_real, var_x, var_y)

    # Mejora marginal para el gráfico del codo
    gains = [abs(inercias[i] - inercias[i - 1]) for i in range(1, len(inercias))]
    rel_pct = [round(g / (inercias[0] + 1e-9) * 100, 2) for g in gains]

    # Scatter data por cluster
    scatter_data = []
    for cid in range(3):
        mask = labels == cid
        scatter_data.append({
            "cluster_id": cid,
            "rol":        roles[cid],
            "centroid_x": float(centroids_real[cid][0]),
            "centroid_y": float(centroids_real[cid][1]),
            "puntos":     [
                {"x": float(X_raw[i, 0]), "y": float(X_raw[i, 1])}
                for i in range(len(X_raw)) if mask[i]
            ],
        })

    return {
        "var_x":          var_x,
        "var_y":          var_y,
        "silhouette":     round(sil_score, 4),
        "interpretacion": interp_sil,
        "inercias":       inercias,
        "mejora_pct":     rel_pct,
        "clusters":       scatter_data,
        "roles":          roles,
    }
