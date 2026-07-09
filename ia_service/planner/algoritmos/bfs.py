"""
planner/algoritmos/bfs.py
Breadth-First Search (BFS) — Búsqueda en Anchura.

Garantiza encontrar el camino más CORTO (menor número de pasos),
pero no necesariamente el de menor costo cuando los costos varían.

Propiedades:
  - Completo: Sí (si la solución existe y el espacio es finito).
  - Óptimo en número de pasos: Sí.
  - Complejidad tiempo: O(b^d) donde b=factor de ramificación, d=profundidad.
  - Complejidad espacio: O(b^d) — mantiene toda la frontera en memoria.

Cumple: PEP8, SOLID (SRP), Clean Code, Type Hints.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Optional

from ..estado import Estado
from ..nodo import Nodo
from ..operadores import expandir_estado

# ── Parámetros de control ─────────────────────────────────────────
MAX_NODOS_BFS: int = 800       # límite de nodos generados
MAX_PROFUNDIDAD_BFS: int = 12  # límite de profundidad de búsqueda


class BreadthFirstSearch:
    """
    Algoritmo BFS para el Motor Inteligente de Planificación.

    Explora el árbol de búsqueda nivel a nivel usando una cola FIFO.
    El primer nodo objetivo encontrado garantiza la solución de menor
    número de pasos (no necesariamente menor costo).

    Usage:
        bfs = BreadthFirstSearch()
        resultado = bfs.buscar(estado_inicial)
    """

    def __init__(
        self,
        max_nodos: int = MAX_NODOS_BFS,
        max_profundidad: int = MAX_PROFUNDIDAD_BFS,
    ) -> None:
        """
        Args:
            max_nodos:       Límite de nodos generados antes de abortar.
            max_profundidad: Límite de profundidad del árbol.
        """
        self.max_nodos = max_nodos
        self.max_profundidad = max_profundidad

        # ── Estadísticas internas ─────────────────────────────────
        self._nodos_expandidos: int = 0
        self._nodos_generados: int = 0
        self._tiempo_inicio: float = 0.0

    def buscar(self, estado_inicial: Estado) -> dict:
        """
        Ejecuta BFS desde el estado inicial hasta encontrar el objetivo
        o agotar los recursos de búsqueda.

        Args:
            estado_inicial: Estado de partida del problema.

        Returns:
            dict con:
                - "encontrado" (bool): si se halló solución
                - "camino" (list[dict]): secuencia de nodos del camino
                - "acciones" (list[str]): operadores aplicados en orden
                - "estado_inicial" (dict): estado de partida serializado
                - "estado_final" (dict): estado objetivo serializado (o None)
                - "costo" (float): costo total del camino encontrado
                - "estadisticas" (dict): métricas del proceso de búsqueda
        """
        self._tiempo_inicio = time.perf_counter()
        self._nodos_expandidos = 0
        self._nodos_generados = 1  # contamos el nodo raíz

        # ── Nodo raíz ─────────────────────────────────────────────
        nodo_raiz = Nodo(
            estado=estado_inicial,
            padre=None,
            accion=None,
            profundidad=0,
            costo=estado_inicial.costo_acumulado,
            heuristica=estado_inicial.heuristica,
        )

        # ── Verificar si ya es objetivo ───────────────────────────
        if estado_inicial.es_objetivo():
            return self._construir_resultado(nodo_raiz, encontrado=True)

        # ── Estructuras de BFS ────────────────────────────────────
        frontera: deque[Nodo] = deque([nodo_raiz])
        visitados: set[int] = {hash(estado_inicial)}

        # ── Bucle principal ───────────────────────────────────────
        while frontera:
            # Revisar límite de nodos
            if self._nodos_generados >= self.max_nodos:
                return self._construir_resultado(None, encontrado=False,
                                                  razon="Límite de nodos alcanzado")

            nodo_actual = frontera.popleft()
            self._nodos_expandidos += 1

            # Verificar límite de profundidad
            if nodo_actual.profundidad >= self.max_profundidad:
                continue

            # Expandir el nodo actual
            sucesores = expandir_estado(nodo_actual.estado)

            for nombre_accion, estado_sucesor in sucesores:
                self._nodos_generados += 1
                hash_estado = hash(estado_sucesor)

                if hash_estado in visitados:
                    continue

                visitados.add(hash_estado)

                nodo_sucesor = Nodo(
                    estado=estado_sucesor,
                    padre=nodo_actual,
                    accion=nombre_accion,
                    profundidad=nodo_actual.profundidad + 1,
                    costo=estado_sucesor.costo_acumulado,
                    heuristica=estado_sucesor.heuristica,
                )

                # ── Test de objetivo ──────────────────────────────
                if estado_sucesor.es_objetivo():
                    return self._construir_resultado(nodo_sucesor, encontrado=True)

                frontera.append(nodo_sucesor)

        # Frontera agotada sin encontrar solución
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

        Args:
            nodo_final: Nodo objetivo (o None si no se encontró).
            encontrado: True si se encontró una solución.
            razon:      Mensaje descriptivo del resultado.

        Returns:
            dict estandarizado listo para serializar a JSON.
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
            "algoritmo": "BFS",
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
