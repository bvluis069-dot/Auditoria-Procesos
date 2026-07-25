import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Auditoría de Procesos - Tiempos de Agitado de Propela",
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
# REGLAS DE TIEMPO POR PESO / CAPACIDAD
# ---------------------------------------------------------
def calcular_regla_tiempo(peso_kg):
    """
    Reglas de Agitación:
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
# MANEJO DE ARCHIVOS Y BASE DE DATOS
# ---------------------------------------------------------
def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        return pd.read_csv(ACTIVAS_FILE)
    return pd.DataFrame(columns=[
        "ID", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS", 
        "Area", "Cantidad_Kg", "Operador", "Supervisor", "Auditor",
        "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza",
        "Limpieza_Propela", "RPM", "Temperatura_C", "Viscosidad",
        "Dificultades_Materiales_JSON", "Tiempo_Target_Min", "Min_Permitido", 
        "Max_Permitido", "Rango_Str", "Hora_Inicio"
    ])

def guardar_activas(df):
    df.to_csv(ACTIVAS_FILE, index=False)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return pd.DataFrame(columns=[
        "Fecha_Hora_Fin", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS",
        "Area", "Cantidad_Kg", "Operador", "Supervisor", "Auditor",
        "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza",
        "Limpieza_Propela", "RPM", "Temperatura_C", "Viscosidad",
        "Tiempo_Std_Min", "Rango_Permitido", "Tiempo_Real_Min", "Tiempo_Prom_Dispersion",
        "Dificultades_Materiales", "Estatus", "Paro_Emergencia",
        "Observaciones", "Firma_Operador", "Firma_Encargado"
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
st.sidebar.caption("Tiempos de Agitado de Propela")

menu = st.sidebar.radio(
    "Selecciona una opción:", 
    [
        "🔴 Monitor en Vivo (Pendientes/Activas)", 
        "📋 Nueva Auditoría (Formato Oficial)", 
        "📊 Hoja de Procesos (Historial Digital)"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Monitor", use_container_width=True):
    st.rerun()

# ---------------------------------------------------------
# OP1: MONITOR EN VIVO
# ---------------------------------------------------------
if menu == "🔴 Monitor en Vivo (Pendientes/Activas)":
    st.title("🖥️ Monitor Operativo en Vivo")
    st.caption("Control de mezcladores y propelas activas en planta")
    
    df_activas = cargar_activas()
    
    if df_activas.empty:
        st.success("✅ No hay agitaciones activas en este momento. Todas las propelas están libres.")
    else:
        st.subheader(f"⚡ Agitaciones en Curso: {len(df_activas)}")
        ahora = datetime.now()
        
        for idx, row in df_activas.iterrows():
            hora_inicio = datetime.strptime(row["Hora_Inicio"], "%Y-%m-%d %H:%M:%S")
            minutos_transcurridos = (ahora - hora_inicio).total_seconds() / 60.0
            
            with st.container():
                c1, c2, c3 = st.columns([3.5, 2, 2.5])
                
                with c1:
                    st.markdown(f"### 🌀 {row['Propela']} — Depto: `{row['Departamento']}`")
                    st.write(f"**Lote / OF:** `{row['Orden_Fabricacion_Lote']}` | **Código PS:** `{row['Codigo_PS']}` | **Cantidad:** `{row['Cantidad_Kg']} kg`")
                    st.write(f"**Área:** `{row['Area']}` | **Op:** `{row['Operador']}` | **Sup:** `{row['Supervisor']}` | **Auditor:** `{row['Auditor']}`")
                    st.caption(f"🧼 Dispensing: {row['Limpieza_Dispensing']} | Propela: {row['Limpieza_Propela']} | RPM: {row['RPM']}")
                
                with c2:
                    st.metric("Tiempo Transcurrido", f"{minutos_transcurridos:.1f} min", delta=f"Rango: {row['Rango_Str']}")
                    st.caption(f"Inicio: {hora_inicio.strftime('%H:%M:%S')}")
                
                with c3:
                    if minutos_transcurridos >= row["Min_Permitido"]:
                        st.markdown(
                            f"""
                            <div style="background-color: #D32F2F; padding: 12px; border-radius: 8px; text-align: center; color: white; font-weight: bold;">
                                🚨 ¡ALERTA RED! <br>
                                <span style="font-size: 18px;">¡APAGAR PROPELA!</span><br>
                                Tiempo cumplido ({minutos_transcurridos:.1f} min)
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        falta = row["Min_Permitido"] - minutos_transcurridos
                        st.info(f"⏳ Agitando... Faltan approx. **{falta:.1f} min**")

                # Cierre y Registro con Firmas
                with st.expander(f"🛑 Finalizar Auditoría y Registrar - {row['Propela']}"):
                    f_col1, f_col2, f_col3 = st.columns(3)
                    
                    with f_col1:
                        tiempo_disp = st.number_input(
                            "⏱️ Tiempo Promedio de Dispersión (min):", 
                            min_value=0.0, value=minutos_transcurridos, step=0.5, key=f"disp_{row['ID']}"
                        )
                        paro_emergencia = st.checkbox("⚠️ Paro de Emergencia / Falla", key=f"paro_{row['ID']}")

                    with f_col2:
                        firma_op = st.text_input("✍️ Firma / Confirmación Operador:", value=row['Operador'], key=f"f_op_{row['ID']}")
                        obs = st.text_area("Observaciones:", key=f"obs_{row['ID']}", placeholder="Detalles o desviaciones...")

                    with f_col3:
                        firma_enc = st.text_input("✍️ Firma / Confirmación Encargado:", value=row['Supervisor'], key=f"f_enc_{row['ID']}")

                    if st.button("💾 Guardar Auditoría en Hoja de Procesos", key=f"btn_fin_{row['ID']}", use_container_width=True):
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
                            "Departamento": row["Departamento"],
                            "Propela": row["Propela"],
                            "Orden_Fabricacion_Lote": row["Orden_Fabricacion_Lote"],
                            "Codigo_PS": row["Codigo_PS"],
                            "Area": row["Area"],
                            "Cantidad_Kg": row["Cantidad_Kg"],
                            "Operador": row["Operador"],
                            "Supervisor": row["Supervisor"],
                            "Auditor": row["Auditor"],
                            "Limpieza_Dispensing": row["Limpieza_Dispensing"],
                            "Checklist_Tara": row["Checklist_Tara"],
                            "Checklist_Limpieza": row["Checklist_Limpieza"],
                            "Limpieza_Propela": row["Limpieza_Propela"],
                            "RPM": row["RPM"],
                            "Temperatura_C": row["Temperatura_C"],
                            "Viscosidad": row["Viscosidad"],
                            "Tiempo_Std_Min": row["Tiempo_Target_Min"],
                            "Rango_Permitido": row["Rango_Str"],
                            "Tiempo_Real_Min": tiempo_final,
                            "Tiempo_Prom_Dispersion": tiempo_disp,
                            "Dificultades_Materiales": row["Dificultades_Materiales_JSON"],
                            "Estatus": estatus,
                            "Paro_Emergencia": "SÍ" if paro_emergencia else "NO",
                            "Observaciones": obs if obs else "Sin observaciones",
                            "Firma_Operador": firma_op,
                            "Firma_Encargado": firma_enc
                        }

                        guardar_en_historial(registro_hist)

                        # Remover de activas
                        df_activas = df_activas[df_activas["ID"] != row["ID"]]
                        guardar_activas(df_activas)

                        st.success(f"✅ Auditoría de {row['Propela']} guardada exitosamente.")
                        st.rerun()

            st.markdown("---")

