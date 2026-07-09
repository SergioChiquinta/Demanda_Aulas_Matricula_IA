"""
planner/operadores.py
Los 5 operadores del Motor Inteligente de Planificación.

Cada operador es una función pura que:
  - Recibe un Estado como entrada
  - Retorna un nuevo Estado (copia profunda modificada) o None si no aplica
  - NO muta el estado original (principio de inmutabilidad funcional)

Cumple: PEP8, SOLID (SRP), DRY, Clean Code, Type Hints.
"""
from __future__ import annotations

from typing import Optional

from .estado import Estado
from .heuristica import calcular_heuristica

# ── Costos de cada operador (usados como g(n) incremental) ───────
COSTO_ASIGNAR_AULA: float = 1.0
COSTO_ABRIR_SECCION: float = 1.5
COSTO_ASIGNAR_DOCENTE: float = 0.5
COSTO_CAMBIAR_HORARIO: float = 0.8
COSTO_CERRAR_SECCION: float = 0.3

# ── Ocupación objetivo y límites ─────────────────────────────────
OCUPACION_OPTIMA_MIN: float = 0.65
OCUPACION_OPTIMA_MAX: float = 0.90


def asignar_aula(estado: Estado) -> Optional[Estado]:
    """
    Operador 1: Asignar Aula.

    Toma la primera aula disponible y asigna a ella un bloque de alumnos
    proporcional a su capacidad. Reduce alumnos_restantes y mueve el aula
    de disponibles a asignadas.

    Precondición:
        - Hay al menos 1 aula disponible.
        - Hay al menos 1 alumno restante.

    Efecto:
        - aulas_disponibles pierde 1 aula.
        - aulas_asignadas gana 1 entrada con alumnos, turno y docente.
        - alumnos_restantes -= min(alumnos_restantes, capacidad_aula * 0.9)
        - secciones_abiertas += 1
        - costo_acumulado += COSTO_ASIGNAR_AULA

    Args:
        estado: Estado actual del problema.

    Returns:
        Nuevo Estado con el operador aplicado, o None si la precondición falla.
    """
    if not estado.aulas_disponibles or estado.alumnos_restantes <= 0:
        return None

    nuevo = estado.copia_profunda()

    # Tomar la primera aula disponible
    aula = nuevo.aulas_disponibles.pop(0)
    capacidad = aula.get("capacidad", 30)

    # Calcular alumnos óptimos para esta aula (respetando ocupación ideal)
    cap_optima = int(capacidad * OCUPACION_OPTIMA_MAX)
    alumnos_para_aula = min(nuevo.alumnos_restantes, max(1, cap_optima))

    # Seleccionar horario (primer disponible o el primero si no hay)
    turno = nuevo.horarios_disponibles[0] if nuevo.horarios_disponibles else "Sin turno"

    # Registrar asignación
    nuevo.aulas_asignadas.append({
        "aula_id": aula.get("id", "?"),
        "capacidad": capacidad,
        "alumnos": alumnos_para_aula,
        "turno": turno,
        "pabellon": aula.get("pabellon", "-"),
        "ocupacion": round(alumnos_para_aula / max(capacidad, 1), 4),
        "docente": None,  # se asigna con el operador asignar_docente
    })

    nuevo.alumnos_restantes -= alumnos_para_aula
    nuevo.secciones_abiertas += 1
    nuevo.costo_acumulado += COSTO_ASIGNAR_AULA
    nuevo.heuristica = calcular_heuristica(nuevo)

    return nuevo


def abrir_seccion(estado: Estado) -> Optional[Estado]:
    """
    Operador 2: Abrir Nueva Sección.

    Abre una sección adicional sin asignar aula inmediatamente.
    Útil cuando la demanda supera la capacidad de las aulas actuales.

    Precondición:
        - Hay docentes disponibles (cada sección necesita 1 docente).
        - Hay alumnos restantes.

    Efecto:
        - secciones_abiertas += 1
        - docentes_disponibles -= 1 (un docente se compromete a esta sección)
        - costo_acumulado += COSTO_ABRIR_SECCION

    Args:
        estado: Estado actual del problema.

    Returns:
        Nuevo Estado o None si la precondición falla.
    """
    if estado.docentes_disponibles <= 0 or estado.alumnos_restantes <= 0:
        return None

    nuevo = estado.copia_profunda()
    nuevo.secciones_abiertas += 1
    nuevo.docentes_disponibles -= 1
    nuevo.costo_acumulado += COSTO_ABRIR_SECCION
    nuevo.heuristica = calcular_heuristica(nuevo)

    return nuevo


