"""
planner/algoritmos/dfs.py
Depth-First Search (DFS) — Búsqueda en Profundidad.

Explora primero el camino más profundo antes de retroceder.
Usa menos memoria que BFS pero no garantiza optimalidad.
Implementado con límite de profundidad para evitar ciclos infinitos.

Propiedades:
  - Completo: Solo si el espacio es finito y hay límite de profundidad.
  - Óptimo: No (puede encontrar soluciones subóptimas).
  - Complejidad tiempo: O(b^m) donde m = profundidad máxima.
  - Complejidad espacio: O(b*m) — solo el camino actual en memoria.

Cumple: PEP8, SOLID (SRP), Clean Code, Type Hints.
"""
from __future__ import annotations

import time
from typing import Optional

from ..estado import Estado
from ..nodo import Nodo
from ..operadores import expandir_estado

# ── Parámetros de control ─────────────────────────────────────────
MAX_NODOS_DFS: int = 800       # límite de nodos generados
MAX_PROFUNDIDAD_DFS: int = 15  # DFS puede ir más profundo que BFS


class DepthFirstSearch:
    """
    Algoritmo DFS para el Motor Inteligente de Planificación.

    Explora el árbol usando una pila LIFO (stack). El DFS tiende a encontrar
    una solución rápidamente pero no garantiza que sea la óptima.
    Con límite de profundidad se comporta como DLS (Depth-Limited Search).

    Usage:
        dfs = DepthFirstSearch()
        resultado = dfs.buscar(estado_inicial)
    """

    def __init__(
        self,
        max_nodos: int = MAX_NODOS_DFS,
        max_profundidad: int = MAX_PROFUNDIDAD_DFS,
    ) -> None:
        """
        Args:
            max_nodos:       Límite de nodos generados antes de abortar.
            max_profundidad: Límite de profundidad del árbol (DLS).
        """
        self.max_nodos = max_nodos
        self.max_profundidad = max_profundidad

        self._nodos_expandidos: int = 0
        self._nodos_generados: int = 0
        self._tiempo_inicio: float = 0.0

    def buscar(self, estado_inicial: Estado) -> dict:
        """
        Ejecuta DFS desde el estado inicial hasta encontrar el objetivo
        o agotar los recursos de búsqueda.

        Args:
            estado_inicial: Estado de partida del problema.

        Returns:
            dict estandarizado con camino, acciones, costo y estadísticas.
        """
        self._tiempo_inicio = time.perf_counter()
        self._nodos_expandidos = 0
        self._nodos_generados = 1

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

        # ── Stack LIFO para DFS ───────────────────────────────────
        pila: list[Nodo] = [nodo_raiz]
        visitados: set[int] = {hash(estado_inicial)}

        # ── Bucle principal ───────────────────────────────────────
        while pila:
            if self._nodos_generados >= self.max_nodos:
                return self._construir_resultado(None, encontrado=False,
                                                  razon="Límite de nodos alcanzado")

            nodo_actual = pila.pop()  # LIFO — diferencia clave vs BFS
            self._nodos_expandidos += 1

            if nodo_actual.profundidad >= self.max_profundidad:
                continue

            sucesores = expandir_estado(nodo_actual.estado)

            # DFS apila en orden inverso para explorar el primero primero
            for nombre_accion, estado_sucesor in reversed(sucesores):
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

                if estado_sucesor.es_objetivo():
                    return self._construir_resultado(nodo_sucesor, encontrado=True)

                pila.append(nodo_sucesor)

        return self._construir_resultado(None, encontrado=False,
                                          razon="Pila agotada sin solución")

    def _construir_resultado(
        self,
        nodo_final: Optional[Nodo],
        encontrado: bool,
        razon: str = "Solución encontrada",
    ) -> dict:
        """
        Construye el diccionario de resultado estandarizado.
        Mismo formato que BFS y A* para uniformidad en el frontend.
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
            "algoritmo": "DFS",
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
