# Demanda Aulas Matricula IA

Colores:
ROJO_UTP = "#8B0000"
ROJO = "#D32F2F"
NEGRO = "#1C1C1C"
GRIS = "#F5F5F5"
BLANCO = "#FFFFFF"

El Excel `data_prediccion_aulas.xlsx` se reemplaza por una base de datos MySQL local llamada `demanda_aulas_matricula_ia`.

La app sigue trabajando con un `DataFrame` llamado `self.df`; la diferencia es que ahora `cargar_datos()` obtiene los datos desde la vista SQL `vw_dataset_prediccion_aulas` en lugar de leer el Excel.

## Archivos importantes

- `demanda_aulas_matricula_ia.sql`: crea la BD, tablas relacionadas, inserta los 1200 registros y crea la vista compatible con la app.
- `demanda_aulas_matricula_IA.py`: en su versión adaptada de la app para leer desde MySQL local.

## Estructura relacional

- `periodos`: periodos académicos.
- `cursos`: datos del curso. Se conserva `codigo_curso_fuente` porque el Excel original repite `id_curso` con distintos nombres.
- `docentes`: docentes de la muestra.
- `aulas`: datos físicos de aula. Se usa una clave interna porque el Excel original repite `aula_id` con distintas capacidades/pabellones.
- `horarios`: turnos/secciones.
- `demanda_matricula`: tabla central con demanda, matrícula y variables predictoras.
- `vw_dataset_prediccion_aulas`: vista que reconstruye las columnas originales del Excel.

## Pasos en XAMPP/phpMyAdmin

1. Abre XAMPP.
2. Inicia `Apache` y `MySQL`.
3. Entra a `http://localhost/phpmyadmin`.
4. Ve a la pestaña `Importar`.
5. Selecciona `demanda_aulas_matricula_ia.sql`.
6. Ejecuta la importación.
7. Al final debe aparecer `total_registros = 1200`, si es así, todo se importó correctamente.

## Instalación de dependencia Python

Ejecuta en la terminal del proyecto:

```bash
pip install mysql-connector-python
```

También puedes reinstalar todo así:

```bash
pip install pandas numpy scikit-learn matplotlib seaborn openpyxl tkintertable mysql-connector-python
```

## Ejecución

Copia `demanda_aulas_matricula_IA.py` en tu ruta del proyecto:

```text
C:\Ruta_Elegida\Demanda_Aulas_Matrícula_IA
```

Luego ejecútalo:

```bash
python demanda_aulas_matricula_IA.py
```

## Configuración si tu MySQL tiene contraseña

En `demanda_aulas_matricula_IA.py`, cambia:

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "demanda_aulas_matricula_ia",
}
```

Si configuraste contraseña en XAMPP, colócala en el campo `password`.
