"""
ga_variables.py
AG #1 — Selección óptima de variables predictoras.
Extraído 1:1 de demanda_aulas_matrícula_IA.py (rama dev-sergio).
"""
import random
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

COLUMNAS_FEATURES_GA = [
    "ciclo_relativo", "creditos_curso", "docente_disponible", "capacidad_aula",
    "alumnos_nuevos", "alumnos_prerrequisito", "alumnos_repitentes", "veces_llevado",
    "carga_academica_proyectada", "cursos_comun", "duracion_semanas", "laboratorio",
    "tiempo_matricula_min",
]


def ga_seleccion_variables(df: pd.DataFrame, pop_size: int = 20, n_gen: int = 30,
                            mutation_rate: float = 0.15) -> dict:
    """
    GA #1 — Selecciona el subconjunto de COLUMNAS_FEATURES_GA que minimiza
    MAE (Ridge, split 80/20).

    Devuelve dict con las features seleccionadas y el MAE obtenido.
    """
    candidatas = [c for c in COLUMNAS_FEATURES_GA if c in df.columns]
    n = len(candidatas)
    y = df["alumnos_matriculados"].values
    X_all = df[candidatas].values
    X_tr, X_te, y_tr, y_te = train_test_split(X_all, y, test_size=0.2, random_state=42)

    def fitness(ind):
        idx = [i for i in range(n) if ind[i]]
        if not idx:
            return -1e9
        pred = Ridge(alpha=1.0).fit(X_tr[:, idx], y_tr).predict(X_te[:, idx])
        return -mean_absolute_error(y_te, pred)

    pop = [[int(x) for x in np.random.randint(0, 2, n)] for _ in range(pop_size)]
    best_ind, best_score = pop[0][:], fitness(pop[0])

    history = []
    for gen in range(n_gen):
        scores = [fitness(ind) for ind in pop]
        gen_best = max(range(pop_size), key=lambda i: scores[i])
        if scores[gen_best] > best_score:
            best_score, best_ind = scores[gen_best], pop[gen_best][:]
        history.append({"gen": gen + 1, "mejor_mae": round(-best_score, 4)})

        sorted_p = sorted(range(pop_size), key=lambda i: scores[i], reverse=True)
        new_pop = [pop[sorted_p[0]][:], pop[sorted_p[1]][:]]
        while len(new_pop) < pop_size:
            t1 = max(random.sample(range(pop_size), 3), key=lambda i: scores[i])
            t2 = max(random.sample(range(pop_size), 3), key=lambda i: scores[i])
            pt = random.randint(1, n - 1)
            child = pop[t1][:pt] + pop[t2][pt:]
            for i in range(n):
                if random.random() < mutation_rate:
                    child[i] = 1 - child[i]
            if sum(child) == 0:
                child[random.randint(0, n - 1)] = 1
            new_pop.append(child)
        pop = new_pop

    seleccionadas = [candidatas[i] for i in range(n) if best_ind[i]]
    mae_ga = round(-best_score, 4)

    return {
        "features_seleccionadas": seleccionadas,
        "todas_candidatas": candidatas,
        "cromosoma": best_ind,
        "mae_ga": mae_ga,
        "n_seleccionadas": len(seleccionadas),
        "n_candidatas": len(candidatas),
        "historia": history,
    }
