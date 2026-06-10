import pandas as pd
import mysql.connector
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error
import random
import time

# ==============================
# PALETA DE COLORES UTP & DISEÑO
# ==============================
ROJO_UTP = "#8B0000"
ROJO_CLARO = "#D32F2F"
NEGRO = "#1C1C1C"
GRIS_FONDO = "#EAEAEA"
BLANCO = "#FFFFFF"
GRIS_TEXTO = "#424242"
FUENTE_TITULO = ("Segoe UI", 24, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 14, "bold")
FUENTE_NORMAL = ("Segoe UI", 11)

# Colores específicos para los Clusters (Consistentes con la interpretación)
COLOR_SUBUTILIZADO = "#FFD700"  # Dorado/Amarillo
COLOR_OPTIMO = "#2E7D32"        # Verde
COLOR_SOBREPOBLADO = "#D32F2F"  # Rojo

# ==============================
# CONFIGURACIÓN DE BASE DE DATOS LOCAL MYSQL/XAMPP
# ==============================
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "demanda_aulas_matricula_ia",
    "charset": "utf8mb4",
    "use_pure": True,
}

COLUMNAS_DATASET = [
    "periodo",
    "id_curso",
    "nombre_curso",
    "ciclo_relativo",
    "creditos_curso",
    "docente_id",
    "docente_disponible",
    "aula_id",
    "capacidad_aula",
    "pabellon",
    "horario_seccion",
    "alumnos_nuevos",
    "alumnos_prerrequisito",
    "alumnos_repitentes",
    "veces_llevado",
    "carga_academica_proyectada",
    "cursos_comun",
    "duracion_semanas",
    "laboratorio",
    "tiempo_matricula_min",
    "alumnos_matriculados",
]

COLUMNAS_NUMERICAS = [
    "id_curso",
    "ciclo_relativo",
    "creditos_curso",
    "docente_id",
    "docente_disponible",
    "aula_id",
    "capacidad_aula",
    "alumnos_nuevos",
    "alumnos_prerrequisito",
    "alumnos_repitentes",
    "veces_llevado",
    "carga_academica_proyectada",
    "cursos_comun",
    "duracion_semanas",
    "laboratorio",
    "tiempo_matricula_min",
    "alumnos_matriculados",
]

# ==============================
# CARGA Y PREPARACIÓN DE DATOS
# ==============================
def cargar_datos():
    """Carga el dataset desde MySQL local manteniendo las mismas columnas del Excel."""
    conexion = None
    cursor = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)

        columnas_sql = ", ".join(COLUMNAS_DATASET)
        consulta = f"""
            SELECT {columnas_sql}
            FROM vw_dataset_prediccion_aulas
            ORDER BY id_registro
        """
        cursor.execute(consulta)
        filas = cursor.fetchall()

        df = pd.DataFrame(filas, columns=COLUMNAS_DATASET)
        if df.empty:
            messagebox.showerror(
                "Error",
                "La base de datos no devolvió registros. Verifica que importaste el script SQL."
            )
            return pd.DataFrame()

        for columna in COLUMNAS_NUMERICAS:
            df[columna] = pd.to_numeric(df[columna], errors="coerce")

        if df[COLUMNAS_NUMERICAS].isnull().any().any():
            raise ValueError("Existen valores numéricos vacíos o inválidos en la vista SQL.")

        df[COLUMNAS_NUMERICAS] = df[COLUMNAS_NUMERICAS].astype(int)
        return df

    except Exception as e:
        messagebox.showerror(
            "Error de conexión BD",
            "No se pudo cargar el dataset desde MySQL."
            "Verifica que Apache/MySQL estén activos en XAMPP, que la BD exista "
            "y que el usuario/contraseña de DB_CONFIG sean correctos."
            f"Detalle técnico: {e}"
        )
        return pd.DataFrame()

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()

def preparar_datos(df):
    # Variables predictoras alineadas a los requerimientos del proyecto
    X = df[[
        "alumnos_nuevos",
        "alumnos_prerrequisito",
        "alumnos_repitentes",
        "docente_disponible",
        "capacidad_aula",
        "duracion_semanas",
        "laboratorio"
    ]]
    y = df["alumnos_matriculados"]
    return X, y

