import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema Integral de Auditoría de Procesos - Agitación",
    page_icon="⚙️",
    layout="wide"
)

ACTIVAS_FILE = "auditorias_activas.csv"
HISTORIAL_FILE = "hoja_de_procesos_agitacion.csv"

# Catálogo de Propelas / Agitadores disponibles
LISTA_PROPELAS = [
    "Propela 01 - Agitador Neumático 100L",
    "Propela 02 - Disco Cowles Alta Velocidad",
    "Propela 03 - Agitador Servomotor Principal",
    "Propela 04 - Propela Marina Heavy Duty",
    "Propela 05 - Tanque Pigmentos Central",
    "Propela 06 - Mezclador Auxiliar Línea Solventes"
]

# ---------------------------------------------------------
# REGLAS DE TIEMPO POR CAPACIDAD / PESO
# ---------------------------------------------------------
def calcular_regla_tiempo(peso_kg):
    """
    Matriz de Tiempos Estándar:
    - 0 kg a 200 kg   --> 10 min
    - 200 kg a 500 kg --> 15 a 20 min (Obj: 17.5 min)
    - > 500 kg        --> 25 a 30 min (Obj: 27.5 min)
    """
    if peso_kg <= 200:
        tiempo_target = 10.0
        rango_str = "10 min"
        min_p, max_p = 10.0, 10.0
    elif 200 < peso_kg <= 500:
        tiempo_target = 17.5
        rango_str = "15 a 20 min"
        min_p, max_p = 15.0, 20.0
    else:
        tiempo_target = 27.5
        rango_str = "25 a 30 min"
        min_p, max_p = 25.0, 30.0
        
    return tiempo_target, rango_str, min_p, max_p

# ---------------------------------------------------------
# MANEJO DE PERSISTENCIA DE DATOS
# ---------------------------------------------------------
def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        return pd.read_csv(ACTIVAS_FILE)
    return pd.DataFrame(columns=[
        "ID", "Propela", "Orden_Fabricacion", "Peso_Kg", 
        "Estado_Limpieza", "RPM", "Temperatura_C", "Viscosidad",
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
        "Estado_Limpieza", "RPM", "Temperatura_C", "Viscosidad",
        "Tiempo_Std_Min", "Rango_Permitido", "Tiempo_Real_Min", 
        "Estatus", "Paro_Emergencia", "Auditor", "Observaciones"
    ])

def guardar_en_historial(registro):
    df_actual = cargar_historial()
    nuevo_df = pd.DataFrame([registro])
    df_actualizado = pd.concat([df_actual, nuevo_df], ignore_index=True)
    df_actualizado.to_csv(HISTORIAL_FILE, index=False)

