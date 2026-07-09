"""
planner/nodo.py
Clase Nodo — envuelve un Estado en el árbol de búsqueda.

Contiene toda la información necesaria para reconstruir el camino
desde el estado inicial hasta el estado objetivo.

Cumple: PEP8, SOLID (SRP), Clean Code, Type Hints.
"""
from __future__ import annotations

from typing import Optional

from .estado import Estado


class Nodo:
    """
    Nodo del árbol de búsqueda.

    Encapsula un Estado y agrega la información contextual necesaria
    para los algoritmos de búsqueda: padre, acción aplicada, profundidad,
    costo real g(n) y estimación heurística h(n).

    Attributes:
        estado:     Estado del problema que este nodo representa.
        padre:      Nodo padre (None si es el nodo raíz).
        accion:     Nombre de la acción/operador que generó este nodo.
        profundidad: Nivel en el árbol (0 = raíz).
        costo:      g(n) — costo acumulado desde la raíz hasta este nodo.
        heuristica: h(n) — estimación al objetivo desde este estado.
    """

    def __init__(
        self,
        estado: Estado,
        padre: Optional["Nodo"] = None,
        accion: Optional[str] = None,
        profundidad: int = 0,
        costo: float = 0.0,
        heuristica: float = 0.0,
    ) -> None:
        self.estado: Estado = estado
        self.padre: Optional["Nodo"] = padre
        self.accion: Optional[str] = accion
        self.profundidad: int = profundidad
        self.costo: float = costo
        self.heuristica: float = heuristica

    # ── Valor de evaluación para A* ──────────────────────────────
    @property
    def f(self) -> float:
        """f(n) = g(n) + h(n). Usado por A* para ordenar la cola de prioridad."""
        return self.costo + self.heuristica

    # ── Comparación para PriorityQueue ────────────────────────────
    def __lt__(self, otro: "Nodo") -> bool:
        """
        Permite comparar nodos en la cola de prioridad de A*.
        Nodos con menor f(n) tienen mayor prioridad.
        """
        return self.f < otro.f

    def __le__(self, otro: "Nodo") -> bool:
        return self.f <= otro.f

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Nodo):
            return False
        return self.estado == otro.estado

    def __hash__(self) -> int:
        return hash(self.estado)

    # ── Reconstrucción del camino ─────────────────────────────────
    def reconstruir_camino(self) -> list["Nodo"]:
        """
        Recorre la cadena de padres desde este nodo hasta la raíz
        y devuelve el camino como lista ordenada [raíz → objetivo].

        Returns:
            Lista de nodos desde el estado inicial al estado actual.
        """
        camino: list[Nodo] = []
        nodo_actual: Optional[Nodo] = self
        while nodo_actual is not None:
            camino.append(nodo_actual)
            nodo_actual = nodo_actual.padre
        camino.reverse()
        return camino

    def obtener_acciones(self) -> list[str]:
        """
        Devuelve la secuencia de acciones aplicadas desde la raíz
        hasta este nodo, en orden cronológico.

        Returns:
            Lista de strings con nombres de operadores aplicados.
        """
        acciones: list[str] = []
        nodo_actual: Optional[Nodo] = self
        while nodo_actual is not None and nodo_actual.accion is not None:
            acciones.append(nodo_actual.accion)
            nodo_actual = nodo_actual.padre
        acciones.reverse()
        return acciones

    # ── Serialización ────────────────────────────────────────────
    def to_dict(self) -> dict:
        """
        Serializa el nodo a diccionario JSON-compatible.
        Incluye el estado, la acción que lo generó y métricas del nodo.
        """
        return {
            "profundidad": self.profundidad,
            "costo": round(self.costo, 4),
            "heuristica": round(self.heuristica, 4),
            "f": round(self.f, 4),
            "accion": self.accion,
            "estado": self.estado.to_dict(),
        }

    # ── Representación legible ────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"Nodo(accion='{self.accion}', prof={self.profundidad}, "
            f"g={self.costo:.2f}, h={self.heuristica:.2f}, f={self.f:.2f})"
        )
