import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Auditoría de Procesos - Agitado de Propela",
    page_icon="⚙️",
    layout="wide"
)

ACTIVAS_FILE = "auditorias_activas.csv"
HISTORIAL_FILE = "hoja_de_procesos_agitacion.csv"

LISTA_PROPELAS = [
    "Propela 01 - Agitador Neumático 100L",
    "Propela 02 - Disco Cowles Alta Velocidad",
    "Propela 03 - Agitador Servomotor Principal",
    "Propela 04 - Propela Marina Heavy Duty",
    "Propela 05 - Tanque Pigmentos Central",
    "Propela 06 - Mezclador Auxiliar Línea Solventes"
]

ESTADOS_PROCESO = [
    "🔴 En Agitación",
    "🟡 Pausado - Falta de Material",
    "⚪ En Espera - Sin Mezclar",
    "🔵 En Muestra / Laboratorio"
]

# ---------------------------------------------------------
# REGLAS DE TIEMPO POR TARA TOTAL
# ---------------------------------------------------------
def calcular_regla_tiempo(tara_total_kg):
    if tara_total_kg <= 200:
        tiempo_target = 10.0
        rango_str = "10 min"
        min_p, max_p = 10.0, 10.0
    elif 200 < tara_total_kg <= 500:
        tiempo_target = 17.5
        rango_str = "15 a 20 min"
        min_p, max_p = 15.0, 20.0
    else:
        tiempo_target = 27.5
        rango_str = "25 a 30 min"
        min_p, max_p = 25.0, 30.0
        
    return tiempo_target, rango_str, min_p, max_p

# ---------------------------------------------------------
# MANEJO DE BASE DE DATOS
# ---------------------------------------------------------
def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        df = pd.read_csv(ACTIVAS_FILE)
        return df
    return pd.DataFrame(columns=[
        "ID", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS", 
        "Area", "Tara_Total_Kg", "Tara_OF_Kg", "Operador", "Supervisor", "Auditor",
        "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza",
        "Limpieza_Propela", "Estatus_Proceso", "Dificultades_Materiales_JSON", 
        "Tiempo_Target_Min", "Min_Permitido", "Max_Permitido", "Rango_Str", "Hora_Inicio"
    ])

