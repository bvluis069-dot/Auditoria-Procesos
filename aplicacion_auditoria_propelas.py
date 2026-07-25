import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Monitor de Auditorías de Propelas",
    page_icon="⚙️",
    layout="wide"
)

ACTIVAS_FILE = "auditorias_activas.csv"
HISTORIAL_FILE = "hoja_de_procesos_agitacion.csv"

# Catálogo de Propelas disponibles en planta
LISTA_PROPELAS = [
    "Propela 01 - Agitador Neumático 100L",
    "Propela 02 - Disco Cowles Alta Velocidad",
    "Propela 03 - Agitador Servomotor Principal",
    "Propela 04 - Propela Marina Heavy Duty",
    "Propela 05 - Tanque Pigmentos Central",
    "Propela 06 - Mezclador Auxiliar Línea Solventes"
]

# ---------------------------------------------------------
# REGLAS DE TIEMPO POR PESO
# ---------------------------------------------------------
def calcular_regla_tiempo(peso_kg):
    """
    Reglas de Agitación:
    - 0 kg a 200 kg   --> 10 min
    - 200 kg a 500 kg --> 15 a 20 min
    - Más de 500 kg   --> 25 a 30 min
    """
    if peso_kg <= 200:
        tiempo_target = 10.0
        rango_str = "10 min"
        min_p, max_p = 10.0, 10.0
    elif 200 < peso_kg <= 500:
        tiempo_target = 17.5  # Objetivo medio
        rango_str = "15 a 20 min"
        min_p, max_p = 15.0, 20.0
    else:  # > 500 kg
        tiempo_target = 27.5  # Objetivo medio
        rango_str = "25 a 30 min"
        min_p, max_p = 25.0, 30.0
        
    return tiempo_target, rango_str, min_p, max_p

# ---------------------------------------------------------
# FUNCIONES PARA MANEJO DE ARCHIVOS Y DATOS
# ---------------------------------------------------------
def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        return pd.read_csv(ACTIVAS_FILE)
    return pd.DataFrame(columns=[
        "ID", "Propela", "Orden_Fabricacion", "Peso_Kg", 
        "Tiempo_Target_Min", "Min_Permitido", "Max_Permitido", 
        "Rango_Str", "Hora_Inicio", "Auditor"
    ])

def guardar_activas(df):
    df.to_csv(ACTIVAS_FILE, index=False)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return pd.DataFrame(columns=[
        "Fecha_Hora_Fin", "Propela", "Orden_Fabricacion", "Peso_Kg", 
        "Tiempo_Std_Min", "Rango_Permitido", "Tiempo_Real_Min", 
        "Estatus", "Auditor", "Observaciones"
    ])

def guardar_en_historial(registro):
    df_actual = cargar_historial()
    nuevo_df = pd.DataFrame([registro])
    df_actualizado = pd.concat([df_actual, nuevo_df], ignore_index=True)
    df_actualizado.to_csv(HISTORIAL_FILE, index=False)

# ---------------------------------------------------------
# NAVEGACIÓN Y MENÚ LATERAL
# ---------------------------------------------------------
st.sidebar.title("⚙️ Control de Auditorías")
menu = st.sidebar.radio(
    "Selecciona una opción:", 
    ["🔴 Monitor en Vivo (Pendientes/Activas)", "➕ Nueva Auditoría / Agitación", "📊 Hoja de Procesos (Historial)"]
)

# Botón para refrescar tiempos
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Tiempos / Monitor", use_container_width=True):
    st.rerun()

