"""
ga_secciones.py
AG #2 — Optimización de distribución de secciones.
Extraído 1:1 de demanda_aulas_matrícula_IA.py (rama dev-sergio).
"""
import random
import numpy as np


def ga_optimizar_secciones(demanda_plan: int, capacidad_efectiva: int,
                            docentes_disponibles: int,
                            pop_size: int = 30, n_gen: int = 50) -> dict:
    """
    GA #2 — Optimiza (n_secciones, factor_ocupacion) para distribución de aulas.
    Cromosoma: [n_sec ∈ 1-10, factor*100 ∈ 60-100].
    """
    if demanda_plan <= 0 or capacidad_efectiva <= 0:
        return {
            "n_secciones": 1, "factor_ocupacion": 0.90,
            "cap_segura": capacidad_efectiva, "total_cupos": capacidad_efectiva,
            "ocupacion": 0.0, "fitness": 0.0,
        }

    def decode(ind):
        n_sec  = max(1, min(10, ind[0]))
        factor = max(0.60, min(1.00, ind[1] / 100.0))
        cap_seg = max(1, int(np.floor(capacidad_efectiva * factor)))
        total   = n_sec * capacidad_efectiva
        ocup    = demanda_plan / total if total > 0 else 2.0
        return n_sec, factor, cap_seg, total, ocup

    def fitness(ind):
        n_sec, _, _, _, ocup = decode(ind)
        s = 200.0 if 0.65 <= ocup <= 0.90 else (80.0 if 0.50 <= ocup < 0.65 else 0.0)
        s -= max(0.0, ocup - 1.0)  * 1200
        s -= max(0.0, ocup - 0.90) * 400
        s -= max(0.0, 0.45 - ocup) * 500
        if docentes_disponibles > 0:
            s -= max(0, n_sec - docentes_disponibles) * 600
        s -= abs(ocup - 0.75) * 80
        return s

    pop = [[random.randint(1, 8), random.randint(70, 100)] for _ in range(pop_size)]
    best_ind, best_score = pop[0][:], fitness(pop[0])

    for _ in range(n_gen):
        scores = [fitness(ind) for ind in pop]
        gen_best = max(range(pop_size), key=lambda i: scores[i])
        if scores[gen_best] > best_score:
            best_score, best_ind = scores[gen_best], pop[gen_best][:]
        sorted_p = sorted(range(pop_size), key=lambda i: scores[i], reverse=True)
        new_pop  = [pop[sorted_p[0]][:], pop[sorted_p[1]][:]]
        while len(new_pop) < pop_size:
            t1 = max(random.sample(range(pop_size), 3), key=lambda i: scores[i])
            t2 = max(random.sample(range(pop_size), 3), key=lambda i: scores[i])
            child = [
                pop[t1][0] if random.random() < 0.5 else pop[t2][0],
                pop[t1][1] if random.random() < 0.5 else pop[t2][1],
            ]
            if random.random() < 0.25:
                child[0] = max(1, min(10, child[0] + random.randint(-1, 1)))
            if random.random() < 0.25:
                child[1] = max(60, min(100, child[1] + random.randint(-5, 5)))
            new_pop.append(child)
        pop = new_pop

    n_sec, factor, cap_seg, total, ocup = decode(best_ind)

    # Distribución sugerida
    base_sec  = demanda_plan // n_sec
    resto_sec = demanda_plan % n_sec
    secciones = []
    for i in range(n_sec):
        alumnos_sec = base_sec + (1 if i < resto_sec else 0)
        secciones.append({
            "seccion":    f"S{i + 1}",
            "alumnos":    alumnos_sec,
            "capacidad":  capacidad_efectiva,
            "ocupacion":  round(alumnos_sec / capacidad_efectiva, 4) if capacidad_efectiva > 0 else 0,
        })

    return {
        "n_secciones":       n_sec,
        "factor_ocupacion":  round(factor, 4),
        "cap_segura":        cap_seg,
        "total_cupos":       total,
        "ocupacion":         round(ocup, 4),
        "fitness":           round(best_score, 2),
        "secciones":         secciones,
        "deficit_docentes":  max(0, n_sec - docentes_disponibles),
    }
