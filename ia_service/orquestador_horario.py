"""
orquestador_horario.py
Orquesta el pipeline completo que genera y persiste el horario
administrativo de un periodo:

    Regresión (demanda por curso) -> AG#2 (n° de secciones y tamaño)
    -> asignación global de aula + bloque + docente (greedy con
       restricciones), respetando aforo=40 y duración=18 semanas fijos.

No reemplaza AG#3 standalone (`ga_horarios`) ni el planificador
BFS/DFS/A* (`planner/`): esos siguen expuestos como endpoints
independientes para explorar/demostrar el timetabling óptimo sobre un
curso o subconjunto puntual. Aquí se resuelve el problema a la escala
real del catálogo (78 cursos x 288 aulas x 70 bloques), donde una
búsqueda combinatoria conjunta explotaría — el propio código ya
limitaba top-30 cursos / 20 aulas antes de esta migración por la misma
razón. La asignación global sigue siendo consciente de restricciones
(un docente no puede repetirse en el mismo bloque, un aula+bloque no
se reutiliza dentro del periodo) vía las claves UNIQUE de `secciones`.
"""
import os
import random
import mysql.connector
from dotenv import load_dotenv

from data_loader import get_df
from ml_model import predecir
from ga_secciones import ga_optimizar_secciones

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "1234"),
    "database": os.getenv("DB_NAME", "demanda_aulas_matricula_ia"),
    "charset": "utf8mb4",
    "use_pure": True,
}


def _conectar():
    return mysql.connector.connect(**DB_CONFIG)


def _cargar_catalogo() -> dict:
    conn = _conectar()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT c.id_curso, c.nombre_curso, c.es_laboratorio,
                   mc.carrera_id, mc.ciclo
            FROM cursos c
            JOIN malla_cursos mc ON mc.curso_id = c.id_curso
        """)
        malla = cur.fetchall()

        cur.execute("SELECT id_aula, codigo_aula, aforo FROM aulas ORDER BY codigo_aula")
        aulas = cur.fetchall()

        cur.execute("SELECT id_bloque, dia_semana, orden FROM bloques_horario ORDER BY orden, dia_semana")
        bloques = cur.fetchall()

        cur.execute("""
            SELECT carrera_id, ciclo_actual AS ciclo, COUNT(*) AS n
            FROM estudiantes GROUP BY carrera_id, ciclo_actual
        """)
        poblacion = {(r["carrera_id"], r["ciclo"]): r["n"] for r in cur.fetchall()}

        cur.execute("SELECT docente_id, curso_id FROM docente_curso")
        docentes_por_curso: dict = {}
        for r in cur.fetchall():
            docentes_por_curso.setdefault(r["curso_id"], []).append(r["docente_id"])

        return {
            "malla": malla, "aulas": aulas, "bloques": bloques,
            "poblacion": poblacion, "docentes_por_curso": docentes_por_curso,
        }
    finally:
        cur.close()
        conn.close()


def _persistir(periodo_id: int, secciones: list[dict]) -> None:
    conn = _conectar()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM matriculas WHERE periodo_id = %s", (periodo_id,))
        cur.execute("DELETE FROM secciones WHERE periodo_id = %s", (periodo_id,))
        for s in secciones:
            cur.execute(
                """INSERT INTO secciones
                   (periodo_id, curso_id, docente_id, aula_id, bloque_id,
                    codigo_seccion, aforo, alumnos_estimados, duracion_semanas)
                   VALUES (%s, %s, %s, %s, %s, %s, 40, %s, 18)""",
                (periodo_id, s["curso_id"], s["docente_id"], s["aula_id"],
                 s["bloque_id"], s["codigo_seccion"], s["alumnos_estimados"]),
            )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def generar_horario_administrativo(periodo_id: int) -> dict:
    """Punto de entrada del pipeline. Devuelve un resumen serializable."""
    catalogo = _cargar_catalogo()
    df_hist = get_df()  # dataset histórico ya cacheado, calibra el modelo entrenado

    # Un curso "Ambas" aparece 2 veces en malla_cursos (una por carrera);
    # se agrupa para no duplicar la sección.
    cursos: dict = {}
    for fila in catalogo["malla"]:
        c = cursos.setdefault(fila["id_curso"], {
            "nombre_curso": fila["nombre_curso"],
            "es_laboratorio": fila["es_laboratorio"],
            "combos": [],
        })
        c["combos"].append((fila["carrera_id"], fila["ciclo"]))

    slots_aula_bloque = [
        (a["id_aula"], b["id_bloque"])
        for a in catalogo["aulas"]
        for b in catalogo["bloques"]
    ]
    random.shuffle(slots_aula_bloque)

    ocupado_docente_bloque: set = set()
    secciones_a_insertar = []
    resumen_cursos = []

    for curso_id, info in cursos.items():
        docentes_habilitados = catalogo["docentes_por_curso"].get(curso_id, [])
        if not docentes_habilitados:
            resumen_cursos.append({
                "curso": info["nombre_curso"], "demanda_predicha": 0,
                "n_secciones": 0, "nota": "sin docentes habilitados",
            })
            continue
        n_docentes = len(docentes_habilitados)

        demanda_base = sum(catalogo["poblacion"].get(combo, 0) for combo in info["combos"])
        payload = {
            "alumnos_nuevos":        round(demanda_base * 0.6),
            "alumnos_prerrequisito": round(demanda_base * 0.25),
            "alumnos_repitentes":    round(demanda_base * 0.15),
            "capacidad_aula":        40,
            "duracion_semanas":      18,
            "docentes_disponibles":  n_docentes,
            "laboratorio":           int(info["es_laboratorio"]),
        }
        prediccion = predecir(df_hist, payload)
        demanda_predicha = max(1, prediccion["pred_base"])

        ag2 = ga_optimizar_secciones(
            demanda_plan=demanda_predicha,
            capacidad_efectiva=40,
            docentes_disponibles=n_docentes,
        )

        secciones_curso = 0
        for i, sec in enumerate(ag2.get("secciones", [])):
            docente_id = docentes_habilitados[i % n_docentes]

            asignado = None
            for candidato in slots_aula_bloque:
                aula_id, bloque_id = candidato
                if (docente_id, bloque_id) in ocupado_docente_bloque:
                    continue
                asignado = candidato
                break

            if asignado is None:
                continue  # no quedan slots (aula,bloque) libres compatibles con este docente

            slots_aula_bloque.remove(asignado)
            aula_id, bloque_id = asignado
            ocupado_docente_bloque.add((docente_id, bloque_id))
            secciones_a_insertar.append({
                "curso_id": curso_id, "docente_id": docente_id, "aula_id": aula_id,
                "bloque_id": bloque_id, "codigo_seccion": sec["seccion"],
                "alumnos_estimados": sec["alumnos"],
            })
            secciones_curso += 1

        resumen_cursos.append({
            "curso": info["nombre_curso"],
            "demanda_predicha": demanda_predicha,
            "n_secciones_planeadas": ag2.get("n_secciones", 0),
            "n_secciones_asignadas": secciones_curso,
        })

    _persistir(periodo_id, secciones_a_insertar)

    return {
        "periodo_id": periodo_id,
        "cursos_procesados": len(cursos),
        "secciones_creadas": len(secciones_a_insertar),
        "aulas_disponibles": len(catalogo["aulas"]),
        "bloques_disponibles": len(catalogo["bloques"]),
        "resumen_cursos": resumen_cursos,
    }
