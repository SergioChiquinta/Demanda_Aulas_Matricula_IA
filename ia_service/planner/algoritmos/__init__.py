"""
planner/algoritmos/__init__.py
Subpaquete de algoritmos de búsqueda desacoplados.

Expone:
  - BreadthFirstSearch
  - DepthFirstSearch
  - AStarSearch
"""
from .bfs import BreadthFirstSearch
from .dfs import DepthFirstSearch
from .astar import AStarSearch

__all__ = ["BreadthFirstSearch", "DepthFirstSearch", "AStarSearch"]