# ---------------------------------------------------------
# OP1: MONITOR EN VIVO (MÚLTIPLES AGITACIONES SIMULTÁNEAS)
# ---------------------------------------------------------
if menu == "🔴 Monitor en Vivo (Pendientes/Activas)":
    st.title("🖥️ Monitor de Agitaciones en Proceso")
    st.caption("Control en tiempo real de agitadores funcionando en planta")
    
    df_activas = cargar_activas()
    
    if df_activas.empty:
        st.success("✅ No hay agitaciones activas en este momento. Todas las propelas están libres o detenidas.")
    else:
        st.subheader(f"⚡ Agitaciones en Curso: {len(df_activas)}")
        
        ahora = datetime.now()
        
        for idx, row in df_activas.iterrows():
            hora_inicio = datetime.strptime(row["Hora_Inicio"], "%Y-%m-%d %H:%M:%S")
            minutos_transcurridos = (ahora - hora_inicio).total_seconds() / 60.0
            
            # Formato de la tarjeta por propela
            with st.container():
                cols = st.columns([3, 2, 2])
                
                with cols[0]:
                    st.markdown(f"### 🌀 {row['Propela']}")
                    st.write(f"**OF / Lote:** {row['Orden_Fabricacion']} | **Peso:** {row['Peso_Kg']} kg | **Auditor:** {row['Auditor']}")
                    st.write(f"**Rango de Especificación:** {row['Rango_Str']}")
                
                with cols[1]:
                    st.metric("Tiempo Transcurrido", f"{minutos_transcurridos:.1f} min", delta=f"Objetivo: {row['Rango_Str']}")
                    st.caption(f"Inicio: {hora_inicio.strftime('%H:%M:%S')}")
                
                with cols[2]:
                    # Evaluar si requiere apagado inmediato
                    if minutos_transcurridos >= row["Min_Permitido"]:
                        st.markdown(
                            f"""
                            <div style="background-color: #D32F2F; padding: 15px; border-radius: 8px; text-align: center; color: white; font-weight: bold; animation: blinker 1.5s linear infinite;">
                                🚨 ¡ALERTA RED! <br>
                                <span style="font-size: 20px;">¡APAGAR PROPELA!</span><br>
                                Tiempo cumplido ({minutos_transcurridos:.1f} min)
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        tiempo_restante = row["Min_Permitido"] - minutos_transcurridos
                        st.info(f"⏳ Agitando... Faltan aprox. {tiempo_restante:.1f} min para apagado.")

                # Acción para Finalizar Auditoría
                with st.expander(f"🛑 Finalizar y Registrar {row['Propela']}"):
                    obs = st.text_input(f"Observaciones para OF {row['Orden_Fabricacion']}:", key=f"obs_{row['ID']}")
                    
                    if st.button(f"Confirmar Apagado y Guardar", key=f"btn_fin_{row['ID']}"):
                        tiempo_final = round(minutos_transcurridos, 1)
                        
                        # Determinar si cumplió el rango
                        cumple = (row["Min_Permitido"] <= tiempo_final <= row["Max_Permitido"])
                        estatus = "CUMPLE" if cumple else "DESVIACIÓN"
                        
                        # Guardar en Hoja de Procesos
                        registro_hist = {
                            "Fecha_Hora_Fin": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Propela": row["Propela"],
                            "Orden_Fabricacion": row["Orden_Fabricacion"],
                            "Peso_Kg": row["Peso_Kg"],
                            "Tiempo_Std_Min": row["Tiempo_Target_Min"],
                            "Rango_Permitido": row["Rango_Str"],
                            "Tiempo_Real_Min": tiempo_final,
                            "Estatus": estatus,
                            "Auditor": row["Auditor"],
                            "Observaciones": obs if obs else "Sin novedades"
                        }
                        guardar_en_historial(registro_hist)
                        
                        # Remover de activas
                        df_activas = df_activas[df_activas["ID"] != row["ID"]]
                        guardar_activas(df_activas)
                        
                        st.success(f"✅ Agitación de {row['Propela']} registrada correctamente.")
                        st.rerun()

            st.markdown("---")

# ---------------------------------------------------------
# OP2: REGISTRAR NUEVA AGITACIÓN
# ---------------------------------------------------------
elif menu == "➕ Nueva Auditoría / Agitación":
    st.title("➕ Iniciar Nueva Agitación")
    st.caption("Configura y pon en marcha una propela")

    df_activas = cargar_activas()
    
    with st.form("form_nueva_agitacion"):
        col1, col2 = st.columns(2)
        
        with col1:
            propela = st.selectbox("Seleccionar Propela / Agitador:", LISTA_PROPELAS)
            orden_fab = st.text_input("Orden de Fabricación / Lote:", placeholder="Ej. OF-1582548")
            peso_kg = st.number_input("Peso del Lote (kg):", min_value=0.0, max_value=10000.0, value=150.0, step=10.0)
            auditor = st.text_input("Auditor / Operador Responsable:", placeholder="Ej. Juan Pérez")
            
        with col2:
            tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(peso_kg)
            st.info("📋 **Regla de Operación Aplicada:**")
            st.markdown(f"* **Rango Requerido:** `{rango_str}`")
            st.markdown(f"* **Tiempo Objetivo:** `{tiempo_target} min`")
            st.write("---")
            
            # Verificar si la propela ya está ocupada
            propelas_ocupadas = df_activas["Propela"].tolist() if not df_activas.empty else []
            if propela in propelas_ocupadas:
                st.warning(f"⚠️ ¡Atención! La **{propela}** ya está en ejecución en el Monitor.")

        btn_iniciar = st.form_submit_button("🚀 Iniciar Agitación y Monitorear", use_container_width=True)

    if btn_iniciar:
        if not orden_fab or not auditor:
            st.error("❌ Por favor completa la Orden de Fabricación y el Nombre del Auditor.")
        elif propela in df_activas["Propela"].tolist():
            st.error(f"❌ La {propela} ya está ocupada. Finaliza la agitación anterior en el Monitor antes de iniciar otra.")
        else:
            nuevo_id = int(datetime.now().timestamp())
            nueva_fila = {
                "ID": nuevo_id,
                "Propela": propela,
                "Orden_Fabricacion": orden_fab,
                "Peso_Kg": peso_kg,
                "Tiempo_Target_Min": tiempo_target,
                "Min_Permitido": min_p,
                "Max_Permitido": max_p,
                "Rango_Str": rango_str,
                "Hora_Inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Auditor": auditor
            }
            
            df_actualizado = pd.concat([df_activas, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_activas(df_actualizado)
            
            st.success(f"✅ Agitación iniciada para **{propela}**. Ya la puedes monitorear en tiempo real.")
            st.balloons()

# ---------------------------------------------------------
# OP3: HOJA DE PROCESOS (HISTORIAL DIGITAL)
# ---------------------------------------------------------
elif menu == "📊 Hoja de Procesos (Historial)":
    st.title("📊 Hoja de Procesos Digital")
    st.caption("Registro histórico y auditoría de tiempos de agitación")
    
    df_historial = cargar_historial()
    
    if df_historial.empty:
        st.info("Aún no hay registros de agitaciones finalizadas.")
    else:
        # Métricas generales
        total = len(df_historial)
        cumplidos = len(df_historial[df_historial["Estatus"] == "CUMPLE"])
        desviaciones = total - cumplidos
        pct = (cumplidos / total) * 100 if total > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Registro Auditorías", total)
        c2.metric("Conformes (Dentro de Rango)", cumplidos)
        c3.metric("Desviaciones", desviaciones, delta_color="inverse")
        c4.metric("% Cumplimiento", f"{pct:.1f}%")
        
        st.markdown("---")
        
        # Tabla interactiva
        st.dataframe(df_historial, use_container_width=True)
        
        # Descarga
        csv_data = df_historial.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Hoja de Procesos en CSV",
            data=csv_data,
            file_name=f"hoja_de_procesos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