def asignar_docente(estado: Estado) -> Optional[Estado]:
    """
    Operador 3: Asignar Docente a una Sección.

    Asigna un docente disponible a la última aula asignada que no tiene docente.
    Reduce el déficit docente y mejora el estado de la planificación.

    Precondición:
        - Hay docentes disponibles.
        - Hay al menos 1 aula asignada sin docente.

    Efecto:
        - docentes_disponibles -= 1
        - La última aula asignada sin docente recibe un docente.
        - costo_acumulado += COSTO_ASIGNAR_DOCENTE

    Args:
        estado: Estado actual del problema.

    Returns:
        Nuevo Estado o None si la precondición falla.
    """
    # Buscar la primera asignación sin docente
    idx_sin_docente = next(
        (i for i, a in enumerate(estado.aulas_asignadas) if a.get("docente") is None),
        None,
    )

    if estado.docentes_disponibles <= 0 or idx_sin_docente is None:
        return None

    nuevo = estado.copia_profunda()
    docente_id = f"D{estado.docentes_disponibles}"  # identificador simbólico
    nuevo.aulas_asignadas[idx_sin_docente]["docente"] = docente_id
    nuevo.docentes_disponibles -= 1
    nuevo.costo_acumulado += COSTO_ASIGNAR_DOCENTE
    nuevo.heuristica = calcular_heuristica(nuevo)

    return nuevo


def cambiar_horario(estado: Estado) -> Optional[Estado]:
    """
    Operador 4: Cambiar Horario de una Sección.

    Rota el horario asignado a la última sección usando el siguiente
    turno disponible. Resuelve conflictos de horario.

    Precondición:
        - Hay al menos 2 horarios disponibles (para tener alternativa).
        - Hay al menos 1 aula asignada.

    Efecto:
        - La última aula asignada cambia su turno al siguiente disponible.
        - El horario anterior se mueve al final de la lista (rotación circular).
        - costo_acumulado += COSTO_CAMBIAR_HORARIO

    Args:
        estado: Estado actual del problema.

    Returns:
        Nuevo Estado o None si la precondición falla.
    """
    if len(estado.horarios_disponibles) < 2 or not estado.aulas_asignadas:
        return None

    nuevo = estado.copia_profunda()

    # Rotar el primer horario al final y usar el segundo como nuevo
    horario_actual = nuevo.horarios_disponibles.pop(0)
    nuevo_turno = nuevo.horarios_disponibles[0]
    nuevo.horarios_disponibles.append(horario_actual)  # rotación circular

    # Aplicar a la última asignación
    nuevo.aulas_asignadas[-1]["turno"] = nuevo_turno
    nuevo.costo_acumulado += COSTO_CAMBIAR_HORARIO
    nuevo.heuristica = calcular_heuristica(nuevo)

    return nuevo


def cerrar_seccion(estado: Estado) -> Optional[Estado]:
    """
    Operador 5: Cerrar Sección.

    Cierra la sección con menor ocupación y redistribuye sus alumnos
    a las secciones restantes. Reduce la fragmentación.

    Precondición:
        - Hay más de 1 sección abierta (no se puede cerrar la única sección).
        - Hay al menos 2 aulas asignadas.

    Efecto:
        - La asignación con menor ocupación se elimina.
        - Sus alumnos vuelven a alumnos_restantes.
        - El aula se devuelve a aulas_disponibles.
        - secciones_abiertas -= 1
        - costo_acumulado += COSTO_CERRAR_SECCION

    Args:
        estado: Estado actual del problema.

    Returns:
        Nuevo Estado o None si la precondición falla.
    """
    if estado.secciones_abiertas <= 1 or len(estado.aulas_asignadas) < 2:
        return None

    nuevo = estado.copia_profunda()

    # Encontrar la sección con menor ocupación
    idx_menor = min(
        range(len(nuevo.aulas_asignadas)),
        key=lambda i: nuevo.aulas_asignadas[i].get("ocupacion", 1.0),
    )

    asignacion_cerrada = nuevo.aulas_asignadas.pop(idx_menor)

    # Devolver alumnos al pool de no asignados
    nuevo.alumnos_restantes += asignacion_cerrada.get("alumnos", 0)

    # Devolver aula al pool de disponibles
    nuevo.aulas_disponibles.append({
        "id": asignacion_cerrada.get("aula_id", "?"),
        "capacidad": asignacion_cerrada.get("capacidad", 30),
        "pabellon": asignacion_cerrada.get("pabellon", "-"),
    })

    nuevo.secciones_abiertas = max(0, nuevo.secciones_abiertas - 1)
    nuevo.costo_acumulado += COSTO_CERRAR_SECCION
    nuevo.heuristica = calcular_heuristica(nuevo)

    return nuevo


# ── Registro de todos los operadores ─────────────────────────────
OPERADORES: list[tuple[str, callable]] = [
    ("asignar_aula",    asignar_aula),
    ("abrir_seccion",   abrir_seccion),
    ("asignar_docente", asignar_docente),
    ("cambiar_horario", cambiar_horario),
    ("cerrar_seccion",  cerrar_seccion),
]
"""
Lista de todos los operadores disponibles, como (nombre, función).
Los algoritmos de búsqueda iteran sobre esta lista para expandir estados.
"""


def expandir_estado(estado: Estado) -> list[tuple[str, Estado]]:
    """
    Genera todos los estados sucesores válidos aplicando cada operador.

    Args:
        estado: Estado a expandir.

    Returns:
        Lista de tuplas (nombre_accion, nuevo_estado) con solo los
        sucesores válidos (donde el operador tuvo precondiciones satisfechas).
    """
    sucesores: list[tuple[str, Estado]] = []
    for nombre, operador in OPERADORES:
        resultado = operador(estado)
        if resultado is not None and resultado.es_valido():
            sucesores.append((nombre, resultado))
    return sucesores
