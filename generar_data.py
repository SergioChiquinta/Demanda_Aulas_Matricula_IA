# =====================================
# ARCHIVO PARA GENERAR DATASET EN EXCEL
# =====================================

# ==========================================================================================================
# No recomendable aplicar para esta versión del proyecto, pero se deja como referencia para futuras mejoras.
# ==========================================================================================================

import pandas as pd
import numpy as np

np.random.seed(42)

rows = 1200

data = {
    "periodo": np.random.choice(
        ["2021-1","2021-2","2022-1","2022-2","2023-1","2023-2","2024-1","2024-2","2025-1","2025-2"],
        rows
    ),
    "id_curso": np.random.randint(100, 200, rows),
    "nombre_curso": ["Curso_"+str(i) for i in range(rows)],
    "ciclo_relativo": np.random.randint(1, 10, rows),
    "creditos_curso": np.random.randint(2, 5, rows),
    "docente_id": np.random.randint(1, 50, rows),
    "docente_disponible": np.random.randint(0, 2, rows),
    "aula_id": np.random.randint(1, 30, rows),
    "capacidad_aula": np.random.randint(20, 60, rows),
    "pabellon": np.random.choice(["A","B","C"], rows),
    "horario_seccion": np.random.choice(["Mañana","Tarde","Noche"], rows),
    "alumnos_nuevos": np.random.randint(5, 40, rows),
    "alumnos_prerrequisito": np.random.randint(5, 30, rows),
    "alumnos_repitentes": np.random.randint(0, 20, rows),
    "veces_llevado": np.random.randint(1, 3, rows),
    "carga_academica_proyectada": np.random.randint(10, 25, rows),
    "cursos_comun": np.random.randint(0, 2, rows),
    "duracion_semanas": np.random.randint(8, 16, rows),
    "laboratorio": np.random.randint(0, 2, rows),
    "tiempo_matricula_min": np.random.randint(135, 270, rows),
}

df = pd.DataFrame(data)

df["alumnos_matriculados"] = (
    df["alumnos_nuevos"]
    + df["alumnos_prerrequisito"]
    + df["alumnos_repitentes"]
    + np.random.randint(-5, 5, rows)
)

df.to_excel("data_prediccion_aulas.xlsx", index=False)

print("Excel generado correctamente")