def guardar_activas(df):
    df.to_csv(ACTIVAS_FILE, index=False)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return pd.DataFrame(columns=[
        "Fecha_Hora_Fin", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS",
        "Area", "Tara_Total_Kg", "Tara_OF_Kg", "Operador", "Supervisor", "Auditor",
        "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza",
        "Limpieza_Propela", "Estatus_Proceso_Final", "Tiempo_Std_Min", "Rango_Permitido", 
        "Tiempo_Real_Min", "Tiempo_Prom_Dispersion", "Dificultades_Materiales", 
        "Estatus_Auditoria", "Paro_Emergencia", "Observaciones", 
        "Firma_Operador", "Firma_Encargado"
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
st.sidebar.caption("Control Operativo de Propelas")

menu = st.sidebar.radio(
    "Navegación:", 
    [
        "🔴 Monitor de O.F. Activas (Bloques)", 
        "📋 Registrar Nueva O.F. / Auditoría", 
        "📊 Hoja de Procesos (Historial)"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refrescar Monitor", use_container_width=True):
    st.rerun()

# ---------------------------------------------------------
# 1. MONITOR EN VIVO (BLOQUES DESPLEGABLES POR CADA O.F.)
# ---------------------------------------------------------
if menu == "🔴 Monitor de O.F. Activas (Bloques)":
    st.title("🖥️ Monitor de Órdenes de Fabricación Activas")
    st.caption("Panel dinámico: abre el bloque de cualquier O.F. para revisar o finalizar su auditoría")
    
    df_activas = cargar_activas()
    
    if df_activas.empty:
        st.success("✅ No hay O.F. activas en este momento. Todos los procesos están concluidos.")
    else:
        st.subheader(f"📦 Órdenes en Seguimiento: {len(df_activas)}")
        ahora = datetime.now()
        
        for idx, row in df_activas.iterrows():
            hora_inicio = datetime.strptime(row["Hora_Inicio"], "%Y-%m-%d %H:%M:%S")
            minutos_transcurridos = (ahora - hora_inicio).total_seconds() / 60.0
            
            # Formato de cabecera para el bloque desplegable
            titulo_bloque = (
                f"📦 O.F. / Lote: {row['Orden_Fabricacion_Lote']} | "
                f"Propela: {row['Propela']} | "
                f"Depto: {row['Departamento']} | "
                f"Estado: {row['Estatus_Proceso']}"
            )
            
            with st.expander(titulo_bloque, expanded=False):
                col_top1, col_top2, col_top3 = st.columns([3, 2, 2.5])
                
                with col_top1:
                    st.markdown(f"#### 🌀 {row['Propela']}")
                    st.write(f"**O.F. / Lote:** `{row['Orden_Fabricacion_Lote']}` | **Código PS:** `{row['Codigo_PS']}`")
                    st.write(f"**Tara Total:** `{row['Tara_Total_Kg']} kg` | **Tara O.F.:** `{row['Tara_OF_Kg']} kg`")
                    st.write(f"**Operador:** `{row['Operador']}` | **Supervisor:** `{row['Supervisor']}` | **Auditor:** `{row['Auditor']}`")
                    st.caption(f"Área: {row['Area']} | Depto: {row['Departamento']} | Inicio: {hora_inicio.strftime('%H:%M:%S')}")
                
                with col_top2:
                    st.metric("Tiempo Transcurrido", f"{minutos_transcurridos:.1f} min", delta=f"Objetivo: {row['Rango_Str']}")
                    
                    # Permite cambiar el estado de la O.F. sin cerrarla
                    nuevo_estado = st.selectbox(
                        "Cambiar Estado del Proceso:",
                        ESTADOS_PROCESO,
                        index=ESTADOS_PROCESO.index(row['Estatus_Proceso']) if row['Estatus_Proceso'] in ESTADOS_PROCESO else 0,
                        key=f"estado_{row['ID']}"
                    )
                    if nuevo_estado != row['Estatus_Proceso']:
                        df_activas.loc[df_activas["ID"] == row["ID"], "Estatus_Proceso"] = nuevo_estado
                        guardar_activas(df_activas)
                        st.rerun()

                with col_top3:
                    if minutos_transcurridos >= row["Min_Permitido"] and row['Estatus_Proceso'] == "🔴 En Agitación":
                        st.markdown(
                            f"""
                            <div style="background-color: #D32F2F; padding: 12px; border-radius: 8px; text-align: center; color: white; font-weight: bold;">
                                🚨 ¡ALERTA DE TIEMPO! <br>
                                <span style="font-size: 18px;">¡APAGAR PROPELA!</span><br>
                                Cumplido ({minutos_transcurridos:.1f} min)
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        st.info(f"📌 **Estado Actual:** {row['Estatus_Proceso']}")

                st.markdown("---")
                
                # Desglose de Inspección y Checklist
                col_det1, col_det2, col_det3 = st.columns(3)
                with col_det1:
                    st.write(f"🧼 **Limpieza Dispensing:** {row['Limpieza_Dispensing']}")
                    st.write(f"🌀 **Limpieza Propela:** {row['Limpieza_Propela']}")
                with col_det2:
                    st.write(f"📋 **Checklist Tara:** {row['Checklist_Tara']}")
                    st.write(f"📋 **Checklist Limpieza:** {row['Checklist_Limpieza']}")
                with col_det3:
                    # Mostrar tabla de materiales si existe
                    try:
                        mat_list = json.loads(row['Dificultades_Materiales_JSON'])
                        if mat_list:
                            st.caption("📦 Materiales / Adiciones:")
                            st.dataframe(pd.DataFrame(mat_list), height=120)
                    except:
                        st.caption("Sin datos de materiales")

                st.markdown("---")
                st.subheader("🏁 Finalizar y Cerrar Auditoría de esta O.F.")
                
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    tiempo_disp = st.number_input(
                        "⏱️ Tiempo Promedio de Dispersión (min):", 
                        min_value=0.0, value=minutos_transcurridos, step=0.5, key=f"disp_{row['ID']}"
                    )
                    paro_emergencia = st.checkbox("⚠️ Paro de Emergencia / Desviación Grave", key=f"paro_{row['ID']}")

                with col_c2:
                    firma_op = st.text_input("✍️ Firma / Confirmación Operador:", value=row['Operador'], key=f"f_op_{row['ID']}")
                    obs = st.text_area("Observaciones Finales:", key=f"obs_{row['ID']}", placeholder="Muestras, adiciones pend, etc...")

                with col_c3:
                    firma_enc = st.text_input("✍️ Firma / Confirmación Encargado:", value=row['Supervisor'], key=f"f_enc_{row['ID']}")

                if st.button("💾 Guardar y Enviar a Hoja de Procesos", key=f"btn_fin_{row['ID']}", use_container_width=True):
                    tiempo_final = round(minutos_transcurridos, 1)
                    cumple = (row["Min_Permitido"] <= tiempo_final <= row["Max_Permitido"]) and not paro_emergencia
                    
                    if paro_emergencia:
                        estatus_audit = "PARO DE EMERGENCIA"
                    elif cumple:
                        estatus_audit = "CUMPLE"
                    else:
                        estatus_audit = "DESVIACIÓN"

                    registro_hist = {
                        "Fecha_Hora_Fin": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Departamento": row["Departamento"],
                        "Propela": row["Propela"],
                        "Orden_Fabricacion_Lote": row["Orden_Fabricacion_Lote"],
                        "Codigo_PS": row["Codigo_PS"],
                        "Area": row["Area"],
                        "Tara_Total_Kg": row["Tara_Total_Kg"],
                        "Tara_OF_Kg": row["Tara_OF_Kg"],
                        "Operador": row["Operador"],
                        "Supervisor": row["Supervisor"],
                        "Auditor": row["Auditor"],
                        "Limpieza_Dispensing": row["Limpieza_Dispensing"],
                        "Checklist_Tara": row["Checklist_Tara"],
                        "Checklist_Limpieza": row["Checklist_Limpieza"],
                        "Limpieza_Propela": row["Limpieza_Propela"],
                        "Estatus_Proceso_Final": row["Estatus_Proceso"],
                        "Tiempo_Std_Min": row["Tiempo_Target_Min"],
                        "Rango_Permitido": row["Rango_Str"],
                        "Tiempo_Real_Min": tiempo_final,
                        "Tiempo_Prom_Dispersion": tiempo_disp,
                        "Dificultades_Materiales": row["Dificultades_Materiales_JSON"],
                        "Estatus_Auditoria": estatus_audit,
                        "Paro_Emergencia": "SÍ" if paro_emergencia else "NO",
                        "Observaciones": obs if obs else "Sin observaciones",
                        "Firma_Operador": firma_op,
                        "Firma_Encargado": firma_enc
                    }

                    guardar_en_historial(registro_hist)

                    # Eliminar de la lista de activas
                    df_activas = df_activas[df_activas["ID"] != row["ID"]]
                    guardar_activas(df_activas)

                    st.success(f"✅ O.F. {row['Orden_Fabricacion_Lote']} finalizada y guardada en el historial.")
                    st.rerun()

# ---------------------------------------------------------
# 2. CAPTURA Y REGISTRO DE NUEVA O.F.
# ---------------------------------------------------------
elif menu == "📋 Registrar Nueva O.F. / Auditoría":
    st.title("📄 Registrar Nueva Auditoría de Agitado de Propela")
    st.caption("Añade una O.F. al monitor para llevar su seguimiento en vivo")

    df_activas = cargar_activas()

    with st.form("form_nueva_of"):
        st.subheader("📌 1. Encabezado e Identificación General")
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        
        with col_e1:
            depto = st.selectbox("Departamento:", ["T1", "T2"])
            operador = st.text_input("Operador:", placeholder="Ej. Juan Pérez")
            
        with col_e2:
            fecha_aud = st.date_input("Fecha:", datetime.now())
            supervisor = st.text_input("Supervisor / Encargado:", placeholder="Ej. Carlos Ruiz")

        with col_e3:
            codigo_ps = st.text_input("Código PS:", placeholder="Ej. PS-8821")
            auditor = st.text_input("Auditor:", placeholder="Ej. M. López")

        with col_e4:
            lote = st.text_input("Lote / O.F.:", placeholder="Ej. 1582548")
            area = st.selectbox("Área:", ["Manual Dispensing", "Automático"])

        st.markdown("---")
        st.subheader("⚖️ 2. Taras e Inspección Preliminar")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        with col_c1:
            tara_total = st.number_input("Tara Total (kg):", min_value=0.0, value=250.0, step=10.0)
            tara_of = st.number_input("Tara de O.F. (kg):", min_value=0.0, value=15.0, step=0.5)
            
        with col_c2:
            limpieza_dispensing = st.selectbox("Limpieza de Dispensing:", ["Buena", "Regular", "Mala"])
            limpieza_propela = st.selectbox("Limpieza de la Propela:", ["Buena", "Regular", "Mala"])

        with col_c3:
            chk_tara = st.selectbox("Check List Tara:", ["SÍ", "NO", "N/A"])
            chk_limpieza = st.selectbox("Check List Limpieza:", ["SÍ", "NO", "N/A"])

        with col_c4:
            propela = st.selectbox("Propela / Agitador Asignado:", LISTA_PROPELAS)
            estatus_inicial = st.selectbox("Estado Inicial del Proceso:", ESTADOS_PROCESO)

        tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(tara_total)
        st.info(f"📋 **Tiempo Estándar según Tara Total ({tara_total} kg):** Rango `{rango_str}` (Objetivo: `{tiempo_target} min`)")

        st.markdown("---")
        st.subheader("📦 3. Dificultades en Materiales (Adiciones)")
        st.caption("Registra adiciones o variaciones de códigos en la O.F.:")
        
        df_mat_default = pd.DataFrame([
            {"CODIGO": "", "KG EN OF": 0.0, "KG AGREGADOS": 0.0, "OBSERVACIONES": ""}
            for _ in range(3)
        ])
        
        tabla_materiales = st.data_editor(
            df_mat_default, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_mat_nueva"
        )

        btn_iniciar = st.form_submit_button("🚀 Agregar O.F. al Monitor de Activas", use_container_width=True)

    if btn_iniciar:
        if not lote or not operador or not auditor:
            st.error("❌ Los campos O.F./Lote, Operador y Auditor son obligatorios.")
        else:
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
                "Tara_Total_Kg": tara_total,
                "Tara_OF_Kg": tara_of,
                "Operador": operador,
                "Supervisor": supervisor,
                "Auditor": auditor,
                "Limpieza_Dispensing": limpieza_dispensing,
                "Checklist_Tara": chk_tara,
                "Checklist_Limpieza": chk_limpieza,
                "Limpieza_Propela": limpieza_propela,
                "Estatus_Proceso": estatus_inicial,
                "Dificultades_Materiales_JSON": mat_json_str,
                "Tiempo_Target_Min": tiempo_target,
                "Min_Permitido": min_p,
                "Max_Permitido": max_p,
                "Rango_Str": rango_str,
                "Hora_Inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            df_actualizado = pd.concat([df_activas, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_activas(df_actualizado)

            st.success(f"✅ O.F. **{lote}** agregada correctamente. Ya puedes ver su bloque en el Monitor.")
            st.balloons()

# ---------------------------------------------------------
# 3. HOJA DE PROCESOS (HISTORIAL DIGITAL)
# ---------------------------------------------------------
elif menu == "📊 Hoja de Procesos (Historial)":
    st.title("📊 Hoja de Procesos Digital")
    st.caption("Registro histórico de auditorías completadas")

    df_historial = cargar_historial()

    if df_historial.empty:
        st.info("No hay auditorías registradas en el historial.")
    else:
        total = len(df_historial)
        cumplidos = len(df_historial[df_historial["Estatus_Auditoria"] == "CUMPLE"])
        desviaciones = len(df_historial[df_historial["Estatus_Auditoria"] == "DESVIACIÓN"])
        paros = len(df_historial[df_historial["Estatus_Auditoria"] == "PARO DE EMERGENCIA"])
        pct = (cumplidos / total) * 100 if total > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Registros", total)
        c2.metric("Conformes", cumplidos)
        c3.metric("Desviaciones", desviaciones, delta_color="inverse")
        c4.metric("Paros Emergencia", paros, delta_color="inverse")
        c5.metric("% Cumplimiento", f"{pct:.1f}%")

        st.markdown("---")

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            deptos_sel = st.multiselect("Filtrar por Departamento:", ["T1", "T2"], default=["T1", "T2"])
        with f_col2:
            estatus_sel = st.multiselect("Filtrar por Estatus Auditoría:", list(df_historial["Estatus_Auditoria"].unique()), default=list(df_historial["Estatus_Auditoria"].unique()))

        df_filtrado = df_historial[
            (df_historial["Departamento"].isin(deptos_sel)) &
            (df_historial["Estatus_Auditoria"].isin(estatus_sel))
        ]

        st.dataframe(df_filtrado, use_container_width=True)

        csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Hoja de Procesos en CSV / Excel",
            data=csv_bytes,
            file_name=f"hoja_de_procesos_propelas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