# ---------------------------------------------------------
# OP2: NUEVA AUDITORÍA (FORMATO EN PAPEL RECREADO)
# ---------------------------------------------------------
elif menu == "📋 Nueva Auditoría (Formato Oficial)":
    st.title("📄 Formato Digital: Tiempos de Agitado de Propela")
    st.caption("Auditoría de Procesos - Captura de parámetros")

    df_activas = cargar_activas()

    with st.form("form_auditoria_completa"):
        st.subheader("📌 1. Encabezado e Identificación General")
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        
        with col_e1:
            depto = st.selectbox("Departamento:", ["T1", "T2"])
            operador = st.text_input("Operador:", placeholder="Nombre del operador")
            
        with col_e2:
            fecha_aud = st.date_input("Fecha:", datetime.now())
            supervisor = st.text_input("Supervisor / Encargado:", placeholder="Nombre del supervisor")

        with col_e3:
            codigo_ps = st.text_input("Código PS:", placeholder="Ej. PS-8821")
            auditor = st.text_input("Auditor:", placeholder="Nombre del auditor")

        with col_e4:
            lote = st.text_input("Lote / OF:", placeholder="Ej. 1582548")
            area = st.selectbox("Área:", ["Manual Dispensing", "Automático"])

        st.markdown("---")
        st.subheader("🧼 2. Inspección y Check List Preliminar")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        with col_c1:
            limpieza_dispensing = st.selectbox("Limpieza de Dispensing:", ["Buena", "Regular", "Mala"])
        with col_c2:
            chk_tara = st.selectbox("Check List Tara:", ["SÍ", "NO", "N/A"])
        with col_c3:
            chk_limpieza = st.selectbox("Check List de Limpieza:", ["SÍ", "NO", "N/A"])
        with col_c4:
            cantidad_kg = st.number_input("Cantidad Total (Kg):", min_value=0.0, value=250.0, step=10.0)

        st.markdown("---")
        st.subheader("📦 3. Dificultades en Materiales (Adiciones)")
        st.caption("Edita o añade las filas correspondientes a los códigos agregados:")
        
        # Tabla dinámica para adición de materiales
        df_mat_default = pd.DataFrame([
            {"CODIGO": "", "KG EN OF": 0.0, "KG AGREGADOS": 0.0, "OBSERVACIONES": ""}
            for _ in range(3)
        ])
        
        tabla_materiales = st.data_editor(
            df_mat_default, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_mat"
        )

        st.markdown("---")
        st.subheader("🌀 4. Parámetros de Mezclado y Agitación")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            propela = st.selectbox("Propela / Agitador Asignado:", LISTA_PROPELAS)
            limpieza_propela = st.selectbox("Limpieza de la Propela:", ["Buena", "Regular", "Mala"])

        with col_m2:
            rpm = st.number_input("Velocidad Agitación (RPM):", min_value=0, max_value=5000, value=1200, step=50)
            temp_c = st.number_input("Temperatura (°C):", min_value=0.0, max_value=120.0, value=25.0, step=0.5)

        with col_m3:
            viscosidad = st.text_input("Viscosidad:", value="35 seg Zahn #4")
            tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(cantidad_kg)
            st.info(f"📋 **Tiempo Estándar:** `{rango_str}` (Target: {tiempo_target} min)")

        # Validar si propela está ocupada
        propelas_ocupadas = df_activas["Propela"].tolist() if not df_activas.empty else []
        if propela in propelas_ocupadas:
            st.warning(f"⚠️ **Atención:** La `{propela}` ya está en uso en el Monitor.")

        btn_iniciar = st.form_submit_button("🚀 Arrancar Agitación y Registrar en Monitor", use_container_width=True)

    if btn_iniciar:
        if not lote or not operador or not auditor:
            st.error("❌ Por favor completa los campos obligatorios: Lote, Operador y Auditor.")
        elif propela in propelas_ocupadas:
            st.error(f"❌ La {propela} ya está ocupada. Finaliza la sesión actual antes de iniciar otra.")
        else:
            # Serializar la tabla de materiales a texto/JSON para almacenarla
            mat_dict = tabla_materiales.dropna(how="all").to_dict(orient="records")
            mat_json_str = json.dumps(mat_dict)

            nuevo_id = int(datetime.now().timestamp())
            nueva_fila = {
                "ID": nuevo_id,
                "Departamento": depto,
                "Propela": propela,
                "Orden_Fabricacion_Lote": lote,
                "Codigo_PS": codigo_ps,
                "Area": area,
                "Cantidad_Kg": cantidad_kg,
                "Operador": operador,
                "Supervisor": supervisor,
                "Auditor": auditor,
                "Limpieza_Dispensing": limpieza_dispensing,
                "Checklist_Tara": chk_tara,
                "Checklist_Limpieza": chk_limpieza,
                "Limpieza_Propela": limpieza_propela,
                "RPM": rpm,
                "Temperatura_C": temp_c,
                "Viscosidad": viscosidad,
                "Dificultades_Materiales_JSON": mat_json_str,
                "Tiempo_Target_Min": tiempo_target,
                "Min_Permitido": min_p,
                "Max_Permitido": max_p,
                "Rango_Str": rango_str,
                "Hora_Inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            df_actualizado = pd.concat([df_activas, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_activas(df_actualizado)

            st.success(f"✅ Agitación iniciada para **{propela}** (Lote: {lote}). Se ha enviado al Monitor en Vivo.")
            st.balloons()

# ---------------------------------------------------------
# OP3: HOJA DE PROCESOS (HISTORIAL DIGITAL)
# ---------------------------------------------------------
elif menu == "📊 Hoja de Procesos (Historial Digital)":
    st.title("📊 Hoja de Procesos Digital")
    st.caption("Registro histórico oficial de auditorías realizadas")

    df_historial = cargar_historial()

    if df_historial.empty:
        st.info("No hay auditorías registradas en el historial.")
    else:
        # Resumen general
        total = len(df_historial)
        cumplidos = len(df_historial[df_historial["Estatus"] == "CUMPLE"])
        desviaciones = len(df_historial[df_historial["Estatus"] == "DESVIACIÓN"])
        paros = len(df_historial[df_historial["Estatus"] == "PARO DE EMERGENCIA"])
        pct = (cumplidos / total) * 100 if total > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Auditorías", total)
        c2.metric("Conformes", cumplidos)
        c3.metric("Desviaciones", desviaciones, delta_color="inverse")
        c4.metric("Paros Emergencia", paros, delta_color="inverse")
        c5.metric("% Cumplimiento", f"{pct:.1f}%")

        st.markdown("---")

        # Filtros de consulta
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            deptos_sel = st.multiselect("Filtrar por Departamento:", ["T1", "T2"], default=["T1", "T2"])
        with f_col2:
            estatus_sel = st.multiselect("Filtrar por Estatus:", list(df_historial["Estatus"].unique()), default=list(df_historial["Estatus"].unique()))

        df_filtrado = df_historial[
            (df_historial["Departamento"].isin(deptos_sel)) &
            (df_historial["Estatus"].isin(estatus_sel))
        ]

        st.dataframe(df_filtrado, use_container_width=True)

        # Descargar reporte
        csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Hoja de Procesos en CSV / Excel",
            data=csv_bytes,
            file_name=f"hoja_de_procesos_propelas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
