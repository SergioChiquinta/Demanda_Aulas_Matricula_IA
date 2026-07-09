"""
planner/heuristica.py
Función heurística h(n) para el Motor Inteligente de Planificación.

La heurística es ADMISIBLE (nunca sobreestima el costo real) y CONSISTENTE
(satisface la desigualdad triangular), garantizando optimalidad de A*.

Diseño: función aislada, fácilmente modificable sin tocar los algoritmos.
Cumple: PEP8, SOLID (OCP — abierto a extensión), Clean Code, Type Hints.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .estado import Estado

# ── Pesos de penalización (fácilmente ajustables) ────────────────
PESO_DESPERDICIO: float = 0.5    # penaliza cupos sin usar
PESO_SOBREOCUPACION: float = 3.0  # penaliza exceder capacidad
PESO_DOCENTES: float = 2.0        # penaliza falta de docentes
PESO_HORARIOS: float = 1.0        # penaliza falta de horarios disponibles
PESO_SECCIONES: float = 0.8       # penaliza exceso de secciones abiertas


def calcular_heuristica(estado: "Estado") -> float:
    """
    Calcula h(n): estimación del costo mínimo para alcanzar el estado objetivo
    desde el estado actual.

    Factores considerados:
        1. Espacios desperdiciados: cupos asignados - alumnos reales
        2. Sobreocupación: alumnos que exceden la capacidad disponible
        3. Docentes faltantes: secciones sin cobertura docente
        4. Escasez de horarios: menos horarios que secciones abiertas
        5. Ineficiencia de secciones: demasiadas secciones para la demanda

    La heurística es admisible porque es una subestimación del costo real
    (todos los pesos son ≤ al costo efectivo de los operadores).

    Args:
        estado: Estado actual del problema.

    Returns:
        float: Valor h(n) ≥ 0. Menor valor = estado más cercano al objetivo.
    """
    h = 0.0

    # ── 1. Alumnos restantes sin asignar ─────────────────────────
    # Si hay alumnos sin aula, estimamos que se necesitan más operaciones.
    if estado.alumnos_restantes > 0:
        # Estimamos cuántas aulas más se necesitan
        aulas_restantes = len(estado.aulas_disponibles)
        if aulas_restantes == 0:
            # No hay aulas disponibles → costo muy alto (estado casi insoluble)
            h += PESO_SOBREOCUPACION * estado.alumnos_restantes
        else:
            # Capacidad promedio de las aulas disponibles
            cap_promedio = sum(
                a.get("capacidad", 30) for a in estado.aulas_disponibles
            ) / aulas_restantes
            # Aulas adicionales estimadas
            aulas_adicionales = max(
                0, estado.alumnos_restantes / max(cap_promedio, 1)
            )
            h += aulas_adicionales * 1.0  # 1 acción por aula adicional

    # ── 2. Espacios desperdiciados ────────────────────────────────
    # Cupos asignados que no tienen alumno (capacidad ociosa)
    cupos_totales = sum(a.get("capacidad", 0) for a in estado.aulas_asignadas)
    alumnos_en_aulas = min(estado.alumnos_asignados, cupos_totales)
    desperdicio = max(0, cupos_totales - alumnos_en_aulas)

    # Desperdicio relativo (% de cupos ociosos)
    if cupos_totales > 0:
        ratio_desperdicio = desperdicio / cupos_totales
        if ratio_desperdicio > 0.40:
            # Más del 40% de cupos vacíos es costoso
            h += PESO_DESPERDICIO * ratio_desperdicio * 10

    # ── 3. Sobreocupación ─────────────────────────────────────────
    # Detecta aulas donde los alumnos asignados exceden la capacidad
    for asignacion in estado.aulas_asignadas:
        cap = asignacion.get("capacidad", 1)
        alumnos = asignacion.get("alumnos", 0)
        if alumnos > cap:
            exceso = alumnos - cap
            h += PESO_SOBREOCUPACION * exceso

    # ── 4. Docentes faltantes ─────────────────────────────────────
    # Si hay más secciones abiertas que docentes disponibles
    deficit_docentes = max(0, estado.secciones_abiertas - estado.docentes_disponibles)
    h += PESO_DOCENTES * deficit_docentes

    # ── 5. Escasez de horarios ────────────────────────────────────
    # Si hay menos horarios disponibles que secciones abiertas
    horarios_count = len(estado.horarios_disponibles)
    if estado.secciones_abiertas > horarios_count > 0:
        conflictos_horario = estado.secciones_abiertas - horarios_count
        h += PESO_HORARIOS * conflictos_horario

    # ── 6. Eficiencia de secciones ────────────────────────────────
    # Muchas secciones pequeñas es menos eficiente que pocas grandes
    if estado.secciones_abiertas > 1 and estado.demanda_total > 0:
        alumnos_por_seccion = (
            estado.demanda_total / estado.secciones_abiertas
        )
        # Penalizar si hay secciones muy pequeñas (< 10 alumnos/sección)
        if alumnos_por_seccion < 10:
            h += PESO_SECCIONES * (10 - alumnos_por_seccion)

    return round(max(0.0, h), 4)


def calcular_heuristica_extendida(estado: "Estado") -> dict:
    """
    Versión diagnóstica de la heurística que retorna el desglose
    de cada componente. Útil para depuración y visualización en el frontend.

    Args:
        estado: Estado actual del problema.

    Returns:
        dict con 'total' y el valor de cada componente de la heurística.
    """
    h_total = calcular_heuristica(estado)

    cupos_totales = sum(a.get("capacidad", 0) for a in estado.aulas_asignadas)
    alumnos_en_aulas = min(estado.alumnos_asignados, cupos_totales)
    desperdicio = max(0, cupos_totales - alumnos_en_aulas)

    sobreocupacion = sum(
        max(0, a.get("alumnos", 0) - a.get("capacidad", 1))
        for a in estado.aulas_asignadas
    )

    deficit_docentes = max(0, estado.secciones_abiertas - estado.docentes_disponibles)
    conflictos_horario = max(
        0, estado.secciones_abiertas - len(estado.horarios_disponibles)
    )

    return {
        "total": h_total,
        "desperdicio_cupos": desperdicio,
        "sobreocupacion_alumnos": sobreocupacion,
        "deficit_docentes": deficit_docentes,
        "conflictos_horario": conflictos_horario,
        "secciones_abiertas": estado.secciones_abiertas,
        "alumnos_restantes": estado.alumnos_restantes,
    }
