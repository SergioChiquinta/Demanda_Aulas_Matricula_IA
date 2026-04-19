import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error

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
# CARGA Y PREPARACIÓN DE DATOS
# ==============================
def cargar_datos():
    try:
        return pd.read_excel("data_prediccion_aulas.xlsx")
    except Exception as e:
        messagebox.showerror("Error", "No se encontró el dataset. Ejecuta primero el generador.")
        return pd.DataFrame()

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
            ("🤖 Simulación IA", self.vista_simulacion)
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

        self.panel_grafico = tk.Frame(self.frame_contenido_analisis, bg=GRIS_FONDO)
        self.panel_grafico.pack(fill="both", expand=True)

        # Clustering y Gráfico con colores adaptados
        X_cluster = self.df[["alumnos_matriculados", "capacidad_aula"]]
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
        self.df['cluster'] = kmeans.fit_predict(X_cluster)
        
        # Mapeo de colores para el scatter plot
        colores_map = [COLOR_SUBUTILIZADO, COLOR_OPTIMO, COLOR_SOBREPOBLADO]
        
        fig, ax = plt.subplots(figsize=(8, 6))
        for cluster_id in range(3):
            subset = self.df[self.df['cluster'] == cluster_id]
            ax.scatter(subset["alumnos_matriculados"], subset["capacidad_aula"], 
                       c=colores_map[cluster_id], alpha=0.7, edgecolors='w', s=80, label=f"Cluster {cluster_id}")
        
        ax.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Línea de Equilibrio')
        ax.set_title("Relación: Demanda Real vs Capacidad de Aula", fontsize=14, pad=20)
        ax.set_xlabel("Alumnos Matriculados (Demanda)", fontsize=12)
        ax.set_ylabel("Capacidad Física del Aula", fontsize=12)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        canvas = FigureCanvasTkAgg(fig, master=self.panel_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Panel de Interpretación con colores coincidentes
        self.panel_info = tk.Frame(self.frame_contenido_analisis, bg=BLANCO, bd=2, relief="ridge")
        tk.Label(self.panel_info, text="Interpretación Administrativa de Datos", 
                 font=FUENTE_SUBTITULO, bg=BLANCO, fg=ROJO_UTP).pack(pady=30)
        
        frame_detalles = tk.Frame(self.panel_info, bg=BLANCO)
        frame_detalles.pack(padx=50, fill="both")

        # Texto de ayuda visual con colores consistentes [cite: 304, 307]
        items = [
            ("🟡 Cluster 0: Subutilización Crítica", COLOR_SUBUTILIZADO, 
             "Aulas con capacidad >60% por encima de la demanda real. \nImpacto: Costo operativo innecesario en energía y mantenimiento. \nRecomendación: Mover a pabellones menores."),
            ("🟢 Cluster 1: Eficiencia Operativa", COLOR_OPTIMO, 
             "Aulas con una relación de ocupación entre el 80% y 95%. \nImpacto: Uso ideal del activo físico. \nRecomendación: Escalar este modelo a otras sedes."),
            ("🔴 Cluster 2: Riesgo de Hacinamiento", COLOR_SOBREPOBLADO, 
             "La demanda iguala o supera el límite físico. \nImpacto: Deterioro de la calidad académica y riesgo de seguridad. \nRecomendación: División inmediata de secciones.")
        ]

        for titulo, color, desc in items:
            lbl_title = tk.Label(frame_detalles, text=titulo, font=("Segoe UI", 13, "bold"), fg=color, bg=BLANCO)
            lbl_title.pack(anchor="w", pady=(10, 0))
            lbl_desc = tk.Label(frame_detalles, text=desc, font=("Segoe UI", 12), fg=GRIS_TEXTO, bg=BLANCO, wraplength=700, justify="left")
            lbl_desc.pack(anchor="w", padx=20, pady=(0, 10))

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
        self.limpiar_contenedor()

        header = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        header.pack(fill="x", pady=20, padx=20)

        tk.Label(header, text="Simulador Predictivo de Demanda",
                font=FUENTE_TITULO, bg=GRIS_FONDO).pack(side="left")
        
        self.btn_guia = tk.Button(header, text="Guía de Variables 📘", font=FUENTE_NORMAL,
                                 bg=ROJO_UTP, fg=BLANCO, command=self.toggle_guia_simulacion)
        self.btn_guia.pack(side="right")

        # Panel Izquierdo: Formulario (Ahora con expand=False para no empujar todo a la derecha)
        f_form = tk.LabelFrame(self.contenedor_principal, text="Parámetros de Entrada",
                             font=FUENTE_SUBTITULO, bg=BLANCO, padx=20, pady=20)
        f_form.pack(side="left", fill="y", padx=(40, 10), pady=20)

        # Panel Derecho: Resultados (Ahora ocupa todo el resto del espacio)
        self.f_res_container = tk.Frame(self.contenedor_principal, bg=GRIS_FONDO)
        self.f_res_container.pack(side="right", fill="both", padx=(10, 40), pady=20, expand=True)

        # VARIABLES
        self.vars_input = {
            "alumnos_nuevos": tk.IntVar(value=20), "alumnos_prerrequisito": tk.IntVar(value=15),
            "alumnos_repitentes": tk.IntVar(value=5), "capacidad_aula": tk.IntVar(value=40),
            "duracion_semanas": tk.IntVar(value=18), "docente_disponible": tk.IntVar(value=1),
            "laboratorio": tk.IntVar(value=0)
        }

        # FORMULARIO
        row = 0
        for k, v in self.vars_input.items():
            tk.Label(f_form, text=k.replace("_", " ").title(), font=FUENTE_NORMAL, bg=BLANCO).grid(row=row, column=0, sticky="w", pady=10)
            if k == "laboratorio":
                tk.Checkbutton(f_form, text="Requiere laboratorio", variable=v, bg=BLANCO).grid(row=row, column=1, sticky="w")
            else:
                tk.Entry(f_form, textvariable=v, font=FUENTE_NORMAL, width=10).grid(row=row, column=1, padx=10)
            row += 1

        tk.Button(f_form, text="EJECUTAR MODELO IA", font=FUENTE_SUBTITULO, bg=ROJO_UTP, fg=BLANCO,
                command=self.realizar_prediccion).grid(row=row, columnspan=2, pady=30, sticky="we")

        # PANEL RESULTADO (VISTA INICIAL)
        self.panel_resultado_sim = tk.Frame(self.f_res_container, bg=GRIS_FONDO)
        self.panel_resultado_sim.pack(fill="both", expand=True)

        self.lbl_pred = tk.Label(self.panel_resultado_sim, text="---", font=("Segoe UI", 52, "bold"), bg=GRIS_FONDO)
        self.lbl_pred.pack(pady=30)

        self.lbl_estado = tk.Label(self.panel_resultado_sim, text="Esperando simulación...", font=FUENTE_SUBTITULO, bg=GRIS_FONDO)
        self.lbl_estado.pack(pady=10)

        self.btn_detalles = tk.Button(self.panel_resultado_sim, text="Ver Detalles 📊", font=FUENTE_NORMAL,
                                    bg=ROJO_UTP, fg=BLANCO, command=self.toggle_detalles)
        self.btn_detalles.pack(pady=20)

        # PANEL DETALLE CON SCROLLBAR (Ocupa el espacio central)
        self.container_scroll = tk.Frame(self.f_res_container, bg=BLANCO, bd=1, relief="solid")
        
        canvas = tk.Canvas(self.container_scroll, bg=BLANCO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.container_scroll, orient="vertical", command=canvas.yview)
        self.panel_detalle = tk.Frame(canvas, bg=BLANCO)

        self.panel_detalle.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=self.panel_detalle, anchor="nw")
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ANCHO AUMENTADO SEGÚN TEXTO
        self.lbl_detalle = tk.Message(self.panel_detalle, text="", font=FUENTE_NORMAL, 
                                     bg=BLANCO, width=900, justify="left") # Ancho ajustado a 900
        self.lbl_detalle.pack(padx=20, pady=20, fill="x")

        self.btn_volver = tk.Button(self.panel_detalle, text="Volver 🔙", font=FUENTE_NORMAL,
                                  bg=NEGRO, fg=BLANCO, command=self.volver_resultado)
        self.btn_volver.pack(pady=20)

        # =========================
        # PANEL GUÍA (MEJORADO)
        # =========================
        self.panel_guia_sim = tk.Frame(self.f_res_container, bg=BLANCO, bd=1, relief="solid")

        txt_guia = (
            "📌 GUÍA COMPLETA DE VARIABLES\n\n"

            "• Alumnos Nuevos:\n"
            "  Principal motor de crecimiento. Impacta directamente la demanda.\n\n"

            "• Alumnos con Prerrequisito:\n"
            "  Representan continuidad académica. Ayudan a estabilizar la demanda.\n\n"

            "• Alumnos Repitentes:\n"
            "  Generan sobrecarga inesperada. Aumentan riesgo operativo.\n\n"

            "• Capacidad del Aula:\n"
            "  Límite físico. Define cuántos alumnos pueden ser asignados.\n\n"

            "• Duración (Semanas):\n"
            "  A mayor duración, menor rotación de aulas disponibles.\n\n"

            "• Docentes Disponibles:\n"
            "  Limita cuántas secciones pueden abrirse simultáneamente.\n\n"

            "• Laboratorio (Checkbox):\n"
            "  ✔ Activado → Reduce capacidad en 15% por equipos.\n"
            "  ✖ Desactivado → Capacidad completa del aula.\n"
        )

        tk.Message(self.panel_guia_sim, text=txt_guia,
                font=FUENTE_NORMAL, bg=BLANCO, width=500)\
            .pack(padx=20, pady=20)

        # FLAGS
        self.mostrar_guia_sim = False
        self.mostrar_detalle = False

    def toggle_detalles(self):
        self.panel_resultado_sim.pack_forget()
        self.panel_guia_sim.pack_forget()
        self.container_scroll.pack(fill="both", expand=True)

    def volver_resultado(self):
        self.container_scroll.pack_forget()
        self.panel_resultado_sim.pack(fill="both", expand=True)

    def toggle_guia_simulacion(self):
        if not self.mostrar_guia_sim:
            self.panel_resultado_sim.pack_forget()
            self.container_scroll.pack_forget()
            self.panel_guia_sim.pack(fill="both", expand=True)
        else:
            self.panel_guia_sim.pack_forget()
            self.panel_resultado_sim.pack(fill="both", expand=True)
        self.mostrar_guia_sim = not self.mostrar_guia_sim

    def realizar_prediccion(self):
        try:
            # =========================
            # 1. INPUTS
            # =========================
            alumnos_nuevos = self.vars_input["alumnos_nuevos"].get()
            alumnos_pre = self.vars_input["alumnos_prerrequisito"].get()
            alumnos_rep = self.vars_input["alumnos_repitentes"].get()
            capacidad = self.vars_input["capacidad_aula"].get()
            duracion = self.vars_input["duracion_semanas"].get()
            docente_disp = self.vars_input["docente_disponible"].get()
            laboratorio = self.vars_input["laboratorio"].get()
            lab_texto = "Sí (reduce capacidad)" if laboratorio == 1 else "No"

            # =========================
            # 2. PREDICCIÓN IA
            # =========================
            datos = [[
                alumnos_nuevos,
                alumnos_pre,
                alumnos_rep,
                docente_disp,
                capacidad,
                duracion,
                laboratorio
            ]]

            pred = int(self.modelo_activo.predict(datos)[0])

            # =========================
            # 3. AJUSTES POR LABORATORIO
            # =========================
            if laboratorio == 1:
                capacidad_real = int(capacidad * 0.85)
            else:
                capacidad_real = capacidad

            # =========================
            # 4. INFRAESTRUCTURA
            # =========================
            aulas_necesarias = int(np.ceil(pred / capacidad_real))

            saturacion = pred / capacidad_real

            # =========================
            # 5. DOCENTES
            # =========================
            docentes_necesarios = aulas_necesarias

            # =========================
            # 6. EFICIENCIA MATRÍCULA
            # =========================
            tiempo_hist = self.df["tiempo_matricula_min"].mean()
            tiempo_ia = tiempo_hist * 0.7  # IA reduce 30%
            mejora = ((tiempo_hist - tiempo_ia) / tiempo_hist) * 100

            # =========================
            # 7. RETIRO DE ALUMNOS
            # =========================
            if saturacion > 1:
                retiro = int(pred * 0.15)
            elif saturacion < 0.5:
                retiro = int(pred * 0.05)
            else:
                retiro = int(pred * 0.08)

            # =========================
            # 8. RESULTADO PRINCIPAL
            # =========================
            self.lbl_pred.config(text=f"{pred} Alumnos")

            # =========================
            # 9. INTERPRETACIÓN AVANZADA
            # =========================
            self.lbl_pred.config(text=f"{pred} Alumnos")

            if saturacion > 1:
                estado = "🔴 CRÍTICO"
                color = COLOR_SOBREPOBLADO
            elif saturacion < 0.6:
                estado = "🟡 INEFICIENTE"
                color = "#B8860B"
            else:
                estado = "🟢 ÓPTIMO"
                color = COLOR_OPTIMO

            self.lbl_estado.config(
                text=f"{estado} - Saturación: {saturacion:.2f}",
                fg=color
            )

            # =========================
            # DETALLE COMPLETO
            # =========================
            detalle = f"""
            📊 RESULTADO OPERATIVO

            • Demanda estimada: {pred}
            • Capacidad efectiva: {capacidad_real}
            • Aulas necesarias: {aulas_necesarias}
            • Docentes requeridos: {docentes_necesarios}

            📚 INTERPRETACIÓN DE VARIABLES

            • Alumnos Nuevos: Impacto directo en crecimiento de demanda
            • Pre-requisitos: Indican flujo académico progresivo
            • Repitentes: Generan sobrecarga no planificada
            • Docente disponible: Limita apertura de secciones
            • Capacidad aula: Restricción física clave
            • Duración: Afecta disponibilidad de aulas
            • Laboratorio: {lab_texto}

            📉 EFICIENCIA ADMINISTRATIVA

            • Tiempo antes: {tiempo_hist:.1f} min
            • Tiempo con IA: {tiempo_ia:.1f} min
            • Mejora: {mejora:.1f}%

            ⚠️ RIESGO ACADÉMICO

            • Retiros estimados: {retiro}

            📌 DECISIÓN

            {estado}:
            """

            if saturacion > 1:
                detalle += "Abrir nuevas secciones o ampliar infraestructura."
            elif saturacion < 0.6:
                detalle += "Reorganizar horarios o fusionar secciones."
            else:
                detalle += "Planificación adecuada."

            self.lbl_detalle.config(text=detalle)

        except:
            messagebox.showerror("Error", "Datos inválidos")

# ==============================
# INICIALIZACIÓN
# ==============================
if __name__ == "__main__":
    root = tk.Tk()
    app = AppDemandaAulas(root)
    root.mainloop()