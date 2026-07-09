"""
planner/algoritmos/astar.py
A* Search — Búsqueda Heurística Óptima.

Combina el costo real g(n) con la estimación heurística h(n):
    f(n) = g(n) + h(n)

Con una heurística admisible y consistente, A* garantiza encontrar
el camino de MENOR COSTO de forma completa y óptima.

Propiedades:
  - Completo: Sí.
  - Óptimo en costo: Sí (con heurística admisible).
  - Complejidad tiempo: O(b^d) en el peor caso, mejor en práctica.
  - Complejidad espacio: O(b^d) — mantiene todos los nodos en memoria.

Implementación: heapq (min-heap) como PriorityQueue eficiente.

Cumple: PEP8, SOLID (SRP), Clean Code, Type Hints.
"""
from __future__ import annotations

import heapq
import time
from typing import Optional

from ..estado import Estado
from ..nodo import Nodo
from ..operadores import expandir_estado

# ── Parámetros de control ─────────────────────────────────────────
MAX_NODOS_ASTAR: int = 1000    # A* puede explorar más con buena heurística
MAX_PROFUNDIDAD_ASTAR: int = 20


class AStarSearch:
    """
    Algoritmo A* para el Motor Inteligente de Planificación.

    Usa una cola de prioridad (min-heap) ordenada por f(n) = g(n) + h(n).
    La heurística admisible de heuristica.py garantiza optimalidad.

    El contador `_contador` rompe empates en el heap cuando dos nodos
    tienen el mismo f(n), usando FIFO como desempate.

    Usage:
        astar = AStarSearch()
        resultado = astar.buscar(estado_inicial)
    """

    def __init__(
        self,
        max_nodos: int = MAX_NODOS_ASTAR,
        max_profundidad: int = MAX_PROFUNDIDAD_ASTAR,
    ) -> None:
        """
        Args:
            max_nodos:       Límite de nodos generados antes de abortar.
            max_profundidad: Límite de profundidad del árbol.
        """
        self.max_nodos = max_nodos
        self.max_profundidad = max_profundidad

        self._nodos_expandidos: int = 0
        self._nodos_generados: int = 0
        self._tiempo_inicio: float = 0.0
        self._contador: int = 0  # desempate FIFO en el heap

    def buscar(self, estado_inicial: Estado) -> dict:
        """
        Ejecuta A* desde el estado inicial hasta encontrar el camino
        de menor costo al objetivo.

        Args:
            estado_inicial: Estado de partida del problema.

        Returns:
            dict estandarizado con camino óptimo, acciones y estadísticas.
        """
        self._tiempo_inicio = time.perf_counter()
        self._nodos_expandidos = 0
        self._nodos_generados = 1
        self._contador = 0

        # ── Nodo raíz ─────────────────────────────────────────────
        nodo_raiz = Nodo(
            estado=estado_inicial,
            padre=None,
            accion=None,
            profundidad=0,
            costo=estado_inicial.costo_acumulado,
            heuristica=estado_inicial.heuristica,
        )

        if estado_inicial.es_objetivo():
            return self._construir_resultado(nodo_raiz, encontrado=True)

        # ── PriorityQueue (min-heap) ──────────────────────────────
        # Tupla: (f(n), contador_desempate, nodo)
        frontera: list[tuple[float, int, Nodo]] = []
        heapq.heappush(frontera, (nodo_raiz.f, self._contador, nodo_raiz))
        self._contador += 1

        # ── Conjuntos de control ──────────────────────────────────
        # explorados: estados ya expandidos (no se re-expanden)
        explorados: set[int] = set()
        # mejor_costo: para cada estado, el menor g(n) visto hasta ahora
        mejor_costo: dict[int, float] = {hash(estado_inicial): 0.0}

        # ── Bucle principal ───────────────────────────────────────
        while frontera:
            if self._nodos_generados >= self.max_nodos:
                return self._construir_resultado(None, encontrado=False,
                                                  razon="Límite de nodos alcanzado")

            # Extraer el nodo con menor f(n)
            _, _, nodo_actual = heapq.heappop(frontera)
            hash_actual = hash(nodo_actual.estado)

            # Evitar re-expandir estados ya explorados
            if hash_actual in explorados:
                continue

            explorados.add(hash_actual)
            self._nodos_expandidos += 1

            # ── Test de objetivo ──────────────────────────────────
            if nodo_actual.estado.es_objetivo():
                return self._construir_resultado(nodo_actual, encontrado=True)

            if nodo_actual.profundidad >= self.max_profundidad:
                continue

            # ── Expandir sucesores ────────────────────────────────
            sucesores = expandir_estado(nodo_actual.estado)

            for nombre_accion, estado_sucesor in sucesores:
                self._nodos_generados += 1
                hash_sucesor = hash(estado_sucesor)

                if hash_sucesor in explorados:
                    continue

                nuevo_costo = estado_sucesor.costo_acumulado

                # Solo agregar si encontramos un camino más barato a este estado
                if hash_sucesor in mejor_costo and nuevo_costo >= mejor_costo[hash_sucesor]:
                    continue

                mejor_costo[hash_sucesor] = nuevo_costo

                nodo_sucesor = Nodo(
                    estado=estado_sucesor,
                    padre=nodo_actual,
                    accion=nombre_accion,
                    profundidad=nodo_actual.profundidad + 1,
                    costo=nuevo_costo,
                    heuristica=estado_sucesor.heuristica,
                )

                heapq.heappush(
                    frontera,
                    (nodo_sucesor.f, self._contador, nodo_sucesor)
                )
                self._contador += 1

        return self._construir_resultado(None, encontrado=False,
                                          razon="Frontera agotada sin solución")

    def _construir_resultado(
        self,
        nodo_final: Optional[Nodo],
        encontrado: bool,
        razon: str = "Solución encontrada",
    ) -> dict:
        """
        Construye el diccionario de resultado estandarizado.
        Mismo formato que BFS y DFS para uniformidad en el frontend.
        """
        tiempo_ms = round((time.perf_counter() - self._tiempo_inicio) * 1000, 2)

        if encontrado and nodo_final is not None:
            camino = nodo_final.reconstruir_camino()
            acciones = nodo_final.obtener_acciones()
            estado_final_dict = nodo_final.estado.to_dict()
            costo_final = nodo_final.costo
            profundidad_final = nodo_final.profundidad
            camino_serializado = [n.to_dict() for n in camino]
        else:
            camino_serializado = []
            acciones = []
            estado_final_dict = None
            costo_final = 0.0
            profundidad_final = 0

        return {
            "algoritmo": "A*",
            "encontrado": encontrado,
            "razon": razon,
            "camino": camino_serializado,
            "acciones": acciones,
            "estado_final": estado_final_dict,
            "costo": round(costo_final, 4),
            "estadisticas": {
                "tiempo_ms": tiempo_ms,
                "nodos_expandidos": self._nodos_expandidos,
                "nodos_generados": self._nodos_generados,
                "profundidad": profundidad_final,
                "longitud_camino": len(acciones),
                "max_nodos_config": self.max_nodos,
                "max_profundidad_config": self.max_profundidad,
            },
        }
