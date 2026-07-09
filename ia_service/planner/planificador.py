"""
planner/planificador.py
Motor Inteligente de Planificación — Orquestador principal.

Recibe la predicción de alumnos del módulo ML, construye el estado inicial,
selecciona el algoritmo de búsqueda y retorna la planificación óptima.

Flujo:
    Predicción ML → Estado Inicial → Algoritmo (BFS/DFS/A*) → Planificación Final

Cumple: PEP8, SOLID, Clean Code, DRY, Type Hints, Docstrings.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from .estado import Estado
from .heuristica import calcular_heuristica, calcular_heuristica_extendida
from .algoritmos.bfs import BreadthFirstSearch
from .algoritmos.dfs import DepthFirstSearch
from .algoritmos.astar import AStarSearch

logger = logging.getLogger(__name__)

# ── Tipos válidos de algoritmo ────────────────────────────────────
TipoAlgoritmo = Literal["bfs", "dfs", "astar"]

# ── Valores por defecto para inputs vacíos ────────────────────────
AULAS_DEFAULT = [
    {"id": "A-101", "capacidad": 40, "pabellon": "A"},
    {"id": "A-102", "capacidad": 40, "pabellon": "A"},
    {"id": "B-201", "capacidad": 35, "pabellon": "B"},
    {"id": "B-202", "capacidad": 35, "pabellon": "B"},
    {"id": "C-301", "capacidad": 50, "pabellon": "C"},
    {"id": "C-302", "capacidad": 50, "pabellon": "C"},
]

HORARIOS_DEFAULT = [
    "Mañana (7:00-10:00)",
    "Mañana (10:00-13:00)",
    "Tarde (13:00-16:00)",
    "Tarde (16:00-19:00)",
    "Noche (19:00-22:00)",
]


class PlanificadorInteligente:
    """
    Motor Inteligente de Planificación basado en Espacios de Estados.

    Orquesta el proceso completo:
    1. Recibe la predicción del modelo ML
    2. Construye el Estado inicial del problema
    3. Ejecuta el algoritmo de búsqueda seleccionado
    4. Extrae la planificación óptima del resultado
    5. Devuelve un resultado completo y serializado

    Separa completamente la lógica de orquestación de los algoritmos
    de búsqueda (Separation of Concerns).
    """

    def __init__(self) -> None:
        """Inicializa los tres algoritmos disponibles."""
        self._algoritmos: dict[str, Any] = {
            "bfs":   BreadthFirstSearch(),
            "dfs":   DepthFirstSearch(),
            "astar": AStarSearch(),
        }

    def planificar(
        self,
        demanda_predicha: int,
        aulas: list[dict[str, Any]] | None = None,
        docentes_disponibles: int = 3,
        horarios: list[str] | None = None,
        algoritmo: TipoAlgoritmo = "astar",
    ) -> dict[str, Any]:
        """
        Punto de entrada principal del planificador.

        Args:
            demanda_predicha:    Número de alumnos predicho por el modelo ML.
            aulas:               Lista de aulas disponibles. Usa default si None.
            docentes_disponibles: Número de docentes disponibles para asignación.
            horarios:            Lista de turnos disponibles. Usa default si None.
            algoritmo:           "bfs", "dfs" o "astar".

        Returns:
            dict con:
                - estado_inicial: Estado de partida serializado
                - resultado_busqueda: Output completo del algoritmo
                - planificacion: Lista de asignaciones finales optimizadas
                - heuristica_diagnostico: Desglose de la heurística inicial
                - algoritmo_usado: Nombre del algoritmo
        """
        logger.info(
            "Iniciando planificación: demanda=%d, algoritmo=%s, docentes=%d",
            demanda_predicha, algoritmo, docentes_disponibles,
        )

        # ── 1. Resolver inputs ────────────────────────────────────
        aulas_validas = self._validar_aulas(aulas or AULAS_DEFAULT)
        horarios_validos = horarios or HORARIOS_DEFAULT
        demanda = max(1, int(demanda_predicha))

        # ── 2. Construir Estado Inicial ───────────────────────────
        estado_inicial = self._construir_estado_inicial(
            demanda, aulas_validas, docentes_disponibles, horarios_validos
        )

        logger.info("Estado inicial construido: %s", estado_inicial)

        # ── 3. Seleccionar y ejecutar algoritmo ───────────────────
        algoritmo_key = algoritmo.lower().strip()
        if algoritmo_key not in self._algoritmos:
            algoritmo_key = "astar"
            logger.warning("Algoritmo '%s' no válido, usando A* por defecto.", algoritmo)

        buscador = self._algoritmos[algoritmo_key]
        resultado_busqueda = buscador.buscar(estado_inicial)

        logger.info(
            "Búsqueda completada: encontrado=%s, nodos=%d, tiempo=%.1fms",
            resultado_busqueda["encontrado"],
            resultado_busqueda["estadisticas"]["nodos_expandidos"],
            resultado_busqueda["estadisticas"]["tiempo_ms"],
        )

        # ── 4. Extraer planificación del resultado ────────────────
        planificacion = self._extraer_planificacion(resultado_busqueda)

        # ── 5. Diagnóstico de heurística del estado inicial ───────
        heuristica_diag = calcular_heuristica_extendida(estado_inicial)

        return {
            "algoritmo_usado": resultado_busqueda["algoritmo"],
            "encontrado": resultado_busqueda["encontrado"],
            "razon": resultado_busqueda["razon"],
            "estado_inicial": estado_inicial.to_dict(),
            "estado_final": resultado_busqueda["estado_final"],
            "acciones": resultado_busqueda["acciones"],
            "camino": resultado_busqueda["camino"],
            "costo": resultado_busqueda["costo"],
            "estadisticas": resultado_busqueda["estadisticas"],
            "planificacion": planificacion,
            "heuristica_diagnostico": heuristica_diag,
            "metricas_precision": self._calcular_metricas_precision(
                demanda, planificacion, resultado_busqueda
            ),
        }

    # ── Métodos privados ──────────────────────────────────────────

    def _construir_estado_inicial(
        self,
        demanda: int,
        aulas: list[dict[str, Any]],
        docentes: int,
        horarios: list[str],
    ) -> Estado:
        """
        Construye el Estado inicial del problema de planificación.

        El estado inicial tiene:
        - Todos los alumnos sin asignar (alumnos_restantes = demanda_total)
        - Todas las aulas disponibles (ninguna asignada aún)
        - Costo acumulado = 0
        - Heurística calculada desde cero

        Args:
            demanda: Total de alumnos a planificar.
            aulas:   Lista de aulas disponibles.
            docentes: Número de docentes disponibles.
            horarios: Lista de turnos disponibles.

        Returns:
            Estado inicial válido y listo para la búsqueda.
        """
        estado = Estado(
            demanda_total=demanda,
            aulas_disponibles=list(aulas),
            aulas_asignadas=[],
            alumnos_restantes=demanda,
            docentes_disponibles=docentes,
            horarios_disponibles=list(horarios),
            secciones_abiertas=0,
            costo_acumulado=0.0,
            heuristica=0.0,
        )
        # Calcular heurística del estado inicial
        estado.heuristica = calcular_heuristica(estado)
        return estado

    def _validar_aulas(self, aulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Valida y normaliza la lista de aulas.
        Garantiza que cada aula tenga id, capacidad y pabellon.

        Args:
            aulas: Lista de aulas a validar.

        Returns:
            Lista de aulas con estructura garantizada.
        """
        aulas_validas = []
        for i, aula in enumerate(aulas):
            if not isinstance(aula, dict):
                continue
            capacidad = int(aula.get("capacidad", 30))
            if capacidad <= 0:
                continue
            aulas_validas.append({
                "id": str(aula.get("id", aula.get("aula_id", f"Aula-{i+1}"))),
                "capacidad": capacidad,
                "pabellon": str(aula.get("pabellon", "?")),
            })
        return aulas_validas if aulas_validas else AULAS_DEFAULT

    def _extraer_planificacion(self, resultado: dict) -> list[dict[str, Any]]:
        """
        Extrae las asignaciones del estado final del resultado de búsqueda.
        Genera la planificación óptima en formato legible para el frontend.

        Args:
            resultado: Resultado del algoritmo de búsqueda.

        Returns:
            Lista de asignaciones con sección, aula, turno, docente, ocupación.
        """
        if not resultado.get("encontrado") or not resultado.get("estado_final"):
            return []

        estado_final = resultado["estado_final"]
        aulas_asignadas = estado_final.get("aulas_asignadas", [])

        planificacion = []
        for i, asignacion in enumerate(aulas_asignadas):
            cap = asignacion.get("capacidad", 1)
            alumnos = asignacion.get("alumnos", 0)
            ocupacion = alumnos / max(cap, 1)

            planificacion.append({
                "seccion": f"S{i + 1}",
                "aula_id": asignacion.get("aula_id", f"Aula-{i+1}"),
                "pabellon": asignacion.get("pabellon", "-"),
                "turno": asignacion.get("turno", "-"),
                "docente": asignacion.get("docente", "Sin asignar"),
                "alumnos": alumnos,
                "capacidad": cap,
                "ocupacion": round(ocupacion, 4),
                "estado_ocupacion": self._clasificar_ocupacion(ocupacion),
            })

        return planificacion

    @staticmethod
    def _clasificar_ocupacion(ratio: float) -> str:
        """
        Clasifica el nivel de ocupación de un aula.
        Misma lógica que el resto del sistema para consistencia visual.

        Args:
            ratio: Fracción alumnos/capacidad.

        Returns:
            Etiqueta descriptiva del estado de ocupación.
        """
        if ratio > 1.0:   return "Excede aforo"
        if ratio >= 0.90: return "Ajustado"
        if ratio >= 0.65: return "Óptimo"
        if ratio >= 0.45: return "Baja ocupación"
        return "Subutilizado"

    @staticmethod
    def _calcular_metricas_precision(
        demanda: int,
        planificacion: list[dict[str, Any]],
        resultado_busqueda: dict,
    ) -> dict[str, Any]:
        """
        Calcula métricas de precisión adaptadas al dominio de planificación.

        Definiciones en este contexto:
          - Verdadero Positivo (TP): alumno asignado en un aula dentro del rango
            óptimo de ocupación (0.65 ≤ ratio ≤ 0.90).
          - Falso Positivo (FP): alumno asignado pero en aula sobreocupada o
            muy subutilizada (ratio < 0.45 ó ratio > 0.90).
          - Falso Negativo (FN): alumno que NO fue asignado a ninguna aula
            (sigue siendo alumnos_restantes en el estado final).

          Precision  = TP / (TP + FP)   → % de asignaciones correctamente ubicadas
          Recall     = TP / (TP + FN)   → % de alumnos cubiertos en condición óptima
          F1-Score   = 2 * P * R / (P + R)
          Accuracy   = (TP + TN) / Total  (TN = secciones cerradas correctamente)

        Args:
            demanda:          Total de alumnos a planificar.
            planificacion:    Lista de asignaciones del estado final.
            resultado_busqueda: Resultado completo del algoritmo.

        Returns:
            dict con todas las métricas de precisión y sus interpretaciones.
        """
        if not planificacion or demanda <= 0:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "accuracy": 0.0,
                "ocupacion_promedio": 0.0,
                "cobertura_alumnos_pct": 0.0,
                "secciones_optimas": 0,
                "secciones_total": 0,
                "alumnos_bien_ubicados": 0,
                "alumnos_cubiertos": 0,
                "alumnos_sin_cubrir": demanda,
                "eficiencia_busqueda": 0.0,
                "interpretaciones": {},
            }

        # ── Conteo de TP, FP, FN ───────────────────────────────────
        tp = 0  # alumnos en aulas óptimas
        fp = 0  # alumnos en aulas fuera del rango óptimo
        secciones_optimas = 0
        alumnos_cubiertos = 0
        ocupaciones = []

        for sec in planificacion:
            alumnos = sec.get("alumnos", 0)
            ocup = sec.get("ocupacion", 0.0)
            ocupaciones.append(ocup)
            alumnos_cubiertos += alumnos

            if 0.65 <= ocup <= 0.90:
                # Aula en rango óptimo → todos sus alumnos son TP
                tp += alumnos
                secciones_optimas += 1
            else:
                # Aula fuera del óptimo → sus alumnos son FP
                fp += alumnos

        # Alumnos que no quedaron asignados
        alumnos_sin_cubrir = max(0, demanda - alumnos_cubiertos)
        fn = alumnos_sin_cubrir  # no cubiertos = Falso Negativo

        # ── Cálculo de métricas ───────────────────────────────────
        precision = tp / max(tp + fp, 1)
        recall    = tp / max(tp + fn, 1)
        f1_score  = (2 * precision * recall) / max(precision + recall, 1e-9)

        # Accuracy: (asignaciones óptimas) / (total secciones)
        total_secciones = len(planificacion)
        accuracy = secciones_optimas / max(total_secciones, 1)

        # Ocupación promedio de todas las aulas
        ocup_promedio = sum(ocupaciones) / max(len(ocupaciones), 1)

        # Cobertura: % de alumnos efectivamente asignados
        cobertura_pct = (alumnos_cubiertos / max(demanda, 1)) * 100

        # Eficiencia de búsqueda: penaliza nodos expandidos vs solución encontrada
        stats = resultado_busqueda.get("estadisticas", {})
        nodos_exp = max(stats.get("nodos_expandidos", 1), 1)
        long_camino = max(stats.get("longitud_camino", 1), 1)
        eficiencia_busqueda = round(min(100.0, (long_camino / nodos_exp) * 100), 2)

        # ── Interpretaciones en lenguaje natural ────────────────────────
        def _interp_precision(v: float) -> str:
            if v >= 0.90: return "Excelente: casi todas las asignaciones están en rango óptimo."
            if v >= 0.70: return "Bueno: la mayoría de las asignaciones son correctas."
            if v >= 0.50: return "Aceptable: hay margen de mejora en las asignaciones."
            return "Bajo: muchas asignaciones están fuera del rango óptimo de ocupación."

        def _interp_recall(v: float) -> str:
            if v >= 0.90: return "Excelente: casi todos los alumnos tienen aula en condición óptima."
            if v >= 0.70: return "Bueno: la mayoría de alumnos están bien cubiertos."
            if v >= 0.50: return "Aceptable: parte de los alumnos quedan en condición suboptima."
            return "Bajo: muchos alumnos no alcanzan condición óptima de asignación."

        def _interp_f1(v: float) -> str:
            if v >= 0.90: return "F1 Óptimo: la planificación es altamente efectiva."
            if v >= 0.70: return "F1 Bueno: balance correcto entre precisión y cobertura."
            if v >= 0.50: return "F1 Aceptable: la solución es funcional pero mejorable."
            return "F1 Bajo: la planificación necesita más recursos o un algoritmo distinto."

        def _interp_eficiencia(v: float) -> str:
            if v >= 50: return "Muy eficiente: el algoritmo encontró la solución con pocos nodos."
            if v >= 20: return "Eficiente: exploración razonable del espacio de estados."
            if v >= 5:  return "Moderado: el algoritmo exploró bastantes nodos antes de resolver."
            return "Intensivo: se expandió mucho el espacio de estados; considera A* con mejor heurística."

        def _interp_cobertura(v: float) -> str:
            if v >= 99: return "Total: todos los alumnos fueron asignados."
            if v >= 90: return "Alta: casi todos los alumnos tienen aula asignada."
            if v >= 70: return "Parcial: una parte significativa de alumnos quedó sin aula."
            return "Baja: la demanda supera la capacidad disponible."

        return {
            "precision":             round(precision, 4),
            "recall":                round(recall, 4),
            "f1_score":              round(f1_score, 4),
            "accuracy":              round(accuracy, 4),
            "ocupacion_promedio":    round(ocup_promedio, 4),
            "cobertura_alumnos_pct": round(cobertura_pct, 2),
            "secciones_optimas":     secciones_optimas,
            "secciones_total":       total_secciones,
            "alumnos_bien_ubicados": tp,
            "alumnos_cubiertos":     alumnos_cubiertos,
            "alumnos_sin_cubrir":    alumnos_sin_cubrir,
            "eficiencia_busqueda":   eficiencia_busqueda,
            "verdaderos_positivos":  tp,
            "falsos_positivos":      fp,
            "falsos_negativos":      fn,
            "interpretaciones": {
                "precision":          _interp_precision(precision),
                "recall":             _interp_recall(recall),
                "f1_score":           _interp_f1(f1_score),
                "eficiencia_busqueda": _interp_eficiencia(eficiencia_busqueda),
                "cobertura":          _interp_cobertura(cobertura_pct),
            },
        }