def entrenar_modelos(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Se utiliza Regresión Lineal y Ridge (penalización) para predicción continua pura
    modelos = {
        "Regresión Lineal Múltiple": LinearRegression(),
        "Regresión Ridge": Ridge(alpha=1.0)
    }
    resultados = {}
    
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        prediccion = modelo.predict(X_test)
        resultados[nombre] = {
            "modelo": modelo,
            "MAE": mean_absolute_error(y_test, prediccion),
            "RMSE": np.sqrt(mean_squared_error(y_test, prediccion))
        }
    return resultados

# ==============================
# ALGORITMO GENÉTICO (METAHEURÍSTICA)
# ==============================
class OptimizadorGenetico:
    def __init__(self, aulas, horarios, secciones, tam_poblacion=80, generaciones=100, tasa_cruce=0.8, tasa_mutacion=0.1):
        self.aulas = aulas
        self.horarios = horarios
        self.secciones = secciones
        self.tam_poblacion = tam_poblacion
        self.generaciones = generaciones
        self.tasa_cruce = tasa_cruce
        self.tasa_mutacion = tasa_mutacion
        
        self.num_aulas = len(aulas)
        self.num_horarios = len(horarios)
        self.num_genes = len(secciones)
        
        # Mapeo de índices a (aula, horario)
        self.espacio_soluciones = []
        for i_aula in range(self.num_aulas):
            for i_horario in range(self.num_horarios):
                self.espacio_soluciones.append((i_aula, i_horario))
                
        self.tam_espacio = len(self.espacio_soluciones)
        self.mejor_cromosoma = None
        self.mejor_conflictos = []

    def calcular_fitness(self, cromosoma):
        penalizacion = 0
        conflictos = []
        
        colisiones_aulas = {}
        colisiones_docentes = {}
        
        for i_sec, gen in enumerate(cromosoma):
            i_aula, i_horario = self.espacio_soluciones[gen]
            aula = self.aulas[i_aula]
            horario = self.horarios[i_horario]
            seccion = self.secciones[i_sec]
            
            # 1. Colisión de Aula (Dura)
            clave_aula = (i_aula, i_horario)
            if clave_aula not in colisiones_aulas:
                colisiones_aulas[clave_aula] = []
            colisiones_aulas[clave_aula].append(i_sec)
            
            # 2. Colisión de Docente (Dura)
            docente_id = seccion['docente_id']
            clave_docente = (docente_id, i_horario)
            if clave_docente not in colisiones_docentes:
                colisiones_docentes[clave_docente] = []
            colisiones_docentes[clave_docente].append(i_sec)
            
            # 3. Capacidad de Aula (Dura / Blanda)
            factor_lab = 0.85 if seccion['laboratorio'] == 1 else 1.0
            capacidad_efectiva = int(aula['capacidad_aula'] * factor_lab)
            
            if seccion['demanda'] > capacidad_efectiva:
                sobrecupo = seccion['demanda'] - capacidad_efectiva
                penalizacion += 500 + sobrecupo * 10
                conflictos.append(f"Sección {seccion['seccion_id']} ({seccion['curso']}) excede cap. de {aula['aula_id']} ({seccion['demanda']}>{capacidad_efectiva})")
            else:
                desperdicio = capacidad_efectiva - seccion['demanda']
                penalizacion += desperdicio * 1.5
                
            # 4. Compatibilidad de Laboratorios (Dura)
            if seccion['laboratorio'] == 1 and aula['pabellon'] != 'C':
                penalizacion += 400
                conflictos.append(f"Sección {seccion['seccion_id']} ({seccion['curso']}) requiere Lab (Pabellón C), asignada en {aula['pabellon']}")
                
            # 5. Coincidencia de Turno (Blanda)
            if horario['turno'].lower() != seccion['turno_preferido'].lower():
                penalizacion += 100
                
        # Procesar colisiones
        for clave, indices in colisiones_aulas.items():
            if len(indices) > 1:
                colisiones_en_aula = len(indices) - 1
                penalizacion += colisiones_en_aula * 1000
                aula_id = self.aulas[clave[0]]['aula_id']
                horario_str = f"{self.horarios[clave[1]]['dia']} {self.horarios[clave[1]]['turno']}"
                conflictos.append(f"Conflicto Aula: {len(indices)} secciones compitiendo por Aula {aula_id} en {horario_str}")
                
        for clave, indices in colisiones_docentes.items():
            if len(indices) > 1:
                colisiones_de_docente = len(indices) - 1
                penalizacion += colisiones_de_docente * 1000
                doc_id = clave[0]
                horario_str = f"{self.horarios[clave[1]]['dia']} {self.horarios[clave[1]]['turno']}"
                conflictos.append(f"Conflicto Docente: Docente ID {doc_id} asignado a {len(indices)} secciones en {horario_str}")
                
        fitness = 1.0 / (1.0 + penalizacion)
        return fitness, conflictos

    def inicializar_poblacion(self):
        poblacion = []
        for _ in range(self.tam_poblacion):
            individuo = [random.randint(0, self.tam_espacio - 1) for _ in range(self.num_genes)]
            poblacion.append(individuo)
        return poblacion

    def seleccion_torneo(self, poblacion, fitness_list, k=3):
        seleccionados = []
        for _ in range(len(poblacion)):
            aspirantes = random.sample(list(zip(poblacion, fitness_list)), k)
            ganador = max(aspirantes, key=lambda x: x[1])[0]
            seleccionados.append(list(ganador))
        return seleccionados

    def cruzar(self, padre1, padre2):
        if random.random() < self.tasa_cruce and self.num_genes > 1:
            punto = random.randint(1, self.num_genes - 1)
            hijo1 = padre1[:punto] + padre2[punto:]
            hijo2 = padre2[:punto] + padre1[punto:]
            return hijo1, hijo2
        return list(padre1), list(padre2)

    def mutar(self, individuo):
        for i in range(self.num_genes):
            if random.random() < self.tasa_mutacion:
                individuo[i] = random.randint(0, self.tam_espacio - 1)
        return individuo

    def optimizar(self):
        poblacion = self.inicializar_poblacion()
        mejor_historico_fitness = -1.0
        mejor_historico_cromosoma = None
        mejor_historico_conflictos = []
        
        for gen_idx in range(self.generaciones):
            fitness_conflictos = [self.calcular_fitness(ind) for ind in poblacion]
            fitness_list = [fc[0] for fc in fitness_conflictos]
            
            mejor_idx = np.argmax(fitness_list)
            mejor_fitness = fitness_list[mejor_idx]
            mejor_cromosoma = poblacion[mejor_idx]
            conflictos_mejor = fitness_conflictos[mejor_idx][1]
            
            if mejor_fitness > mejor_historico_fitness:
                mejor_historico_fitness = mejor_fitness
                mejor_historico_cromosoma = list(mejor_cromosoma)
                mejor_historico_conflictos = conflictos_mejor
                
                self.mejor_cromosoma = mejor_historico_cromosoma
                self.mejor_conflictos = mejor_historico_conflictos
                
            yield gen_idx, mejor_fitness, mejor_historico_fitness, mejor_historico_cromosoma, mejor_historico_conflictos
            
            padres = self.seleccion_torneo(poblacion, fitness_list)
            
            nueva_poblacion = []
            # Elitismo: conservar los 2 mejores
            indices_ordenados = np.argsort(fitness_list)[::-1]
            nueva_poblacion.append(list(poblacion[indices_ordenados[0]]))
            if len(poblacion) > 1:
                nueva_poblacion.append(list(poblacion[indices_ordenados[1]]))
                
            while len(nueva_poblacion) < self.tam_poblacion:
                p1 = random.choice(padres)
                p2 = random.choice(padres)
                h1, h2 = self.cruzar(p1, p2)
                h1 = self.mutar(h1)
                h2 = self.mutar(h2)
                nueva_poblacion.append(h1)
                if len(nueva_poblacion) < self.tam_poblacion:
                    nueva_poblacion.append(h2)
                    
            poblacion = nueva_poblacion

import random

# ==============================
# APLICACIÓN PRINCIPAL
# ==============================
class AppDemandaAulas:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Predictivo de Demanda de Aulas - Gestión Académica")
        self.root.geometry("1920x1080")
        self.root.state('zoomed') # Maximizar ventana
        self.root.configure(bg=GRIS_FONDO)

        self.df = cargar_datos()
        if self.df.empty: return
        
        self.X, self.y = preparar_datos(self.df)
        self.modelos = entrenar_modelos(self.X, self.y)
        self.modelo_activo = self.modelos["Regresión Lineal Múltiple"]["modelo"]

        self.crear_menu_lateral()
        self.contenedor_principal = tk.Frame(self.root, bg=GRIS_FONDO)
        self.contenedor_principal.pack(side="right", fill="both", expand=True)
        
        self.vista_dashboard()

    # ==============================
    # NAVEGACIÓN
    # ==============================
    def crear_menu_lateral(self):
        menu = tk.Frame(self.root, bg=NEGRO, width=250)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        tk.Label(menu, text="MENÚ\nADMINISTRATIVO", font=("Segoe UI", 16, "bold"), 
                 bg=NEGRO, fg=BLANCO, pady=30).pack()

        botones = [
            ("📊 Dashboard Resumen", self.vista_dashboard),
            ("📈 Análisis de Aforos", self.vista_analisis),
            ("🤖 Simulación IA", self.vista_simulacion),
            ("🗓 Horarios Distribuidos", self.vista_horarios_distribuidos)
        ]

        for texto, comando in botones:
            btn = tk.Button(menu, text=texto, font=FUENTE_SUBTITULO, bg=ROJO_UTP, fg=BLANCO,
                            activebackground=ROJO_CLARO, activeforeground=BLANCO,
                            bd=0, pady=15, cursor="hand2", command=comando)
            btn.pack(fill="x", padx=10, pady=10)

    def limpiar_contenedor(self):
        for widget in self.contenedor_principal.winfo_children():
            widget.destroy()

    # ==============================
    # 1. VISTA: DASHBOARD
    # ==============================
    def vista_dashboard(self):
        self.limpiar_contenedor()
        
        titulo = tk.Label(self.contenedor_principal, text="Resumen General Académico", 
                          font=FUENTE_TITULO, bg=GRIS_FONDO, fg=NEGRO)
        titulo.pack(pady=20, anchor="w", padx=40)

        # KPIs (Tarjetas)
        frame_kpis = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        frame_kpis.pack(fill="x", padx=40, pady=10)

        mae_actual = self.modelos["Regresión Lineal Múltiple"]["MAE"]
        rmse_actual = self.modelos["Regresión Lineal Múltiple"]["RMSE"]
        total_alumnos = self.df['alumnos_matriculados'].sum()
        aforo_promedio = self.df['capacidad_aula'].mean()

        self.crear_tarjeta(frame_kpis, "Total Matrículas (Histórico)", f"{total_alumnos:,}")
        self.crear_tarjeta(frame_kpis, "Aforo Promedio por Aula", f"{aforo_promedio:.0f} alumnos")
        self.crear_tarjeta(frame_kpis, "Margen de Error (MAE)", f"± {mae_actual:.2f} alumnos")
        self.crear_tarjeta(frame_kpis, "Penalización Error (RMSE)", f"{rmse_actual:.2f}")

        # --- TABLA CON SCROLLBAR HORIZONTAL ---
        frame_tabla = tk.Frame(self.contenedor_principal, bg=BLANCO, bd=1, relief="solid")
        frame_tabla.pack(fill="both", expand=True, padx=40, pady=20)
        
        tk.Label(frame_tabla, text="Últimos Registros Históricos", 
                 font=FUENTE_SUBTITULO, bg=BLANCO).pack(anchor="w", padx=20, pady=10)

        columnas_admin = ["periodo", "nombre_curso", "pabellon", "horario_seccion", 
                          "capacidad_aula", "alumnos_matriculados"]
        
        # Crear scrollbar horizontal
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal")
        
        # Crear Treeview vinculado a la scrollbar
        tree = ttk.Treeview(frame_tabla, columns=columnas_admin, show="headings", 
                            height=15, xscrollcommand=scroll_x.set)
        
        scroll_x.config(command=tree.xview)
        
        # Empaquetar: Primero el Treeview, luego la barra abajo
        tree.pack(fill="both", expand=True, padx=20, pady=(10, 0))
        scroll_x.pack(fill="x", padx=20, pady=(0, 10))

        encabezados = ["Periodo", "Asignatura", "Pabellón", "Turno", "Capacidad Física", "Matriculados Reales"]
        for col, encabezado in zip(columnas_admin, encabezados):
            tree.heading(col, text=encabezado)
            # Ajustamos un ancho mínimo para forzar que aparezca el scroll si la ventana es pequeña
            tree.column(col, anchor="center", width=150) 

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background=ROJO_UTP, foreground=NEGRO)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)

        for _, row in self.df[columnas_admin].head(100).iterrows():
            tree.insert("", "end", values=list(row))

    def crear_tarjeta(self, parent, titulo, valor):
        card = tk.Frame(parent, bg=BLANCO, bd=1, relief="solid", width=300, height=120)
        card.pack(side="left", padx=15, expand=True, fill="both")
        card.pack_propagate(False)
        tk.Label(card, text=titulo, font=("Segoe UI", 12), bg=BLANCO, fg=GRIS_TEXTO).pack(pady=(20, 5))
        tk.Label(card, text=valor, font=("Segoe UI", 20, "bold"), bg=BLANCO, fg=ROJO_UTP).pack()

    # ==============================
    # 2. VISTA: ANÁLISIS
    # ==============================
    def vista_analisis(self):
        self.limpiar_contenedor()

        header_frame = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        header_frame.pack(fill="x", pady=20, padx=40)

        tk.Label(header_frame, text="Análisis de Eficiencia de Infraestructura",
                 font=FUENTE_TITULO, bg=GRIS_FONDO, fg=NEGRO).pack(side="left")

        self.mostrar_info = False
        self.btn_toggle = tk.Button(header_frame, text="Ver Interpretación 📝", font=FUENTE_NORMAL,
                                    bg=ROJO_UTP, fg=BLANCO, bd=0, padx=20, cursor="hand2",
                                    command=self.toggle_interpretacion)
        self.btn_toggle.pack(side="right")

        self.frame_contenido_analisis = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        self.frame_contenido_analisis.pack(fill="both", expand=True, padx=40, pady=10)

        # Variables numéricas aptas para clustering (se excluyen categóricas)
        vars_numericas = [
            "alumnos_matriculados", "capacidad_aula", "carga_academica_proyectada",
            "creditos_curso", "alumnos_repitentes", "tiempo_matricula_min",
            "alumnos_nuevos", "veces_llevado"
        ]
        self.vars_disponibles = [v for v in vars_numericas if v in self.df.columns]

        # Panel de controles: Comboboxes para selección dinámica de variables X e Y
        panel_controles = tk.Frame(self.frame_contenido_analisis, bg=GRIS_FONDO)
        panel_controles.pack(fill="x", pady=(0, 10))

        tk.Label(panel_controles, text="Variable X:", font=FUENTE_NORMAL,
                 bg=GRIS_FONDO, fg=NEGRO).pack(side="left", padx=(0, 5))
        self.combo_x = ttk.Combobox(panel_controles, values=self.vars_disponibles,
                                    state="readonly", width=25)
        self.combo_x.set("alumnos_matriculados" if "alumnos_matriculados" in self.vars_disponibles
                         else self.vars_disponibles[0])
        self.combo_x.pack(side="left", padx=(0, 20))

        tk.Label(panel_controles, text="Variable Y:", font=FUENTE_NORMAL,
                 bg=GRIS_FONDO, fg=NEGRO).pack(side="left", padx=(0, 5))
        self.combo_y = ttk.Combobox(panel_controles, values=self.vars_disponibles,
                                    state="readonly", width=25)
        self.combo_y.set("capacidad_aula" if "capacidad_aula" in self.vars_disponibles
                         else self.vars_disponibles[1])
        self.combo_y.pack(side="left", padx=(0, 20))

        # Actualización automática al cambiar cualquier variable
        self.combo_x.bind("<<ComboboxSelected>>", lambda _: self._actualizar_analisis())
        self.combo_y.bind("<<ComboboxSelected>>", lambda _: self._actualizar_analisis())

        tk.Button(panel_controles, text="Actualizar Análisis 🔄", font=FUENTE_NORMAL,
                  bg=ROJO_UTP, fg=BLANCO, bd=0, padx=15, cursor="hand2",
                  command=self._actualizar_analisis).pack(side="left")

        self.panel_grafico = tk.Frame(self.frame_contenido_analisis, bg=GRIS_FONDO)
        self.panel_grafico.pack(fill="both", expand=True)

        # Panel de interpretación: se crea aquí pero se muestra solo con el toggle
        self.panel_info = tk.Frame(self.frame_contenido_analisis, bg=BLANCO, bd=2, relief="ridge")

        # Ejecutar análisis inicial con los valores por defecto
        self._actualizar_analisis()

    def _actualizar_analisis(self):
        """Ejecuta el pipeline completo con K=3 fijo cada vez que cambian los Combobox.

        K=3 es una decisión de dominio administrativo: la infraestructura académica
        tiene exactamente 3 estados operativos relevantes y excluyentes:
          • Subutilización  — capacidad ociosa, costo operativo innecesario
          • Eficiencia       — ocupación equilibrada, uso ideal del activo
          • Hacinamiento    — demanda ≥ capacidad, riesgo académico y de seguridad

        El método del codo y el silhouette score se usan únicamente como herramientas
        de VALIDACIÓN para confirmar que K=3 es razonable con los datos seleccionados.
        """
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score

        K = 3  # Valor de diseño administrativo — fijo por definición del modelo

        var_x = self.combo_x.get()
        var_y = self.combo_y.get()

        if var_x == var_y:
            messagebox.showwarning("Variables iguales",
                                   "Selecciona variables distintas para X e Y.")
            return
        if var_x not in self.df.columns or var_y not in self.df.columns:
            messagebox.showerror("Error de datos",
                                 f"Columna no encontrada: '{var_x}' o '{var_y}'.")
            return

        # Selección EXPLÍCITA por nombre — ningún ciclo anterior puede influir
        datos = self.df[[var_x, var_y]].dropna()
        if len(datos) < 9:
            messagebox.showerror("Datos insuficientes",
                                 "Se necesitan al menos 9 filas válidas para el clustering.")
            return

        # Array 2-D fresco — columna 0 = var_x, columna 1 = var_y
        X_raw = datos[[var_x, var_y]].values

        # DEBUG: verifica en consola que el pipeline usa las variables correctas
        print(f"\n{'='*60}")
        print(f"[ANALISIS] var_x={var_x!r}  var_y={var_y!r}")
        print(f"[ANALISIS] Filas válidas : {len(X_raw)}")
        print(f"[ANALISIS] Rango {var_x}: [{X_raw[:,0].min():.2f}, {X_raw[:,0].max():.2f}]")
        print(f"[ANALISIS] Rango {var_y}: [{X_raw[:,1].min():.2f}, {X_raw[:,1].max():.2f}]")

        # StandardScaler: normaliza var_x y var_y a media=0, std=1.
        # Necesario porque KMeans usa distancias euclidianas; sin normalizar, la variable
        # con mayor rango dominaría la geometría del clustering.
        scaler   = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)

        # Inercias sobre datos CRUDOS para el gráfico del codo.
        # Al usar X_raw (no X_scaled), el eje Y refleja la escala real de cada variable:
        # "capacidad_aula" (rango ~200) produce inercias en miles,
        # "veces_llevado" (rango ~10) las produce en decenas — curvas visualmente distintas.
        inercias = []
        for k in range(1, 11):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            km.fit(X_raw)
            inercias.append(km.inertia_)

        print(f"[ANALISIS] Inercias K=1..10: {[round(v, 1) for v in inercias]}")
        print(f"[ANALISIS] Inercia en K=3  : {inercias[2]:,.1f}")

        # KMeans con K=3 sobre datos normalizados
        # n_init=10: 10 inicializaciones distintas, conserva la de menor inercia
        # random_state=42: semilla fija para reproducibilidad exacta
        kmeans           = KMeans(n_clusters=K, n_init=10, random_state=42)
        labels           = kmeans.fit_predict(X_scaled)
        centroids_scaled = kmeans.cluster_centers_
        centroids_real   = scaler.inverse_transform(centroids_scaled)

        # Silhouette Score: valida la calidad del agrupamiento K=3 en los datos actuales
        try:
            sil_score = silhouette_score(X_scaled, labels)
        except Exception:
            sil_score = 0.0

        print(f"[ANALISIS] Silhouette Score: {sil_score:.4f}")

        interp_sil = ("Excelente" if sil_score > 0.7 else
                      "Bueno"     if sil_score > 0.5 else
                      "Aceptable" if sil_score > 0.25 else "Débil")

        cluster_roles = self._asignar_roles_clusters(centroids_real, var_x, var_y)

        self.df['cluster'] = -1
        self.df.loc[datos.index, 'cluster'] = labels

        # Cerrar figura anterior para liberar estado interno de matplotlib
        fig_prev = getattr(self, '_fig_analisis', None)
        if fig_prev is not None:
            plt.close(fig_prev)

        for widget in self.panel_grafico.winfo_children():
            widget.destroy()

        # Figura completamente nueva en cada ejecución
        self._fig_analisis, (ax_scatter, ax_codo) = plt.subplots(1, 2, figsize=(14, 5))
        self._fig_analisis.patch.set_facecolor(GRIS_FONDO)

        colores_fijos = {
            "subutilizado": COLOR_SUBUTILIZADO,
            "optimo":       COLOR_OPTIMO,
            "sobrepoblado": COLOR_SOBREPOBLADO
        }

        # Scatter con valores REALES para que los ejes sean legibles
        for cid in range(K):
            rol   = cluster_roles.get(cid, "optimo")
            color = colores_fijos[rol]
            mask  = labels == cid
            ax_scatter.scatter(X_raw[mask, 0], X_raw[mask, 1],
                               c=color, alpha=0.7, edgecolors='w', s=80,
                               label=f"Cluster {cid}")

        ax_scatter.set_title(f"K=3: {var_x} vs {var_y}", fontsize=13, pad=15)
        ax_scatter.set_xlabel(var_x.replace("_", " ").title(), fontsize=11)
        ax_scatter.set_ylabel(var_y.replace("_", " ").title(), fontsize=11)
        ax_scatter.legend(fontsize=9)
        ax_scatter.grid(True, linestyle="--", alpha=0.6)
        ax_scatter.set_facecolor("#F9F9F9")
        ax_scatter.annotate(f"Silhouette: {sil_score:.3f} — {interp_sil}",
                            xy=(0.02, 0.97), xycoords="axes fraction",
                            fontsize=9, va="top",
                            bbox=dict(boxstyle="round,pad=0.3", fc=BLANCO, alpha=0.85))

        # ── Gráfico del codo (validación visual de K=3) ──────────────────────
        # La curva usa inercias sobre X_raw: el eje Y cambia con cada par de
        # variables, evidenciando que el recálculo es real.
        ax_codo.plot(range(1, 11), inercias, "o-",
                     color=ROJO_UTP, linewidth=2, markersize=6, zorder=3,
                     label="Inercia por K")

        # Marcador prominente en K=3
        val_k3 = inercias[2]
        ax_codo.scatter([3], [val_k3], s=280, color=COLOR_OPTIMO,
                        zorder=5, marker='*')

        # Línea vertical fija en K=3
        ax_codo.axvline(x=3, color=COLOR_OPTIMO, linestyle="--",
                        alpha=0.75, linewidth=1.8)

        # Zona sombreada de retornos decrecientes (K > 3)
        ax_codo.axvspan(3.5, 10.5, alpha=0.07, color=GRIS_TEXTO)
        ax_codo.text(3.7, inercias[0] * 0.97,
                     "retornos\ndecrecientes", fontsize=7.5,
                     color=GRIS_TEXTO, va="top", style="italic")

        # Anotación con justificación administrativa de K=3
        y_rango = inercias[0] - inercias[-1]
        ann_y   = inercias[-1] + y_rango * 0.55
        ax_codo.annotate(
            f"K=3 (modelo administrativo)\nInercia: {val_k3:,.0f}",
            xy=(3, val_k3),
            xytext=(4.4, ann_y),
            fontsize=8.5, color=COLOR_OPTIMO, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLOR_OPTIMO, lw=1.5),
            bbox=dict(boxstyle="round,pad=0.4", fc=BLANCO,
                      ec=COLOR_OPTIMO, alpha=0.92)
        )

        # Eje secundario: mejora marginal por K (barras %)
        # Verde para K≤3 (zona útil), gris para K>3 (retornos decrecientes)
        gains   = np.abs(np.diff(inercias))
        rel_pct = gains / (inercias[0] + 1e-9) * 100
        bar_cols = [COLOR_OPTIMO if k <= 3 else "#BDBDBD" for k in range(2, 11)]
        ax_r = ax_codo.twinx()
        ax_r.bar(range(2, 11), rel_pct, alpha=0.28, color=bar_cols,
                 width=0.55, zorder=2)
        ax_r.set_ylabel("Mejora marginal (%)", fontsize=9, color=GRIS_TEXTO)
        ax_r.tick_params(axis="y", labelcolor=GRIS_TEXTO, labelsize=8)
        for k_bar, pct, col in zip(range(2, 11), rel_pct, bar_cols):
            if pct > 2:
                ax_r.text(k_bar, pct + 0.3, f"{pct:.0f}%",
                          ha="center", va="bottom", fontsize=7,
                          color=col, fontweight="bold")

        ax_codo.set_title("Método del Codo — Validación de K=3", fontsize=13, pad=15)
        ax_codo.set_xlabel("Número de Clusters (K)", fontsize=11)
        lbl_x = var_x.replace("_", " ")[:14]
        lbl_y = var_y.replace("_", " ")[:14]
        ax_codo.set_ylabel(f"Inercia  [{lbl_x} + {lbl_y}]", fontsize=9)
        ax_codo.legend(fontsize=8, loc="upper right")
        ax_codo.grid(True, linestyle="--", alpha=0.5, zorder=1)
        ax_codo.set_facecolor("#F9F9F9")
        ax_codo.set_xticks(range(1, 11))

        plt.tight_layout(pad=2.0)

        canvas = FigureCanvasTkAgg(self._fig_analisis, master=self.panel_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self._construir_panel_info(cluster_roles, centroids_real, var_x, var_y,
                                   sil_score, interp_sil)

    def _asignar_roles_clusters(self, centroids_real, var_x, var_y):
        """Asigna el rol semántico de cada uno de los 3 clusters según centroides reales.

        K=3 siempre produce exactamente: subutilizado / optimo / sobrepoblado.
        Con variables alumnos vs capacidad usa el ratio de ocupación (demanda/oferta).
        Con cualquier otro par ordena por magnitud del centroide en var_x.
        """
        usa_ratio = ("alumno" in var_x.lower() and "capacidad" in var_y.lower())

        if usa_ratio:
            # Mayor ratio → mayor ocupación relativa → mayor riesgo de hacinamiento
            pares = [(i, c[0] / c[1] if c[1] > 0 else float("inf"))
                     for i, c in enumerate(centroids_real)]
        else:
            pares = [(i, c[0]) for i, c in enumerate(centroids_real)]

        pares.sort(key=lambda x: x[1])
        return {
            pares[0][0]: "subutilizado",
            pares[1][0]: "optimo",
            pares[2][0]: "sobrepoblado"
        }

    def _construir_panel_info(self, cluster_roles, centroids_real, var_x, var_y,
                               sil_score, interp_sil):
        """Reconstruye el panel de interpretación con descripciones dinámicas."""
        for widget in self.panel_info.winfo_children():
            widget.destroy()

        tk.Label(self.panel_info, text="Interpretación Administrativa de Datos",
                 font=FUENTE_SUBTITULO, bg=BLANCO, fg=ROJO_UTP).pack(pady=(20, 5))

        tk.Label(self.panel_info,
                 text=(f"K = 3  (modelo administrativo: Subutilización / Eficiencia / Hacinamiento)"
                       f"   |   Silhouette: {sil_score:.3f}  →  {interp_sil}"),
                 font=("Segoe UI", 11, "italic"), bg=BLANCO, fg=GRIS_TEXTO).pack(pady=(0, 15))

        frame_detalles = tk.Frame(self.panel_info, bg=BLANCO)
        frame_detalles.pack(padx=50, fill="both")

        plantillas = {
            "subutilizado": {
                "emoji": "🟡", "titulo": "Subutilización Crítica", "color": COLOR_SUBUTILIZADO,
                "desc": ("Aulas con capacidad muy superior a la demanda real.\n"
                         "Centroide → {vx}: {cx:.1f} | {vy}: {cy:.1f}\n"
                         "Impacto: Costo operativo innecesario en energía y mantenimiento.\n"
                         "Recomendación: Mover a pabellones menores o reasignar secciones.")
            },
            "optimo": {
                "emoji": "🟢", "titulo": "Eficiencia Operativa", "color": COLOR_OPTIMO,
                "desc": ("Aulas con relación de ocupación equilibrada y saludable.\n"
                         "Centroide → {vx}: {cx:.1f} | {vy}: {cy:.1f}\n"
                         "Impacto: Uso ideal del activo físico.\n"
                         "Recomendación: Escalar este modelo a otras sedes.")
            },
            "sobrepoblado": {
                "emoji": "🔴", "titulo": "Riesgo de Hacinamiento", "color": COLOR_SOBREPOBLADO,
                "desc": ("La demanda iguala o supera la capacidad física del aula.\n"
                         "Centroide → {vx}: {cx:.1f} | {vy}: {cy:.1f}\n"
                         "Impacto: Deterioro de la calidad académica y riesgo de seguridad.\n"
                         "Recomendación: División inmediata de secciones.")
            }
        }

        vx = var_x.replace("_", " ")
        vy = var_y.replace("_", " ")

        for cluster_id, rol in sorted(cluster_roles.items()):
            p    = plantillas[rol]
            cx   = centroids_real[cluster_id][0]
            cy   = centroids_real[cluster_id][1]
            desc = p["desc"].format(vx=vx, cx=cx, vy=vy, cy=cy)
            tk.Label(frame_detalles,
                     text=f"{p['emoji']} Cluster {cluster_id}: {p['titulo']}",
                     font=("Segoe UI", 13, "bold"), fg=p["color"], bg=BLANCO
                     ).pack(anchor="w", pady=(10, 0))
            tk.Label(frame_detalles, text=desc, font=("Segoe UI", 12),
                     fg=GRIS_TEXTO, bg=BLANCO, wraplength=700, justify="left"
                     ).pack(anchor="w", padx=20, pady=(0, 10))

    def toggle_interpretacion(self):
        if not self.mostrar_info:
            self.panel_grafico.pack_forget()
            self.panel_info.pack(fill="both", expand=True, pady=20)
            self.btn_toggle.config(text="Ver Gráfico 📊")
            self.mostrar_info = True
        else:
            self.panel_info.pack_forget()
            self.panel_grafico.pack(fill="both", expand=True)
            self.btn_toggle.config(text="Ver Interpretación 📝")
            self.mostrar_info = False

    # ==============================
    # 3. VISTA: SIMULACIÓN
    # ==============================
    def vista_simulacion(self):
        """Vista profesional para simular demanda, aforo, secciones y recursos.

        Ajuste visual:
        - El formulario izquierdo ahora tiene scroll vertical.
        - El panel de resultados usa un layout vertical responsivo.
        - La guía de variables también tiene scroll.
        - El gráfico y la tabla ya no compiten horizontalmente por espacio.
        """
        self.limpiar_contenedor()

        # =========================
        # HEADER
        # =========================
        header = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        header.pack(fill="x", pady=(18, 5), padx=28)

        titulo_header = tk.Label(
            header,
            text="Simulador Predictivo de Carga de Aulas",
            font=("Segoe UI", 22, "bold"),
            bg=GRIS_FONDO,
            fg=NEGRO
        )
        titulo_header.pack(side="left", fill="x", expand=True, anchor="w")

        acciones = tk.Frame(header, bg=GRIS_FONDO)
        acciones.pack(side="right", anchor="e")

        self.btn_guia = tk.Button(
            acciones,
            text="Guía de Variables 📘",
            font=FUENTE_NORMAL,
            bg=ROJO_UTP,
            fg=BLANCO,
            activebackground=ROJO_CLARO,
            activeforeground=BLANCO,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.toggle_guia_simulacion
        )
        self.btn_guia.pack(side="left", padx=5)

        self.btn_detalles = tk.Button(
            acciones,
            text="Informe Detallado 📄",
            font=FUENTE_NORMAL,
            bg=NEGRO,
            fg=BLANCO,
            activebackground=GRIS_TEXTO,
            activeforeground=BLANCO,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.toggle_detalles
        )
        self.btn_detalles.pack(side="left", padx=5)

        subtitulo = tk.Label(
            self.contenedor_principal,
            text="Evalúa demanda estimada, capacidad efectiva, secciones necesarias, ocupación y disponibilidad docente.",
            font=("Segoe UI", 10),
            bg=GRIS_FONDO,
            fg=GRIS_TEXTO
        )
        subtitulo.pack(anchor="w", padx=30, pady=(0, 8))

        # =========================
        # CONTENEDOR GENERAL RESPONSIVO
        # =========================
        cuerpo = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        cuerpo.columnconfigure(0, weight=0, minsize=410)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        # =========================
        # PANEL IZQUIERDO: FORMULARIO CON SCROLL
        # =========================
        f_form_outer = tk.LabelFrame(
            cuerpo,
            text="Parámetros del escenario",
            font=FUENTE_SUBTITULO,
            bg=BLANCO,
            fg=NEGRO,
            padx=6,
            pady=6
        )
        f_form_outer.grid(row=0, column=0, sticky="ns", padx=(0, 18), pady=4)
        f_form_outer.grid_propagate(False)
        f_form_outer.configure(width=420)

        canvas_form = tk.Canvas(f_form_outer, bg=BLANCO, highlightthickness=0, width=398)
        scrollbar_form = ttk.Scrollbar(f_form_outer, orient="vertical", command=canvas_form.yview)
        self.form_sim = tk.Frame(canvas_form, bg=BLANCO)

        form_window = canvas_form.create_window((0, 0), window=self.form_sim, anchor="nw")
        self.form_sim.bind(
            "<Configure>",
            lambda e: canvas_form.configure(scrollregion=canvas_form.bbox("all"))
        )
        canvas_form.bind(
            "<Configure>",
            lambda e: canvas_form.itemconfig(form_window, width=e.width)
        )
        canvas_form.configure(yscrollcommand=scrollbar_form.set)
        canvas_form.pack(side="left", fill="both", expand=True)
        scrollbar_form.pack(side="right", fill="y")

        # Capacidad base fija en 40 porque la BD fue ajustada a aulas homogéneas.
        capacidad_base = 40
        if "capacidad_aula" in self.df.columns and len(self.df["capacidad_aula"]) > 0:
            try:
                capacidad_base = int(round(float(self.df["capacidad_aula"].median())))
            except Exception:
                capacidad_base = 40

        self.vars_input = {
            "alumnos_nuevos": tk.IntVar(value=25),
            "alumnos_prerrequisito": tk.IntVar(value=20),
            "alumnos_repitentes": tk.IntVar(value=8),
            "capacidad_aula": tk.IntVar(value=capacidad_base),
            "duracion_semanas": tk.IntVar(value=18),
            "docentes_disponibles": tk.IntVar(value=2),
            "laboratorio": tk.IntVar(value=0),
        }

        self.form_sim.columnconfigure(0, weight=1)
        self.form_sim.columnconfigure(1, weight=0)

        fila = 0
        fila = self._crear_input_sim(
            self.form_sim, fila, "Alumnos nuevos", self.vars_input["alumnos_nuevos"],
            0, 120, "Demanda nueva esperada para el curso."
        )
        fila = self._crear_input_sim(
            self.form_sim, fila, "Alumnos con prerrequisito", self.vars_input["alumnos_prerrequisito"],
            0, 120, "Estudiantes habilitados para llevar la asignatura."
        )
        fila = self._crear_input_sim(
            self.form_sim, fila, "Alumnos repitentes", self.vars_input["alumnos_repitentes"],
            0, 80, "Sobrecarga académica por repetición del curso."
        )
        fila = self._crear_input_sim(
            self.form_sim, fila, "Capacidad por aula", self.vars_input["capacidad_aula"],
            1, 120, "Capacidad física base. En este avance se usa 40."
        )
        fila = self._crear_input_sim(
            self.form_sim, fila, "Duración en semanas", self.vars_input["duracion_semanas"],
            1, 24, "Duración operativa del curso en el periodo."
        )
        fila = self._crear_input_sim(
            self.form_sim, fila, "Docentes disponibles", self.vars_input["docentes_disponibles"],
            0, 20, "Recursos docentes disponibles para abrir secciones."
        )

        tk.Label(
            self.form_sim,
            text="Requiere laboratorio",
            font=FUENTE_NORMAL,
            bg=BLANCO,
            fg=NEGRO
        ).grid(row=fila, column=0, sticky="w", padx=12, pady=(8, 0))

        tk.Checkbutton(
            self.form_sim,
            text="Sí, reduce capacidad efectiva",
            variable=self.vars_input["laboratorio"],
            bg=BLANCO,
            fg=GRIS_TEXTO,
            activebackground=BLANCO,
            font=("Segoe UI", 9)
        ).grid(row=fila, column=1, sticky="e", padx=(0, 12), pady=(8, 0))
        fila += 1

        tk.Label(
            self.form_sim,
            text="Si el curso usa laboratorio, se reserva espacio para equipos y seguridad.",
            font=("Segoe UI", 8),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            wraplength=280,
            justify="left"
        ).grid(row=fila, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))
        fila += 1

        tk.Label(
            self.form_sim,
            text="Escenario de planificación",
            font=FUENTE_NORMAL,
            bg=BLANCO,
            fg=NEGRO
        ).grid(row=fila, column=0, sticky="w", padx=12, pady=(8, 2))

        self.combo_escenario_sim = ttk.Combobox(
            self.form_sim,
            values=["Conservador (+MAE)", "Base IA", "Optimista (-MAE)"],
            state="readonly",
            width=20
        )
        self.combo_escenario_sim.set("Conservador (+MAE)")
        self.combo_escenario_sim.grid(row=fila, column=1, sticky="e", padx=(0, 12), pady=(8, 2))
        fila += 1

        tk.Label(
            self.form_sim,
            text="Conservador usa el margen de error para reducir riesgo de falta de cupos.",
            font=("Segoe UI", 8),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            wraplength=280,
            justify="left"
        ).grid(row=fila, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))
        fila += 1

        tk.Label(
            self.form_sim,
            text="Turno / Pabellón referencial",
            font=FUENTE_NORMAL,
            bg=BLANCO,
            fg=NEGRO
        ).grid(row=fila, column=0, sticky="w", padx=12, pady=(8, 2))

        contexto = tk.Frame(self.form_sim, bg=BLANCO)
        contexto.grid(row=fila, column=1, sticky="e", padx=(0, 12), pady=(8, 2))

        horarios = sorted([str(x) for x in self.df["horario_seccion"].dropna().unique()]) if "horario_seccion" in self.df.columns else ["Mañana", "Tarde", "Noche"]
        pabellones = sorted([str(x) for x in self.df["pabellon"].dropna().unique()]) if "pabellon" in self.df.columns else ["A", "B", "C"]

        self.combo_turno_sim = ttk.Combobox(contexto, values=horarios, state="readonly", width=9)
        self.combo_turno_sim.set(horarios[0] if horarios else "Mañana")
        self.combo_turno_sim.pack(side="left", padx=(0, 5))

        self.combo_pabellon_sim = ttk.Combobox(contexto, values=pabellones, state="readonly", width=4)
        self.combo_pabellon_sim.set(pabellones[0] if pabellones else "A")
        self.combo_pabellon_sim.pack(side="left")
        fila += 1

        tk.Button(
            self.form_sim,
            text="EJECUTAR SIMULACIÓN IA",
            font=FUENTE_SUBTITULO,
            bg=ROJO_UTP,
            fg=BLANCO,
            activebackground=ROJO_CLARO,
            activeforeground=BLANCO,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.realizar_prediccion
        ).grid(row=fila, column=0, columnspan=2, padx=12, pady=(22, 8), sticky="we")
        fila += 1

        tk.Button(
            self.form_sim,
            text="Restablecer valores",
            font=FUENTE_NORMAL,
            bg=GRIS_TEXTO,
            fg=BLANCO,
            activebackground=NEGRO,
            activeforeground=BLANCO,
            bd=0,
            pady=7,
            cursor="hand2",
            command=self._restablecer_simulacion
        ).grid(row=fila, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="we")

        # =========================
        # PANEL DERECHO
        # =========================
        self.f_res_container = tk.Frame(cuerpo, bg=GRIS_FONDO)
        self.f_res_container.grid(row=0, column=1, sticky="nsew", pady=4)
        self.f_res_container.columnconfigure(0, weight=1)
        self.f_res_container.rowconfigure(0, weight=1)

        # Resultado principal con scroll para pantallas pequeñas.
        self.panel_resultado_sim = tk.Frame(self.f_res_container, bg=GRIS_FONDO)
        self.panel_resultado_sim.pack(fill="both", expand=True)

        canvas_result = tk.Canvas(self.panel_resultado_sim, bg=GRIS_FONDO, highlightthickness=0)
        scroll_result = ttk.Scrollbar(self.panel_resultado_sim, orient="vertical", command=canvas_result.yview)
        self.resultado_content_sim = tk.Frame(canvas_result, bg=GRIS_FONDO)

        result_window = canvas_result.create_window((0, 0), window=self.resultado_content_sim, anchor="nw")
        self.resultado_content_sim.bind(
            "<Configure>",
            lambda e: canvas_result.configure(scrollregion=canvas_result.bbox("all"))
        )
        canvas_result.bind(
            "<Configure>",
            lambda e: canvas_result.itemconfig(result_window, width=e.width)
        )
        canvas_result.configure(yscrollcommand=scroll_result.set)
        canvas_result.pack(side="left", fill="both", expand=True)
        scroll_result.pack(side="right", fill="y")

        # Banner de estado responsivo.
        self.banner_sim = tk.Frame(self.resultado_content_sim, bg=BLANCO, bd=1, relief="solid")
        self.banner_sim.pack(fill="x", pady=(0, 10))

        self.lbl_pred = tk.Label(
            self.banner_sim,
            text="Ejecuta una simulación",
            font=("Segoe UI", 18, "bold"),
            bg=BLANCO,
            fg=ROJO_UTP,
            justify="left"
        )
        self.lbl_pred.pack(anchor="w", padx=16, pady=(12, 2), fill="x")

        self.lbl_estado = tk.Label(
            self.banner_sim,
            text="El sistema calculará demanda, aulas, ocupación, cupos y recursos docentes.",
            font=("Segoe UI", 10),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            justify="left"
        )
        self.lbl_estado.pack(anchor="w", padx=16, pady=(0, 12), fill="x")

        self.banner_sim.bind(
            "<Configure>",
            lambda e: (
                self.lbl_pred.configure(wraplength=max(350, e.width - 40)),
                self.lbl_estado.configure(wraplength=max(350, e.width - 40))
            )
        )

        # KPIs en 2x2 para evitar textos cortados.
        self.frame_kpis_sim = tk.Frame(self.resultado_content_sim, bg=GRIS_FONDO)
        self.frame_kpis_sim.pack(fill="x", pady=(0, 10))
        self.frame_kpis_sim.columnconfigure(0, weight=1)
        self.frame_kpis_sim.columnconfigure(1, weight=1)

        self.sim_kpi_labels = {}
        self._crear_card_sim(self.frame_kpis_sim, "Demanda IA", "---", "demanda")
        self._crear_card_sim(self.frame_kpis_sim, "Demanda a planificar", "---", "planificacion")
        self._crear_card_sim(self.frame_kpis_sim, "Aulas recomendadas", "---", "aulas")
        self._crear_card_sim(self.frame_kpis_sim, "Ocupación promedio", "---", "ocupacion")

        # Resultado central en vertical: gráfico arriba, tabla abajo.
        self.panel_grafico_sim = tk.Frame(self.resultado_content_sim, bg=BLANCO, bd=1, relief="solid")
        self.panel_grafico_sim.pack(fill="both", expand=False, pady=(0, 10))

        self.panel_tabla_sim = tk.Frame(self.resultado_content_sim, bg=BLANCO, bd=1, relief="solid")
        self.panel_tabla_sim.pack(fill="both", expand=True, pady=(0, 5))

        tk.Label(
            self.panel_tabla_sim,
            text="Distribución sugerida por sección",
            font=FUENTE_SUBTITULO,
            bg=BLANCO,
            fg=NEGRO
        ).pack(anchor="w", padx=15, pady=(12, 5))

        columnas = ("seccion", "aula", "capacidad", "alumnos", "ocupacion", "estado")
        self.tree_secciones = ttk.Treeview(
            self.panel_tabla_sim,
            columns=columnas,
            show="headings",
            height=6
        )

        encabezados = {
            "seccion": "Sección",
            "aula": "Aula",
            "capacidad": "Capacidad",
            "alumnos": "Alumnos",
            "ocupacion": "Ocupación",
            "estado": "Estado"
        }

        anchos = {
            "seccion": 70,
            "aula": 90,
            "capacidad": 90,
            "alumnos": 90,
            "ocupacion": 95,
            "estado": 130
        }

        for col in columnas:
            self.tree_secciones.heading(col, text=encabezados[col])
            self.tree_secciones.column(col, anchor="center", width=anchos[col], stretch=True)

        scroll_y = ttk.Scrollbar(self.panel_tabla_sim, orient="vertical", command=self.tree_secciones.yview)
        self.tree_secciones.configure(yscrollcommand=scroll_y.set)
        self.tree_secciones.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(5, 15))
        scroll_y.pack(side="right", fill="y", padx=(0, 15), pady=(5, 15))

        # =========================
        # INFORME DETALLADO CON SCROLL
        # =========================
        self.container_scroll = tk.Frame(self.f_res_container, bg=BLANCO, bd=1, relief="solid")
        canvas = tk.Canvas(self.container_scroll, bg=BLANCO, highlightthickness=0, yscrollincrement=18)
        scrollbar = tk.Scrollbar(
            self.container_scroll,
            orient="vertical",
            command=canvas.yview,
            width=18,
            bd=1,
            relief="solid",
            bg=ROJO_UTP,
            activebackground=ROJO_CLARO,
            troughcolor="#E0E0E0"
        )
        self.panel_detalle = tk.Frame(canvas, bg=BLANCO)

        detalle_window = canvas.create_window((0, 0), window=self.panel_detalle, anchor="nw")
        self.panel_detalle.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(detalle_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._habilitar_scroll_mouse(canvas)

        tk.Label(
            self.panel_detalle,
            text="Informe técnico de simulación",
            font=("Segoe UI", 22, "bold"),
            bg=BLANCO,
            fg=ROJO_UTP
        ).pack(anchor="w", padx=25, pady=(20, 5))

        self.lbl_detalle = tk.Message(
            self.panel_detalle,
            text="Ejecuta una simulación para generar el informe operativo.",
            font=("Segoe UI", 11),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            width=850,
            justify="left"
        )
        self.lbl_detalle.pack(anchor="w", padx=25, pady=10, fill="x")

        self.panel_detalle.bind(
            "<Configure>",
            lambda e: self.lbl_detalle.configure(width=max(360, e.width - 60))
        )

        tk.Button(
            self.panel_detalle,
            text="Volver al resultado 🔙",
            font=FUENTE_NORMAL,
            bg=NEGRO,
            fg=BLANCO,
            activebackground=GRIS_TEXTO,
            activeforeground=BLANCO,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.volver_resultado
        ).pack(anchor="w", padx=25, pady=(5, 25))

        # =========================
        # GUÍA CON SCROLL Y TEXTO RESPONSIVO
        # =========================
        self.panel_guia_sim = tk.Frame(self.f_res_container, bg=BLANCO, bd=1, relief="solid")
        canvas_guia = tk.Canvas(self.panel_guia_sim, bg=BLANCO, highlightthickness=0, yscrollincrement=18)
        scrollbar_guia = tk.Scrollbar(
            self.panel_guia_sim,
            orient="vertical",
            command=canvas_guia.yview,
            width=18,
            bd=1,
            relief="solid",
            bg=ROJO_UTP,
            activebackground=ROJO_CLARO,
            troughcolor="#E0E0E0"
        )
        guia_content = tk.Frame(canvas_guia, bg=BLANCO)

        guia_window = canvas_guia.create_window((0, 0), window=guia_content, anchor="nw")
        guia_content.bind("<Configure>", lambda e: canvas_guia.configure(scrollregion=canvas_guia.bbox("all")))
        canvas_guia.bind("<Configure>", lambda e: canvas_guia.itemconfig(guia_window, width=e.width))
        canvas_guia.configure(yscrollcommand=scrollbar_guia.set)
        canvas_guia.pack(side="left", fill="both", expand=True)
        scrollbar_guia.pack(side="right", fill="y")
        self._habilitar_scroll_mouse(canvas_guia)

        tk.Label(
            guia_content,
            text="Guía del simulador",
            font=("Segoe UI", 22, "bold"),
            bg=BLANCO,
            fg=ROJO_UTP,
            justify="left"
        ).pack(anchor="w", padx=25, pady=(20, 8), fill="x")

        txt_guia = (
            "Este módulo convierte la predicción de matrícula en una decisión de infraestructura.\n\n"
            "1) Predicción IA:\n"
            "Usa el modelo entrenado con alumnos nuevos, prerrequisitos, repitentes, docente disponible, "
            "capacidad, duración y laboratorio.\n\n"
            "2) Escenario de planificación:\n"
            "• Conservador (+MAE): suma el margen de error promedio para reducir riesgo de falta de cupos.\n"
            "• Base IA: usa directamente la predicción central del modelo.\n"
            "• Optimista (-MAE): reduce el margen para escenarios de menor demanda.\n\n"
            "3) Capacidad efectiva:\n"
            "Si el curso requiere laboratorio, la capacidad se reduce 15% por equipos, movilidad y seguridad.\n\n"
            "4) Aulas recomendadas:\n"
            "No solo se calcula el mínimo por aforo. También se usa una ocupación segura del 90%, "
            "para evitar aulas al límite.\n\n"
            "5) Docentes requeridos:\n"
            "Se asume 1 docente por sección. Si faltan docentes, el estado operativo se marca como crítico.\n\n"
            "6) Distribución sugerida:\n"
            "Reparte la demanda de planificación entre las secciones recomendadas para facilitar la asignación."
        )

        self.lbl_guia_sim = tk.Message(
            guia_content,
            text=txt_guia,
            font=("Segoe UI", 11),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            width=850,
            justify="left"
        )
        self.lbl_guia_sim.pack(anchor="w", padx=25, pady=10, fill="x")

        guia_content.bind(
            "<Configure>",
            lambda e: self.lbl_guia_sim.configure(width=max(360, e.width - 60))
        )

        tk.Button(
            guia_content,
            text="Volver al simulador 🔙",
            font=FUENTE_NORMAL,
            bg=NEGRO,
            fg=BLANCO,
            activebackground=GRIS_TEXTO,
            activeforeground=BLANCO,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.volver_resultado
        ).pack(anchor="w", padx=25, pady=(5, 25))

        self.mostrar_guia_sim = False
        self.mostrar_detalle = False

        # Estado inicial útil para exposición.
        self._render_grafico_simulacion(0, 0, 0, 40)
        self.tree_secciones.insert("", "end", values=("-", "Ejecutar", "-", "-", "-", "-"))
        self.realizar_prediccion()

    def _habilitar_scroll_mouse(self, canvas):
        """Activa desplazamiento con rueda del mouse en paneles Canvas con scrollbar visible."""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-1, "units")

        def _on_linux_scroll_down(event):
            canvas.yview_scroll(1, "units")

        def _bind_scroll(_event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_linux_scroll_up)
            canvas.bind_all("<Button-5>", _on_linux_scroll_down)

        def _unbind_scroll(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_scroll)
        canvas.bind("<Leave>", _unbind_scroll)

    def _crear_input_sim(self, parent, fila, etiqueta, variable, minimo, maximo, ayuda):
        """Crea una entrada numérica uniforme para el formulario de simulación."""
        tk.Label(
            parent,
            text=etiqueta,
            font=("Segoe UI", 10),
            bg=BLANCO,
            fg=NEGRO
        ).grid(row=fila, column=0, sticky="w", padx=12, pady=(7, 0))

        spin = tk.Spinbox(
            parent,
            from_=minimo,
            to=maximo,
            textvariable=variable,
            width=7,
            font=("Segoe UI", 10),
            justify="center"
        )
        spin.grid(row=fila, column=1, sticky="e", padx=(0, 12), pady=(7, 0))
        fila += 1

        tk.Label(
            parent,
            text=ayuda,
            font=("Segoe UI", 8),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            wraplength=280,
            justify="left"
        ).grid(row=fila, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 4))
        fila += 1
        return fila

    def _crear_card_sim(self, parent, titulo, valor, clave):
        """Crea una tarjeta KPI compacta para la simulación en una grilla 2x2."""
        index = len(self.sim_kpi_labels)
        fila = index // 2
        columna = index % 2

        card = tk.Frame(parent, bg=BLANCO, bd=1, relief="solid", height=82)
        card.grid(row=fila, column=columna, sticky="nsew", padx=5, pady=5)
        card.grid_propagate(False)

        tk.Label(
            card,
            text=titulo,
            font=("Segoe UI", 9),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            wraplength=230,
            justify="center"
        ).pack(pady=(10, 1), fill="x")

        lbl = tk.Label(
            card,
            text=valor,
            font=("Segoe UI", 17, "bold"),
            bg=BLANCO,
            fg=ROJO_UTP
        )
        lbl.pack()

        self.sim_kpi_labels[clave] = lbl

    def _restablecer_simulacion(self):
        """Restablece valores razonables para una simulación base."""
        self.vars_input["alumnos_nuevos"].set(25)
        self.vars_input["alumnos_prerrequisito"].set(20)
        self.vars_input["alumnos_repitentes"].set(8)
        self.vars_input["capacidad_aula"].set(40)
        self.vars_input["duracion_semanas"].set(12)
        self.vars_input["docentes_disponibles"].set(2)
        self.vars_input["laboratorio"].set(0)
        self.combo_escenario_sim.set("Conservador (+MAE)")
        self.realizar_prediccion()

    def _mostrar_panel_simulacion(self, panel):
        """Muestra uno de los paneles derechos sin destruir el estado de la vista."""
        for p in [self.panel_resultado_sim, self.container_scroll, self.panel_guia_sim]:
            p.pack_forget()
        panel.pack(fill="both", expand=True)

    def toggle_detalles(self):
        self._mostrar_panel_simulacion(self.container_scroll)
        self.mostrar_detalle = True
        self.mostrar_guia_sim = False

    def volver_resultado(self):
        self._mostrar_panel_simulacion(self.panel_resultado_sim)
        self.mostrar_detalle = False
        self.mostrar_guia_sim = False

    def toggle_guia_simulacion(self):
        if self.mostrar_guia_sim:
            self.volver_resultado()
        else:
            self._mostrar_panel_simulacion(self.panel_guia_sim)
            self.mostrar_guia_sim = True
            self.mostrar_detalle = False

    def _clasificar_ocupacion(self, ratio):
        """Devuelve estado textual y color según ocupación."""
        if ratio > 1:
            return "Excede aforo", COLOR_SOBREPOBLADO
        if ratio >= 0.90:
            return "Ajustado", "#B8860B"
        if ratio >= 0.65:
            return "Óptimo", COLOR_OPTIMO
        if ratio >= 0.45:
            return "Baja ocupación", "#B8860B"
        return "Subutilizado", COLOR_SUBUTILIZADO

    def _render_grafico_simulacion(self, demanda_base, demanda_plan, cupos_planificados, capacidad_aula):
        """Renderiza gráfico comparativo de demanda y capacidad planificada."""
        for widget in self.panel_grafico_sim.winfo_children():
            widget.destroy()

        fig_prev = getattr(self, "_fig_simulacion", None)
        if fig_prev is not None:
            plt.close(fig_prev)

        self._fig_simulacion, ax = plt.subplots(figsize=(7.6, 3.15))
        self._fig_simulacion.patch.set_facecolor(BLANCO)

        etiquetas = ["IA", "Planificada", "Cupos"]
        valores = [demanda_base, demanda_plan, cupos_planificados]
        colores = [ROJO_UTP, ROJO_CLARO, COLOR_OPTIMO]

        barras = ax.bar(etiquetas, valores, color=colores, alpha=0.88, width=0.55)

        limite_superior = max(max(valores + [capacidad_aula]) * 1.25, capacidad_aula + 10)
        for barra, valor in zip(barras, valores):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + limite_superior * 0.02,
                f"{int(valor)}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        ax.axhline(y=capacidad_aula, linestyle="--", linewidth=1.2, color=GRIS_TEXTO, alpha=0.7)
        ax.text(
            -0.35,
            capacidad_aula + limite_superior * 0.025,
            f"Capacidad por aula: {capacidad_aula}",
            fontsize=9,
            color=GRIS_TEXTO
        )

        ax.set_title("Demanda vs capacidad operativa", fontsize=13, pad=10)
        ax.set_ylabel("Alumnos / cupos", fontsize=10)
        ax.set_ylim(0, limite_superior)
        ax.tick_params(axis="x", labelsize=10)
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)
        ax.set_facecolor("#F9F9F9")
        plt.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(self._fig_simulacion, master=self.panel_grafico_sim)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=8)

    def realizar_prediccion(self):
        try:
            # =========================
            # 1. LECTURA Y VALIDACIÓN
            # =========================
            alumnos_nuevos = int(self.vars_input["alumnos_nuevos"].get())
            alumnos_pre = int(self.vars_input["alumnos_prerrequisito"].get())
            alumnos_rep = int(self.vars_input["alumnos_repitentes"].get())
            capacidad = int(self.vars_input["capacidad_aula"].get())
            duracion = int(self.vars_input["duracion_semanas"].get())
            docentes_disponibles = int(self.vars_input["docentes_disponibles"].get())
            laboratorio = int(self.vars_input["laboratorio"].get())

            if min(alumnos_nuevos, alumnos_pre, alumnos_rep, capacidad, duracion, docentes_disponibles) < 0:
                raise ValueError("No se permiten valores negativos.")
            if capacidad <= 0:
                raise ValueError("La capacidad del aula debe ser mayor a cero.")
            if duracion <= 0:
                raise ValueError("La duración debe ser mayor a cero.")
            if laboratorio not in [0, 1]:
                laboratorio = 1 if laboratorio else 0

            turno = self.combo_turno_sim.get()
            pabellon = self.combo_pabellon_sim.get()
            escenario = self.combo_escenario_sim.get()

            # El modelo entrenó con docente_disponible como variable binaria.
            docente_disponible_modelo = 1 if docentes_disponibles > 0 else 0

            # =========================
            # 2. PREDICCIÓN IA
            # =========================
            datos_prediccion = pd.DataFrame([{
                "alumnos_nuevos": alumnos_nuevos,
                "alumnos_prerrequisito": alumnos_pre,
                "alumnos_repitentes": alumnos_rep,
                "docente_disponible": docente_disponible_modelo,
                "capacidad_aula": capacidad,
                "duracion_semanas": duracion,
                "laboratorio": laboratorio
            }])

            pred_base = int(round(float(self.modelo_activo.predict(datos_prediccion)[0])))
            pred_base = max(0, pred_base)

            mae = float(self.modelos["Regresión Lineal Múltiple"]["MAE"])
            pred_min = max(0, int(np.floor(pred_base - mae)))
            pred_max = max(pred_base, int(np.ceil(pred_base + mae)))

            if escenario == "Optimista (-MAE)":
                demanda_plan = pred_min
            elif escenario == "Base IA":
                demanda_plan = pred_base
            else:
                demanda_plan = pred_max

            demanda_plan = max(1, int(demanda_plan))

            # =========================
            # 3. CAPACIDAD Y SECCIONES
            # =========================
            factor_laboratorio = 0.85 if laboratorio == 1 else 1.00
            capacidad_efectiva = max(1, int(np.floor(capacidad * factor_laboratorio)))

            # Se recomienda no planificar al 100% de ocupación.
            capacidad_segura = max(1, int(np.floor(capacidad_efectiva * 0.90)))

            aulas_minimas = max(1, int(np.ceil(demanda_plan / capacidad_efectiva)))
            aulas_recomendadas = max(1, int(np.ceil(demanda_plan / capacidad_segura)))
            
            # Guardar variables de simulación para el algoritmo genético
            self.sim_demanda_plan = demanda_plan
            self.sim_aulas_recomendadas = aulas_recomendadas
            self.sim_capacidad_efectiva = capacidad_efectiva
            self.sim_laboratorio = laboratorio
            self.sim_turno = turno
            self.sim_pabellon = pabellon
            capacidad_total = aulas_recomendadas * capacidad_efectiva
            ocupacion_promedio = demanda_plan / capacidad_total
            cupos_libres = capacidad_total - demanda_plan

            docentes_necesarios = aulas_recomendadas
            deficit_docentes = max(0, docentes_necesarios - docentes_disponibles)

            saturacion_sin_plan = pred_base / capacidad_efectiva
            exceso_sin_plan = max(0, pred_base - capacidad_efectiva)

            estado_ocupacion, color_ocupacion = self._clasificar_ocupacion(ocupacion_promedio)

            if deficit_docentes > 0:
                estado_general = "🔴 CRÍTICO OPERATIVO"
                color_estado = COLOR_SOBREPOBLADO
                recomendacion = (
                    f"Faltan {deficit_docentes} docente(s). Asignar docentes adicionales, "
                    "abrir otro turno o reducir la cantidad de secciones planificadas."
                )
            elif ocupacion_promedio > 1:
                estado_general = "🔴 CRÍTICO POR AFORO"
                color_estado = COLOR_SOBREPOBLADO
                recomendacion = "La demanda supera los cupos planificados. Abrir secciones adicionales."
            elif ocupacion_promedio >= 0.90:
                estado_general = "🟠 AJUSTADO"
                color_estado = "#B8860B"
                recomendacion = "La asignación es viable, pero queda con poco margen. Conviene monitorear matrícula."
            elif ocupacion_promedio >= 0.65:
                estado_general = "🟢 ÓPTIMO"
                color_estado = COLOR_OPTIMO
                recomendacion = "La carga está equilibrada. Se recomienda aprobar esta distribución."
            elif ocupacion_promedio >= 0.45:
                estado_general = "🟡 BAJA OCUPACIÓN"
                color_estado = "#B8860B"
                recomendacion = "Hay cupos libres relevantes. Evaluar fusión de secciones si la demanda real baja."
            else:
                estado_general = "🟡 SUBUTILIZADO"
                color_estado = COLOR_SUBUTILIZADO
                recomendacion = "Demasiada capacidad ociosa. Reducir secciones o reasignar aulas."

            # =========================
            # 4. EFICIENCIA ADMINISTRATIVA
            # =========================
            tiempo_hist = float(self.df["tiempo_matricula_min"].mean())
            complejidad_operativa = 1 + max(0, aulas_recomendadas - 1) * 0.08 + (0.05 if laboratorio == 1 else 0)
            tiempo_sin_ia = tiempo_hist * complejidad_operativa
            tiempo_con_ia = tiempo_sin_ia * 0.70
            mejora = ((tiempo_sin_ia - tiempo_con_ia) / tiempo_sin_ia) * 100

            # Riesgo académico estimado según saturación sin planificación.
            if saturacion_sin_plan > 1:
                alumnos_riesgo = int(np.ceil(exceso_sin_plan * 0.60))
                riesgo_texto = "alto si se mantiene una sola aula"
            elif saturacion_sin_plan >= 0.90:
                alumnos_riesgo = int(np.ceil(pred_base * 0.06))
                riesgo_texto = "moderado por ocupación ajustada"
            else:
                alumnos_riesgo = int(np.ceil(pred_base * 0.03))
                riesgo_texto = "bajo"

            # =========================
            # 5. ACTUALIZAR KPIs
            # =========================
            self.lbl_pred.config(
                text=f"{estado_general} — {demanda_plan} alumnos a planificar",
                fg=color_estado
            )

            self.lbl_estado.config(
                text=(
                    f"Predicción base: {pred_base} | Intervalo operativo: {pred_min}–{pred_max} | "
                    f"Turno: {turno} | Pabellón: {pabellon} | {recomendacion}"
                ),
                fg=GRIS_TEXTO
            )

            self.sim_kpi_labels["demanda"].config(text=f"{pred_base}", fg=ROJO_UTP)
            self.sim_kpi_labels["planificacion"].config(text=f"{demanda_plan}", fg=ROJO_UTP)
            self.sim_kpi_labels["aulas"].config(text=f"{aulas_recomendadas}", fg=color_estado)
            self.sim_kpi_labels["ocupacion"].config(text=f"{ocupacion_promedio*100:.1f}%", fg=color_estado)

            # =========================
            # 6. TABLA DE DISTRIBUCIÓN
            # =========================
            for item in self.tree_secciones.get_children():
                self.tree_secciones.delete(item)

            base_por_seccion = demanda_plan // aulas_recomendadas
            resto = demanda_plan % aulas_recomendadas

            distribucion = []
            for i in range(aulas_recomendadas):
                alumnos_seccion = base_por_seccion + (1 if i < resto else 0)
                ratio = alumnos_seccion / capacidad_efectiva
                estado_sec, _ = self._clasificar_ocupacion(ratio)
                aula_sugerida = f"{pabellon}-{i+1:02d}"
                distribucion.append((i + 1, aula_sugerida, capacidad_efectiva, alumnos_seccion, ratio, estado_sec))

                self.tree_secciones.insert(
                    "",
                    "end",
                    values=(
                        f"S{i+1}",
                        aula_sugerida,
                        capacidad_efectiva,
                        alumnos_seccion,
                        f"{ratio*100:.1f}%",
                        estado_sec
                    )
                )

            # =========================
            # 7. GRÁFICO
            # =========================
            self._render_grafico_simulacion(
                demanda_base=pred_base,
                demanda_plan=demanda_plan,
                cupos_planificados=capacidad_total,
                capacidad_aula=capacidad_efectiva
            )

            # =========================
            # 8. INFORME DETALLADO
            # =========================
            lab_texto = "Sí, capacidad reducida al 85%" if laboratorio == 1 else "No, capacidad completa"

            detalle = f"""
📊 RESULTADO EJECUTIVO

Estado general:
{estado_general}

Recomendación:
{recomendacion}

📌 DEMANDA ESTIMADA

• Predicción base del modelo IA: {pred_base} alumnos
• Margen de error usado (MAE): ± {mae:.2f} alumnos
• Intervalo operativo estimado: {pred_min} a {pred_max} alumnos
• Escenario seleccionado: {escenario}
• Demanda usada para planificación: {demanda_plan} alumnos

🏫 PLANIFICACIÓN DE AULAS

• Capacidad física por aula: {capacidad} alumnos
• Laboratorio: {lab_texto}
• Capacidad efectiva por aula: {capacidad_efectiva} alumnos
• Capacidad segura usada para planificación: {capacidad_segura} alumnos por aula
• Aulas mínimas por aforo: {aulas_minimas}
• Aulas recomendadas: {aulas_recomendadas}
• Cupos planificados totales: {capacidad_total}
• Cupos libres proyectados: {cupos_libres}
• Ocupación promedio: {ocupacion_promedio*100:.1f}% ({estado_ocupacion})

👨‍🏫 RECURSOS DOCENTES

• Docentes disponibles: {docentes_disponibles}
• Docentes requeridos: {docentes_necesarios}
• Déficit docente: {deficit_docentes}

⚠️ RIESGO SIN PLANIFICACIÓN

• Saturación si solo se usara 1 aula: {saturacion_sin_plan:.2f}
• Exceso estimado sobre una sola aula: {exceso_sin_plan} alumno(s)
• Alumnos en riesgo operativo: {alumnos_riesgo} ({riesgo_texto})

⏱️ EFICIENCIA ADMINISTRATIVA

• Tiempo histórico promedio de matrícula: {tiempo_hist:.1f} min
• Tiempo estimado sin asistencia IA: {tiempo_sin_ia:.1f} min
• Tiempo estimado con asistencia IA: {tiempo_con_ia:.1f} min
• Mejora administrativa estimada: {mejora:.1f}%

📚 INTERPRETACIÓN DE VARIABLES

• Alumnos nuevos: {alumnos_nuevos}
• Alumnos con prerrequisito: {alumnos_pre}
• Alumnos repitentes: {alumnos_rep}
• Duración del curso: {duracion} semanas
• Turno referencial: {turno}
• Pabellón referencial: {pabellon}

🧩 DISTRIBUCIÓN SUGERIDA

"""

            for seccion, aula, cap, alumnos, ratio, estado_sec in distribucion:
                detalle += f"• Sección S{seccion} → Aula {aula}: {alumnos}/{cap} alumnos ({ratio*100:.1f}%) - {estado_sec}\n"

            self.lbl_detalle.config(text=detalle.strip())

            # Al ejecutar, volver automáticamente al resultado principal.
            self.volver_resultado()

        except Exception as e:
            messagebox.showerror("Error", f"Datos inválidos o incompletos.\n\nDetalle técnico: {e}")

    # ==============================
    # 4. VISTA: HORARIOS DISTRIBUIDOS (Algoritmo Genético)
    # ==============================

    # --- Clase interna: Motor del Algoritmo Genético ---
    class _OptimizadorGenetico:
        """Algoritmo Genético para optimizar la asignación de secciones a
        combinaciones (aula, horario), minimizando colisiones y desperdicio
        de aforo. Usa los resultados de Regresión Lineal (predicción de
        demanda) y K-Means Clustering (clasificación de estado del aula)
        como insumos para la función de aptitud (fitness).

        Componentes obligatorios de la metaheurística:
        • Población   – conjunto de cromosomas (soluciones candidatas)
        • Fitness     – función de aptitud con penalizaciones duras y blandas
        • Selección   – torneo de tamaño k=3
        • Cruce       – single-point crossover con tasa configurable
        • Mutación    – mutación uniforme por gen con tasa configurable
        • Elitismo    – los 2 mejores pasan intactos a la siguiente generación
        """

        def __init__(self, aulas, horarios, secciones,
                     tam_poblacion=80, generaciones=100,
                     tasa_cruce=0.8, tasa_mutacion=0.10):
            self.aulas = aulas
            self.horarios = horarios
            self.secciones = secciones
            self.tam_poblacion = tam_poblacion
            self.generaciones = generaciones
            self.tasa_cruce = tasa_cruce
            self.tasa_mutacion = tasa_mutacion

            self.num_aulas = len(aulas)
            self.num_horarios = len(horarios)
            self.num_genes = len(secciones)

            # Espacio de búsqueda: cada gen codifica un par (aula, horario)
            self.espacio = []
            for ia in range(self.num_aulas):
                for ih in range(self.num_horarios):
                    self.espacio.append((ia, ih))
            self.tam_espacio = len(self.espacio)

            self.mejor_cromosoma = None
            self.mejor_conflictos = []

        # --- Función de Aptitud (Fitness) ---------------------------------
        def calcular_fitness(self, cromosoma):
            """Evalúa un cromosoma. Retorna (fitness, lista_conflictos).
            fitness = 1 / (1 + penalización_total)
            """
            pen = 0
            conflictos = []
            uso_aula = {}     # (i_aula, i_horario) -> [indices de sección]
            uso_docente = {}  # (docente_id, i_horario) -> [indices de sección]

            for i_sec, gen in enumerate(cromosoma):
                ia, ih = self.espacio[gen]
                aula = self.aulas[ia]
                horario = self.horarios[ih]
                sec = self.secciones[i_sec]

                # Colisión de aula
                clave_a = (ia, ih)
                uso_aula.setdefault(clave_a, []).append(i_sec)

                # Colisión de docente
                clave_d = (sec['docente_id'], ih)
                uso_docente.setdefault(clave_d, []).append(i_sec)

                # Capacidad efectiva (laboratorio reduce 15%)
                factor = 0.85 if sec['laboratorio'] == 1 else 1.0
                cap_ef = int(aula['capacidad_aula'] * factor)

                if sec['demanda'] > cap_ef:
                    exceso = sec['demanda'] - cap_ef
                    pen += 500 + exceso * 10
                    conflictos.append(
                        f"Secc {sec['sid']} ({sec['curso']}): "
                        f"demanda {sec['demanda']} > cap {cap_ef} en Aula {aula['aula_id']}")
                else:
                    pen += (cap_ef - sec['demanda']) * 1.5  # desperdicio

                # Laboratorio incompatible
                if sec['laboratorio'] == 1 and aula.get('pabellon', '') != 'C':
                    pen += 400
                    conflictos.append(
                        f"Secc {sec['sid']} ({sec['curso']}): requiere Lab (Pab C), "
                        f"asignada en Pab {aula.get('pabellon', '?')}")

                # Turno no preferido
                if horario['turno'].lower() != sec.get('turno_pref', '').lower():
                    pen += 100

            # Penalizar colisiones
            for clave, ids in uso_aula.items():
                if len(ids) > 1:
                    pen += (len(ids) - 1) * 1000
                    a_id = self.aulas[clave[0]]['aula_id']
                    h_str = f"{self.horarios[clave[1]]['dia']} {self.horarios[clave[1]]['turno']}"
                    conflictos.append(
                        f"Colisión aula: {len(ids)} secciones en Aula {a_id}, {h_str}")

            for clave, ids in uso_docente.items():
                if len(ids) > 1:
                    pen += (len(ids) - 1) * 1000
                    h_str = f"{self.horarios[clave[1]]['dia']} {self.horarios[clave[1]]['turno']}"
                    conflictos.append(
                        f"Colisión docente ID {clave[0]}: {len(ids)} secciones en {h_str}")

            return 1.0 / (1.0 + pen), conflictos

        # --- Inicialización de la Población -------------------------------
        def inicializar_poblacion(self):
            """Genera la población inicial de cromosomas aleatorios."""
            return [[random.randint(0, self.tam_espacio - 1)
                     for _ in range(self.num_genes)]
                    for _ in range(self.tam_poblacion)]

        # --- Selección por Torneo -----------------------------------------
        def seleccion_torneo(self, poblacion, fitness_list, k=3):
            """Selecciona individuos por torneo de tamaño k."""
            sel = []
            pool = list(zip(poblacion, fitness_list))
            for _ in range(len(poblacion)):
                aspirantes = random.sample(pool, min(k, len(pool)))
                ganador = max(aspirantes, key=lambda x: x[1])[0]
                sel.append(list(ganador))
            return sel

        # --- Cruce en un Punto (Single-Point Crossover) -------------------
        def cruzar(self, p1, p2):
            """Cruza dos padres. Retorna dos hijos."""
            if random.random() < self.tasa_cruce and self.num_genes > 1:
                pt = random.randint(1, self.num_genes - 1)
                return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]
            return list(p1), list(p2)

        # --- Mutación Uniforme --------------------------------------------
        def mutar(self, ind):
            """Muta cada gen con probabilidad tasa_mutacion."""
            for i in range(self.num_genes):
                if random.random() < self.tasa_mutacion:
                    ind[i] = random.randint(0, self.tam_espacio - 1)
            return ind

        # --- Bucle Evolutivo (generador) ----------------------------------
        def optimizar(self):
            """Generador que ejecuta el ciclo evolutivo completo.
            Produce (gen, fitness_actual, mejor_fitness, mejor_cromosoma, conflictos)
            en cada generación para actualizar la GUI sin bloquearla."""
            pob = self.inicializar_poblacion()
            mejor_f = -1.0
            mejor_c = None
            mejor_conf = []

            for gen in range(self.generaciones):
                evals = [self.calcular_fitness(ind) for ind in pob]
                fits = [e[0] for e in evals]

                idx_best = int(np.argmax(fits))
                f_gen = fits[idx_best]

                if f_gen > mejor_f:
                    mejor_f = f_gen
                    mejor_c = list(pob[idx_best])
                    mejor_conf = evals[idx_best][1]
                    self.mejor_cromosoma = mejor_c
                    self.mejor_conflictos = mejor_conf

                yield gen, f_gen, mejor_f, mejor_c, mejor_conf

                # Siguiente generación
                padres = self.seleccion_torneo(pob, fits)
                nueva = []
                orden = np.argsort(fits)[::-1]
                nueva.append(list(pob[orden[0]]))  # elitismo 1
                if len(pob) > 1:
                    nueva.append(list(pob[orden[1]]))  # elitismo 2

                while len(nueva) < self.tam_poblacion:
                    pa = random.choice(padres)
                    pb = random.choice(padres)
                    h1, h2 = self.cruzar(pa, pb)
                    nueva.append(self.mutar(h1))
                    if len(nueva) < self.tam_poblacion:
                        nueva.append(self.mutar(h2))
                pob = nueva

    # --- Vista del Dashboard: Horarios Distribuidos -----------------------
    def vista_horarios_distribuidos(self):
        """Construye la interfaz de la vista 'Horarios Distribuidos'.
        Permite configurar hiperparámetros del AG, ejecutar la optimización
        y visualizar la convergencia y la tabla de asignación resultante."""
        self.limpiar_contenedor()

        tk.Label(self.contenedor_principal,
                 text="Horarios Distribuidos — Algoritmo Genético",
                 font=FUENTE_TITULO, bg=GRIS_FONDO, fg=NEGRO
                 ).pack(pady=15, anchor="w", padx=30)

        tk.Label(self.contenedor_principal,
                 text=("Optimización metaheurística que combina la predicción de "
                       "demanda (Regresión Lineal) y la clasificación de eficiencia "
                       "(K-Means Clustering) para distribuir secciones en aulas y horarios."),
                 font=("Segoe UI", 10), bg=GRIS_FONDO, fg=GRIS_TEXTO,
                 wraplength=900, justify="left"
                 ).pack(anchor="w", padx=30, pady=(0, 10))

        cuerpo = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30, pady=5)
        cuerpo.columnconfigure(0, weight=0, minsize=370)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        # === PANEL IZQUIERDO: CONFIGURACIÓN ===
        f_cfg = tk.LabelFrame(cuerpo, text="Configuración del AG",
                              font=FUENTE_SUBTITULO, bg=BLANCO, fg=NEGRO,
                              padx=15, pady=15)
        f_cfg.grid(row=0, column=0, sticky="ns", padx=(0, 15))
        f_cfg.columnconfigure(0, weight=1)
        f_cfg.columnconfigure(1, weight=0)

        row = 0
        # Periodo
        tk.Label(f_cfg, text="Periodo académico:", font=FUENTE_NORMAL,
                 bg=BLANCO).grid(row=row, column=0, sticky="w", pady=4)
        periodos = sorted(list(self.df["periodo"].dropna().unique()))
        self._hd_periodo = ttk.Combobox(f_cfg, values=periodos,
                                        state="readonly", width=14)
        self._hd_periodo.set(periodos[-1] if periodos else "")
        self._hd_periodo.grid(row=row, column=1, sticky="e", pady=4)
        row += 1

        # Pabellón
        tk.Label(f_cfg, text="Pabellón:", font=FUENTE_NORMAL,
                 bg=BLANCO).grid(row=row, column=0, sticky="w", pady=4)
        pabs = sorted(list(self.df["pabellon"].dropna().unique()))
        self._hd_pabellon = ttk.Combobox(f_cfg, values=pabs,
                                         state="readonly", width=14)
        self._hd_pabellon.set(pabs[0] if pabs else "A")
        self._hd_pabellon.grid(row=row, column=1, sticky="e", pady=4)
        row += 1

        # Turno
        tk.Label(f_cfg, text="Turno de referencia:", font=FUENTE_NORMAL,
                 bg=BLANCO).grid(row=row, column=0, sticky="w", pady=4)
        turnos_uniq = sorted([str(x) for x in self.df["horario_seccion"].dropna().unique()])
        self._hd_turno = ttk.Combobox(f_cfg, values=turnos_uniq,
                                      state="readonly", width=14)
        self._hd_turno.set(turnos_uniq[0] if turnos_uniq else "Mañana")
        self._hd_turno.grid(row=row, column=1, sticky="e", pady=4)
        row += 1

        # Población
        tk.Label(f_cfg, text="Tamaño de población:", font=FUENTE_NORMAL,
                 bg=BLANCO).grid(row=row, column=0, sticky="w", pady=4)
        self._hd_pop = tk.IntVar(value=80)
        tk.Spinbox(f_cfg, from_=20, to=300, textvariable=self._hd_pop,
                   width=12, justify="center").grid(row=row, column=1,
                                                    sticky="e", pady=4)
        row += 1

        # Generaciones
        tk.Label(f_cfg, text="Generaciones:", font=FUENTE_NORMAL,
                 bg=BLANCO).grid(row=row, column=0, sticky="w", pady=4)
        self._hd_gen = tk.IntVar(value=100)
        tk.Spinbox(f_cfg, from_=10, to=500, textvariable=self._hd_gen,
                   width=12, justify="center").grid(row=row, column=1,
                                                    sticky="e", pady=4)
        row += 1

        # Prob. mutación
        tk.Label(f_cfg, text="Prob. de mutación:", font=FUENTE_NORMAL,
                 bg=BLANCO).grid(row=row, column=0, sticky="w", pady=4)
        self._hd_mut = tk.DoubleVar(value=0.10)
        tk.Spinbox(f_cfg, from_=0.01, to=0.50, increment=0.01,
                   textvariable=self._hd_mut, width=12,
                   justify="center").grid(row=row, column=1,
                                          sticky="e", pady=4)
        row += 1

        # Botón ejecutar
        tk.Button(f_cfg, text="EJECUTAR OPTIMIZACIÓN",
                  font=FUENTE_SUBTITULO, bg=ROJO_UTP, fg=BLANCO,
                  activebackground=ROJO_CLARO, activeforeground=BLANCO,
                  bd=0, pady=10, cursor="hand2",
                  command=self._ejecutar_horarios_ag
                  ).grid(row=row, column=0, columnspan=2,
                         sticky="we", pady=(18, 10))
        row += 1

        # Panel de estadísticas
        f_stats = tk.LabelFrame(f_cfg, text="Resultados del Proceso",
                                font=("Segoe UI", 10, "bold"),
                                bg=BLANCO, fg=NEGRO, padx=10, pady=10)
        f_stats.grid(row=row, column=0, columnspan=2, sticky="we", pady=8)

        self._hd_lbl_fit = tk.Label(f_stats, text="Mejor Fitness: ---",
                                    font=FUENTE_NORMAL, bg=BLANCO, fg=GRIS_TEXTO)
        self._hd_lbl_fit.pack(anchor="w")
        self._hd_lbl_conf = tk.Label(f_stats, text="Conflictos: ---",
                                     font=FUENTE_NORMAL, bg=BLANCO, fg=GRIS_TEXTO)
        self._hd_lbl_conf.pack(anchor="w")
        self._hd_lbl_time = tk.Label(f_stats, text="Tiempo: ---",
                                     font=FUENTE_NORMAL, bg=BLANCO, fg=GRIS_TEXTO)
        self._hd_lbl_time.pack(anchor="w")

        # === PANEL DERECHO: GRÁFICO + TABLA ===
        f_der = tk.Frame(cuerpo, bg=GRIS_FONDO)
        f_der.grid(row=0, column=1, sticky="nsew")
        f_der.rowconfigure(0, weight=1)
        f_der.rowconfigure(1, weight=1)
        f_der.columnconfigure(0, weight=1)

        # Gráfico de convergencia
        self._hd_panel_graf = tk.Frame(f_der, bg=BLANCO, bd=1, relief="solid")
        self._hd_panel_graf.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        # Tabla de asignación
        self._hd_panel_tabla = tk.Frame(f_der, bg=BLANCO, bd=1, relief="solid")
        self._hd_panel_tabla.grid(row=1, column=0, sticky="nsew")

        tk.Label(self._hd_panel_tabla,
                 text="Distribución Óptima de Horarios y Aulas",
                 font=FUENTE_SUBTITULO, bg=BLANCO, fg=NEGRO
                 ).pack(anchor="w", padx=15, pady=(10, 5))

        cols = ("seccion", "curso", "docente", "aula",
                "capacidad", "horario", "ocupacion", "estado")
        self._hd_tree = ttk.Treeview(self._hd_panel_tabla,
                                     columns=cols, show="headings", height=9)
        headers = {"seccion": "Sección", "curso": "Curso",
                   "docente": "Docente", "aula": "Aula",
                   "capacidad": "Capacidad", "horario": "Día / Turno",
                   "ocupacion": "Ocupación", "estado": "Estado"}
        for c in cols:
            self._hd_tree.heading(c, text=headers[c])
            self._hd_tree.column(c, anchor="center", stretch=True)

        sb = ttk.Scrollbar(self._hd_panel_tabla, orient="vertical",
                           command=self._hd_tree.yview)
        self._hd_tree.configure(yscrollcommand=sb.set)
        self._hd_tree.pack(side="left", fill="both", expand=True,
                           padx=(15, 0), pady=(5, 10))
        sb.pack(side="right", fill="y", padx=(0, 15), pady=(5, 10))

        self._hd_fig = None
        self._hd_render_vacio()

    # --- Gráfico vacío inicial ---
    def _hd_render_vacio(self):
        for w in self._hd_panel_graf.winfo_children():
            w.destroy()
        if self._hd_fig is not None:
            plt.close(self._hd_fig)

        self._hd_fig, ax = plt.subplots(figsize=(8, 2.6))
        self._hd_fig.patch.set_facecolor(BLANCO)
        ax.set_facecolor("#F9F9F9")
        ax.set_title("Convergencia del Algoritmo Genético", fontsize=12)
        ax.set_xlabel("Generación", fontsize=10)
        ax.set_ylabel("Fitness (Aptitud)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(self._hd_fig, master=self._hd_panel_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- Preparar secciones usando Regresión + Clustering -----------------
    def _hd_preparar_secciones(self, periodo, pabellon, turno):
        """Genera la lista de secciones para el AG combinando:
        1) Predicción de demanda por Regresión Lineal (modelo entrenado)
        2) Clasificación de eficiencia por K-Means (cluster del análisis)
        """
        # Filtrar datos históricos
        mask = (self.df["periodo"] == periodo) & (self.df["pabellon"] == pabellon)
        df_filt = self.df[mask].copy()

        # Si no hay datos para este filtro, usar cualquier periodo disponible
        if df_filt.empty:
            df_filt = self.df[self.df["pabellon"] == pabellon].copy()
        if df_filt.empty:
            df_filt = self.df.copy()

        df_filt = df_filt.head(15)  # Limitar para rendimiento

        secciones = []
        modelo_reg = self.modelos["Regresión Lineal Múltiple"]["modelo"]

        for idx, row in df_filt.iterrows():
            # --- Regresión: predecir demanda ---
            X_pred = pd.DataFrame([{
                "alumnos_nuevos": int(row["alumnos_nuevos"]),
                "alumnos_prerrequisito": int(row["alumnos_prerrequisito"]),
                "alumnos_repitentes": int(row["alumnos_repitentes"]),
                "docente_disponible": int(row["docente_disponible"]),
                "capacidad_aula": int(row["capacidad_aula"]),
                "duracion_semanas": int(row["duracion_semanas"]),
                "laboratorio": int(row["laboratorio"])
            }])
            demanda_pred = max(1, int(round(float(modelo_reg.predict(X_pred)[0]))))

            # --- Clustering: clasificar estado de eficiencia ---
            X_cluster = np.array([[demanda_pred, int(row["capacidad_aula"])]])
            km_temp = KMeans(n_clusters=3, n_init=10, random_state=42)
            # Entrenar con los datos globales para tener centroides coherentes
            datos_globales = self.df[["alumnos_matriculados", "capacidad_aula"]].values
            km_temp.fit(datos_globales)
            cluster_id = int(km_temp.predict(X_cluster)[0])

            # Mapear cluster a etiqueta
            centroides = km_temp.cluster_centers_
            ratios = [c[0] / c[1] if c[1] > 0 else 0 for c in centroides]
            orden = sorted(range(3), key=lambda i: ratios[i])
            roles = {orden[0]: "Sub", orden[1]: "Óptimo", orden[2]: "Sobre"}
            etiqueta_cluster = roles.get(cluster_id, "Óptimo")

            secciones.append({
                "sid": f"S-{row['id_curso']}-{idx}",
                "curso": row["nombre_curso"],
                "docente_id": int(row["docente_id"]),
                "demanda": demanda_pred,
                "laboratorio": int(row["laboratorio"]),
                "turno_pref": turno,
                "cluster": etiqueta_cluster
            })

        return secciones

    # --- Ejecutar el Algoritmo Genético -----------------------------------
    def _ejecutar_horarios_ag(self):
        periodo = self._hd_periodo.get()
        pabellon = self._hd_pabellon.get()
        turno = self._hd_turno.get()

        # Aulas disponibles
        aulas_df = (self.df[self.df["pabellon"] == pabellon]
                    [["aula_id", "capacidad_aula", "pabellon"]]
                    .drop_duplicates())
        aulas = aulas_df.to_dict('records')
        if not aulas:
            aulas = [{"aula_id": 100 + i, "capacidad_aula": 40,
                      "pabellon": pabellon} for i in range(8)]

        # Horarios (15 slots: L-V × 3 turnos)
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        turnos_dia = ["Mañana", "Tarde", "Noche"]
        horarios = [{"dia": d, "turno": t} for d in dias for t in turnos_dia]

        # Secciones (con predicción IA + clustering)
        secciones = self._hd_preparar_secciones(periodo, pabellon, turno)
        if not secciones:
            messagebox.showwarning("Sin datos",
                                   "No se encontraron secciones para el filtro seleccionado.")
            return

        # Instanciar AG
        ag = self._OptimizadorGenetico(
            aulas=aulas,
            horarios=horarios,
            secciones=secciones,
            tam_poblacion=self._hd_pop.get(),
            generaciones=self._hd_gen.get(),
            tasa_mutacion=self._hd_mut.get()
        )

        gen_x, fit_y, best_y = [], [], []
        t0 = time.time()
        generador = ag.optimizar()
        n_gen = self._hd_gen.get()

        def paso():
            try:
                g, f_act, f_best, _, confs = next(generador)
                gen_x.append(g)
                fit_y.append(f_act)
                best_y.append(f_best)

                self._hd_lbl_fit.config(
                    text=f"Mejor Fitness: {f_best:.6f}  (Gen {g + 1})",
                    fg=COLOR_OPTIMO if f_best > 0.002 else ROJO_UTP)
                self._hd_lbl_conf.config(
                    text=f"Conflictos: {len(confs)}",
                    fg=ROJO_UTP if confs else COLOR_OPTIMO)
                self._hd_lbl_time.config(
                    text=f"Tiempo: {time.time() - t0:.2f} s")

                if g % 5 == 0 or g == n_gen - 1:
                    self._hd_render_curva(gen_x, fit_y, best_y)

                self.root.after(5, paso)
            except StopIteration:
                self._hd_finalizar(ag, gen_x, fit_y, best_y, t0)

        paso()

    # --- Actualizar gráfico de convergencia --------------------------------
    def _hd_render_curva(self, gx, fy, by):
        for w in self._hd_panel_graf.winfo_children():
            w.destroy()
        if self._hd_fig is not None:
            plt.close(self._hd_fig)

        self._hd_fig, ax = plt.subplots(figsize=(8, 2.6))
        self._hd_fig.patch.set_facecolor(BLANCO)
        ax.set_facecolor("#F9F9F9")
        ax.plot(gx, fy, label="Fitness Generación", color=ROJO_CLARO, alpha=0.55)
        ax.plot(gx, by, label="Mejor Histórico", color=COLOR_OPTIMO, linewidth=2)
        ax.set_title("Convergencia del Algoritmo Genético", fontsize=11, pad=8)
        ax.set_xlabel("Generación", fontsize=9)
        ax.set_ylabel("Fitness", fontsize=9)
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(self._hd_fig, master=self._hd_panel_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- Mostrar tabla de resultados y mensaje final ----------------------
    def _hd_finalizar(self, ag, gx, fy, by, t0):
        self._hd_render_curva(gx, fy, by)
        cromosoma = ag.mejor_cromosoma
        if cromosoma is None:
            return

        for item in self._hd_tree.get_children():
            self._hd_tree.delete(item)

        _, conflictos = ag.calcular_fitness(cromosoma)

        for i_sec, gen in enumerate(cromosoma):
            ia, ih = ag.espacio[gen]
            aula = ag.aulas[ia]
            hor = ag.horarios[ih]
            sec = ag.secciones[i_sec]

            flab = 0.85 if sec['laboratorio'] == 1 else 1.0
            cap_ef = int(aula['capacidad_aula'] * flab)
            ratio = sec['demanda'] / cap_ef
            estado, _ = self._clasificar_ocupacion(ratio)

            self._hd_tree.insert("", "end", values=(
                sec["sid"],
                sec["curso"],
                sec["docente_id"],
                f"Aula {aula['aula_id']} ({aula.get('pabellon', '')})",
                cap_ef,
                f"{hor['dia']} ({hor['turno']})",
                f"{ratio * 100:.1f}%",
                f"{estado}  [{sec.get('cluster', '')}]"
            ))

        dt = time.time() - t0
        if not conflictos:
            messagebox.showinfo(
                "Optimización Completada",
                f"Distribución optimizada sin conflictos.\n\n"
                f"Generaciones: {len(gx)}\n"
                f"Tiempo: {dt:.2f} s\n"
                f"Fitness óptimo: {by[-1]:.6f}")
        else:
            messagebox.showwarning(
                "Optimización con Advertencias",
                f"Quedan {len(conflictos)} conflicto(s) tras {len(gx)} generaciones.\n\n"
                + "\n".join(conflictos[:4])
                + "\n\nSugerencia: aumente la población o las generaciones.")


# ==============================
# INICIALIZACIÓN
# ==============================
if __name__ == "__main__":
    root = tk.Tk()
    app = AppDemandaAulas(root)
    root.mainloop()