# ---------------------------------------------------------
# MENÚ LATERAL Y NAVEGACIÓN
# ---------------------------------------------------------
st.sidebar.title("⚙️ Auditoría de Procesos")
menu = st.sidebar.radio(
    "Menú de Operación:", 
    [
        "🔴 Monitor en Vivo (Pendientes/Activas)", 
        "➕ Nueva Auditoría / Agitación", 
        "📊 Hoja de Procesos (Historial Digital)"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refrescar Monitor", use_container_width=True):
    st.rerun()

# ---------------------------------------------------------
# 1. MONITOR EN VIVO (MÚLTIPLES PROPELAS SIMULTÁNEAS)
# ---------------------------------------------------------
if menu == "🔴 Monitor en Vivo (Pendientes/Activas)":
    st.title("🖥️ Monitor Operativo de Agitación en Planta")
    st.caption("Panel de control en tiempo real con alertas de seguridad y temporización")
    
    df_activas = cargar_activas()
    
    if df_activas.empty:
        st.success("✅ No hay agitaciones activas en este momento. Todos los equipos están disponibles.")
    else:
        st.subheader(f"⚡ Agitaciones en Ejecución: {len(df_activas)}")
        ahora = datetime.now()
        
        for idx, row in df_activas.iterrows():
            hora_inicio = datetime.strptime(row["Hora_Inicio"], "%Y-%m-%d %H:%M:%S")
            minutos_transcurridos = (ahora - hora_inicio).total_seconds() / 60.0
            
            with st.container():
                c_info, c_time, c_alert = st.columns([3, 2, 2.5])
                
                with c_info:
                    st.markdown(f"### 🌀 {row['Propela']}")
                    st.write(f"**OF / Lote:** `{row['Orden_Fabricacion']}` | **Peso:** `{row['Peso_Kg']} kg` | **Auditor:** `{row['Auditor']}`")
                    st.write(f"🧼 **Limpieza:** `{row['Estado_Limpieza']}` | ⚡ **RPM:** `{row['RPM']}` | 🌡️ **Temp:** `{row['Temperatura_C']} °C` | 🧪 **Viscosidad:** `{row['Viscosidad']}`")
                    st.caption(f"Especificación: {row['Rango_Str']} | Inicio: {hora_inicio.strftime('%H:%M:%S')}")
                
                with c_time:
                    st.metric("Tiempo Transcurrido", f"{minutos_transcurridos:.1f} min", delta=f"Rango: {row['Rango_Str']}")
                
                with c_alert:
                    # EVALUACIÓN DE ALERTA ROJA VISUAL
                    if minutos_transcurridos >= row["Min_Permitido"]:
                        st.markdown(
                            f"""
                            <div style="background-color: #B71C1C; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; border: 2px solid #FF5252;">
                                <h2 style="color: #FFFFFF; margin:0; font-size: 24px;">🚨 ¡ALERTA RED!</h2>
                                <h3 style="color: #FFEB3B; margin:5px 0 0 0; font-size: 22px;">¡APAGAR PROPELA!</h3>
                                <p style="margin:5px 0 0 0; font-size: 14px;">Tiempo Cumplido: <b>{minutos_transcurridos:.1f} min</b></p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        falta = row["Min_Permitido"] - minutos_transcurridos
                        st.info(f"⏳ **Agitando normal.**\nFaltan **{falta:.1f} min** para el tiempo mínimo.")

                # MODAL / EXPANDER PARA FINALIZAR AGITACIÓN
                with st.expander(f"🛑 Finalizar Agitación y Auditoría - {row['Propela']}"):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        paro_emergencia = st.checkbox("⚠️ ¿Hubo Paro de Emergencia o Falla?", key=f"paro_{row['ID']}")
                    with col_f2:
                        obs = st.text_input("Observaciones / Desviaciones:", key=f"obs_{row['ID']}", placeholder="Ej. Cambio de tonalidad, muestra a laboratorio OK...")
                    
                    if st.button("💾 Confirmar Apagado y Enviar a Hoja de Procesos", key=f"btn_fin_{row['ID']}", use_container_width=True):
                        tiempo_final = round(minutos_transcurridos, 1)
                        cumple = (row["Min_Permitido"] <= tiempo_final <= row["Max_Permitido"]) and not paro_emergencia
                        
                        if paro_emergencia:
                            estatus = "PARO DE EMERGENCIA"
                        elif cumple:
                            estatus = "CUMPLE"
                        else:
                            estatus = "DESVIACIÓN"
                        
                        registro_hist = {
                            "Fecha_Hora_Fin": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Propela": row["Propela"],
                            "Orden_Fabricacion": row["Orden_Fabricacion"],
                            "Peso_Kg": row["Peso_Kg"],
                            "Estado_Limpieza": row["Estado_Limpieza"],
                            "RPM": row["RPM"],
                            "Temperatura_C": row["Temperatura_C"],
                            "Viscosidad": row["Viscosidad"],
                            "Tiempo_Std_Min": row["Tiempo_Target_Min"],
                            "Rango_Permitido": row["Rango_Str"],
                            "Tiempo_Real_Min": tiempo_final,
                            "Estatus": estatus,
                            "Paro_Emergencia": "SÍ" if paro_emergencia else "NO",
                            "Auditor": row["Auditor"],
                            "Observaciones": obs if obs else "Sin novedades"
                        }
                        
                        guardar_en_historial(registro_hist)
                        
                        # Eliminar de la lista de activas
                        df_activas = df_activas[df_activas["ID"] != row["ID"]]
                        guardar_activas(df_activas)
                        
                        st.success(f"✅ Agitación de {row['Propela']} registrada correctamente con estatus: **{estatus}**.")
                        st.rerun()

            st.markdown("---")

# ---------------------------------------------------------
# 2. CAPTURA DE NUEVA AGITACIÓN / AUDITORÍA
# ---------------------------------------------------------
elif menu == "➕ Nueva Auditoría / Agitación":
    st.title("➕ Registrar e Iniciar Nueva Agitación")
    st.caption("Configuración completa de parámetros operativos antes de iniciar el mezclado")

    df_activas = cargar_activas()
    
    with st.form("form_nueva_agitacion"):
        st.subheader("1. Datos de Identificación y Lote")
        col1, col2 = st.columns(2)
        with col1:
            propela = st.selectbox("Seleccionar Propela / Agitador:", LISTA_PROPELAS)
            orden_fab = st.text_input("Orden de Fabricación / Lote (OF):", placeholder="Ej. OF-1582548")
            auditor = st.text_input("Auditor / Operador Responsable:", placeholder="Ej. Juan Pérez")
        with col2:
            peso_kg = st.number_input("Peso del Lote (kg):", min_value=0.0, max_value=20000.0, value=250.0, step=10.0)
            tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(peso_kg)
            st.info(f"📋 **Especificación de Tiempo:** Rango `{rango_str}` (Objetivo: `{tiempo_target} min`)")

        st.markdown("---")
        st.subheader("2. Verificación Previa y Parámetros Operativos")
        col3, col4, col5 = st.columns(3)
        
        with col3:
            estado_limpieza = st.selectbox(
                "🧼 Inspección de Limpieza (Propela/Bomba):", 
                ["Limpia / Libre de Residuos", "Requiere Lavado Previo", "Inspeccionada con Solvente"]
            )
            rpm = st.number_input("⚡ Velocidad de Agitación (RPM):", min_value=0, max_value=5000, value=1200, step=50)

        with col4:
            temp_c = st.number_input("🌡️ Temperatura Inicial (°C):", min_value=0.0, max_value=120.0, value=25.0, step=0.5)
            viscosidad = st.text_input("🧪 Viscosidad Inicial (Segundos / cP):", value="35 seg Zahn #4")

        with col5:
            st.write("📌 **Verificación de Seguridad:**")
            st.caption("Asegura el cierre de válvulas de descarga y fijación del contenedor antes de arrancar el motor.")

        # Advertencia de propela ocupada
        propelas_ocupadas = df_activas["Propela"].tolist() if not df_activas.empty else []
        if propela in propelas_ocupadas:
            st.warning(f"⚠️ **Atención:** La `{propela}` ya tiene una auditoría en curso en el Monitor.")

        btn_iniciar = st.form_submit_button("🚀 Iniciar Agitación y Registrar en Monitor", use_container_width=True)

    if btn_iniciar:
        if not orden_fab or not auditor:
            st.error("❌ La Orden de Fabricación y el Nombre del Auditor son obligatorios.")
        elif propela in propelas_ocupadas:
            st.error(f"❌ La {propela} ya está ocupada. Finaliza su ciclo actual en el Monitor antes de arrancar de nuevo.")
        else:
            nuevo_id = int(datetime.now().timestamp())
            nueva_fila = {
                "ID": nuevo_id,
                "Propela": propela,
                "Orden_Fabricacion": orden_fab,
                "Peso_Kg": peso_kg,
                "Estado_Limpieza": estado_limpieza,
                "RPM": rpm,
                "Temperatura_C": temp_c,
                "Viscosidad": viscosidad,
                "Tiempo_Target_Min": tiempo_target,
                "Min_Permitido": min_p,
                "Max_Permitido": max_p,
                "Rango_Str": rango_str,
                "Hora_Inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Auditor": auditor
            }
            
            df_actualizado = pd.concat([df_activas, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_activas(df_actualizado)
            
            st.success(f"✅ Agitación iniciada para **{propela}** (OF: {orden_fab}). Monitorea el proceso en la pantalla principal.")
            st.balloons()

# ---------------------------------------------------------
# 3. HOJA DE PROCESOS (HISTORIAL DIGITAL Y AUDITORÍA)
# ---------------------------------------------------------
elif menu == "📊 Hoja de Procesos (Historial Digital)":
    st.title("📊 Hoja de Procesos Digital")
    st.caption("Base de datos de auditorías de agitación, parámetros fisicoquímicos y cumplimiento de especificación")
    
    df_historial = cargar_historial()
    
    if df_historial.empty:
        st.info("No hay registros guardados en la Hoja de Procesos.")
    else:
        # Tarjetas de Métricas de Calidad
        total_regs = len(df_historial)
        cumplidos = len(df_historial[df_historial["Estatus"] == "CUMPLE"])
        desviaciones = len(df_historial[df_historial["Estatus"] == "DESVIACIÓN"])
        paros = len(df_historial[df_historial["Estatus"] == "PARO DE EMERGENCIA"])
        
        pct_cumplimiento = (cumplidos / total_regs) * 100 if total_regs > 0 else 0
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Auditorías", total_regs)
        m2.metric("Conformes (CUMPLE)", cumplidos)
        m3.metric("Desviaciones", desviaciones, delta_color="inverse")
        m4.metric("Paros Emergencia", paros, delta_color="inverse")
        m5.metric("% Cumplimiento", f"{pct_cumplimiento:.1f}%")
        
        st.markdown("---")
        
        # Filtros de búsqueda
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            propelas_unicas = list(df_historial["Propela"].unique())
            filtro_prop = st.multiselect("Filtrar por Propela:", propelas_unicas, default=propelas_unicas)
        with col_f2:
            estatus_unicos = list(df_historial["Estatus"].unique())
            filtro_estatus = st.multiselect("Filtrar por Estatus:", estatus_unicos, default=estatus_unicos)
            
        df_filtrado = df_historial[
            (df_historial["Propela"].isin(filtro_prop)) & 
            (df_historial["Estatus"].isin(filtro_estatus))
        ]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Botón de Descarga
        csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Hoja de Procesos Completa (CSV / Excel)",
            data=csv_bytes,
            file_name=f"hoja_de_procesos_propelas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
