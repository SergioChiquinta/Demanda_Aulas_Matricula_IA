"""
planner/estado.py
Clase Estado — representación completa del espacio de estados del problema
de asignación de aulas.

Principios: OOP, inmutabilidad mediante copias profundas, serialización completa.
Cumple: PEP8, SOLID (SRP), Clean Code, Type Hints.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Estado:
    """
    Representación de un estado en el espacio de estados del problema
    de planificación de aulas.

    Attributes:
        demanda_total:       Número total de alumnos a asignar (constante).
        aulas_disponibles:   Lista de aulas aún no asignadas.
                             Cada aula: {"id": str, "capacidad": int, "pabellon": str}
        aulas_asignadas:     Lista de asignaciones ya realizadas.
                             Cada asignación: {"aula_id", "capacidad", "alumnos", "turno", "docente"}
        alumnos_restantes:   Alumnos que aún no tienen aula asignada.
        docentes_disponibles: Número de docentes aún sin asignar a sección.
        horarios_disponibles: Lista de turnos disponibles (strings, e.g. "Mañana").
        secciones_abiertas:  Número de secciones actualmente abiertas.
        costo_acumulado:     g(n) — costo total desde el estado inicial.
        heuristica:          h(n) — estimación calculada por heuristica.py.
    """

    demanda_total: int
    aulas_disponibles: list[dict[str, Any]]
    aulas_asignadas: list[dict[str, Any]]
    alumnos_restantes: int
    docentes_disponibles: int
    horarios_disponibles: list[str]
    secciones_abiertas: int
    costo_acumulado: float
    heuristica: float = 0.0

    # ── Propiedad derivada ───────────────────────────────────────
    @property
    def f(self) -> float:
        """f(n) = g(n) + h(n). Valor de evaluación para A*."""
        return self.costo_acumulado + self.heuristica

    @property
    def alumnos_asignados(self) -> int:
        """Número de alumnos que ya tienen aula asignada."""
        return self.demanda_total - self.alumnos_restantes

    @property
    def cupos_totales_asignados(self) -> int:
        """Suma de capacidades de las aulas ya asignadas."""
        return sum(a.get("capacidad", 0) for a in self.aulas_asignadas)

    # ── Copia profunda ───────────────────────────────────────────
    def copia_profunda(self) -> "Estado":
        """
        Retorna una copia independiente del estado actual.
        Garantiza que los operadores no muten el estado original (inmutabilidad funcional).
        """
        return Estado(
            demanda_total=self.demanda_total,
            aulas_disponibles=copy.deepcopy(self.aulas_disponibles),
            aulas_asignadas=copy.deepcopy(self.aulas_asignadas),
            alumnos_restantes=self.alumnos_restantes,
            docentes_disponibles=self.docentes_disponibles,
            horarios_disponibles=list(self.horarios_disponibles),
            secciones_abiertas=self.secciones_abiertas,
            costo_acumulado=self.costo_acumulado,
            heuristica=self.heuristica,
        )

    # ── Comparación e identidad ──────────────────────────────────
    def __eq__(self, otro: object) -> bool:
        """
        Dos estados son iguales si tienen las mismas asignaciones realizadas
        y los mismos alumnos restantes. Permite detectar estados duplicados.
        """
        if not isinstance(otro, Estado):
            return False
        return (
            self.alumnos_restantes == otro.alumnos_restantes
            and self.secciones_abiertas == otro.secciones_abiertas
            and self.docentes_disponibles == otro.docentes_disponibles
            and len(self.aulas_asignadas) == len(otro.aulas_asignadas)
        )

    def __hash__(self) -> int:
        """
        Hash basado en características clave para uso en sets/dicts.
        Permite al BFS y A* detectar estados ya visitados.
        """
        return hash((
            self.alumnos_restantes,
            self.secciones_abiertas,
            self.docentes_disponibles,
            len(self.aulas_asignadas),
        ))

    # ── Serialización ────────────────────────────────────────────
    def to_dict(self) -> dict[str, Any]:
        """
        Serializa el estado a un diccionario JSON-compatible.
        Usado por el planificador para devolver resultados al frontend.
        """
        return {
            "demanda_total": self.demanda_total,
            "alumnos_restantes": self.alumnos_restantes,
            "alumnos_asignados": self.alumnos_asignados,
            "secciones_abiertas": self.secciones_abiertas,
            "docentes_disponibles": self.docentes_disponibles,
            "aulas_disponibles_count": len(self.aulas_disponibles),
            "horarios_disponibles": list(self.horarios_disponibles),
            "aulas_asignadas": copy.deepcopy(self.aulas_asignadas),
            "cupos_totales": self.cupos_totales_asignados,
            "costo_acumulado": round(self.costo_acumulado, 4),
            "heuristica": round(self.heuristica, 4),
            "f": round(self.f, 4),
        }

    # ── Validaciones ─────────────────────────────────────────────
    def es_valido(self) -> bool:
        """
        Verifica que el estado sea internamente consistente.
        Un estado inválido no debe expandirse.
        """
        if self.demanda_total <= 0:
            return False
        if self.alumnos_restantes < 0:
            return False
        if self.secciones_abiertas < 0:
            return False
        if self.docentes_disponibles < 0:
            return False
        return True

    def es_objetivo(self) -> bool:
        """
        Test de meta: todos los alumnos tienen aula asignada
        y no hay déficit de docentes crítico.
        """
        return self.alumnos_restantes <= 0

    # ── Representación legible ───────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"Estado(demanda={self.demanda_total}, restantes={self.alumnos_restantes}, "
            f"secciones={self.secciones_abiertas}, docentes={self.docentes_disponibles}, "
            f"asignaciones={len(self.aulas_asignadas)}, g={self.costo_acumulado:.2f}, "
            f"h={self.heuristica:.2f}, f={self.f:.2f})"
        )
