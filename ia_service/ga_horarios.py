"""
ga_horarios.py
AG #3 — Timetabling: asigna top-30 cursos a (aula, turno).
Extraído 1:1 de demanda_aulas_matrícula_IA.py (rama dev-sergio).
"""
import random
import numpy as np
import pandas as pd


def _clasificar_ocupacion(ratio: float) -> str:
    if ratio > 1:      return "Excede aforo"
    if ratio >= 0.90:  return "Ajustado"
    if ratio >= 0.65:  return "Óptimo"
    if ratio >= 0.45:  return "Baja ocupación"
    return "Subutilizado"


def ga_horarios(df: pd.DataFrame, pop_size: int = 40,
                n_gen: int = 60, mutation_rate: float = 0.05) -> dict:
    """
    GA #3 — Asigna top-30 cursos más demandados a (aula, turno)
    minimizando conflictos de aula, conflictos de docente y hacinamiento.
    """
    resumen = (
        df.groupby("nombre_curso", as_index=False)
        .agg(
            demanda=("alumnos_matriculados", "mean"),
            laboratorio=("laboratorio", "max"),
            docente_id=("docente_id", "first"),
        )
        .sort_values("demanda", ascending=False)
        .head(30)
        .reset_index(drop=True)
    )
    resumen["demanda"] = resumen["demanda"].round().astype(int)

    aulas = (
        df[["aula_id", "capacidad_aula", "pabellon"]]
        .drop_duplicates("aula_id")
        .reset_index(drop=True)
    )
    turnos = sorted(df["horario_seccion"].dropna().unique().tolist())

    n_c, n_a, n_t = len(resumen), len(aulas), len(turnos)
    if n_a == 0 or n_t == 0 or n_c == 0:
        return {"asignaciones": [], "conflictos": 0, "score": 0.0}

    caps = aulas["capacidad_aula"].values
    docs = resumen["docente_id"].values
    dems = resumen["demanda"].values

    def fitness(ind):
        a_idx, t_idx = ind[:n_c], ind[n_c:]
        s = 0.0
        for i in range(n_c):
            for j in range(i + 1, n_c):
                if a_idx[i] == a_idx[j] and t_idx[i] == t_idx[j]:
                    s -= 800
                if docs[i] == docs[j] and t_idx[i] == t_idx[j]:
                    s -= 500
        for i in range(n_c):
            ocup = dems[i] / caps[a_idx[i]] if caps[a_idx[i]] > 0 else 2.0
            if ocup > 1.0:
                s -= (ocup - 1.0) * 600
            elif 0.65 <= ocup <= 0.90:
                s += 100
            elif ocup < 0.40:
                s -= (0.40 - ocup) * 150
        return s

    gene_len = 2 * n_c
    pop = [
        list(np.random.randint(0, n_a, n_c)) + list(np.random.randint(0, n_t, n_c))
        for _ in range(pop_size)
    ]
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
            pt    = random.randint(1, gene_len - 1)
            child = pop[t1][:pt] + pop[t2][pt:]
            for k in range(gene_len):
                if random.random() < mutation_rate:
                    child[k] = (
                        random.randint(0, n_a - 1) if k < n_c
                        else random.randint(0, n_t - 1)
                    )
            new_pop.append(child)
        pop = new_pop

    a_asig, t_asig = best_ind[:n_c], best_ind[n_c:]

    # Contar conflictos de aula
    slot_count: dict = {}
    for ai, ti in zip(a_asig, t_asig):
        key = (int(ai), int(ti))
        slot_count[key] = slot_count.get(key, 0) + 1
    conflictos = sum(v - 1 for v in slot_count.values() if v > 1)

    asignaciones = []
    for i, (ai, ti) in enumerate(zip(a_asig, t_asig)):
        dem = int(dems[i])
        cap = int(caps[ai])
        ocup = dem / cap if cap > 0 else 2.0
        asignaciones.append({
            "curso":     resumen["nombre_curso"].iloc[i],
            "aula_id":   str(aulas["aula_id"].iloc[ai]),
            "pabellon":  str(aulas["pabellon"].iloc[ai]),
            "turno":     str(turnos[ti]),
            "demanda":   dem,
            "capacidad": cap,
            "ocupacion": round(ocup, 4),
            "estado":    _clasificar_ocupacion(ocup),
        })

    return {
        "asignaciones": asignaciones,
        "conflictos":   conflictos,
        "score":        round(float(best_score), 2),
        "n_cursos":     n_c,
        "n_aulas":      n_a,
        "n_turnos":     n_t,
    }
