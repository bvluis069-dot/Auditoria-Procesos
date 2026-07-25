import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL Y GOOGLE SHEETS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Procesos - Pesado y Agitación",
    page_icon="⚙️",
    layout="wide"
)

ACTIVAS_FILE = "auditorias_activas.csv"
HISTORIAL_FILE = "hoja_de_procesos_agitacion.csv"

# Conexión a Google Sheets
GOOGLE_CREDENTIALS = "mes-molienda-sanchez-7a9a01e5553d.json"
GOOGLE_SHEET_NAME = "Control_Molienda_MES"
WORKSHEET_PROPELAS = "Historial_Propelas"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

LISTA_PROPELAS = [
    "Cowles 01 - Agitador Neumático 100L",
    "Cowles 02 - Disco Alta Velocidad",
    "Cowles 03 - Agitador Servomotor Principal",
    "Cowles 04 - Propela Marina Heavy Duty",
    "Cowles 05 - Tanque Pigmentos Central",
    "Cowles 06 - Mezclador Auxiliar Línea Solventes"
]

ESTADOS_PESADO = [
    "⚪ En Espera (Pesado)",
    "🟡 Pausado - Falta de Material",
    "🟢 Pesado Concluido - Listo para Mezclar"
]

# ---------------------------------------------------------
# FUNCIÓN DE CONEXIÓN A GOOGLE SHEETS
# ---------------------------------------------------------
@st.cache_resource
def conectar_google_sheets():
    try:
        credenciales = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS,
            scopes=SCOPES
        )
        cliente = gspread.authorize(credenciales)
        libro = cliente.open(GOOGLE_SHEET_NAME)
        return libro
    except Exception as e:
        return None

def guardar_en_google_sheets(datos):
    """Envía la fila finalizada a la hoja Historial_Propelas"""
    try:
        libro = conectar_google_sheets()
        if not libro:
            return False
        
        hoja = libro.worksheet(WORKSHEET_PROPELAS)
        
        fila = [
            datos.get("ID Orden", ""),
            datos.get("Fecha Fin", ""),
            datos.get("Departamento", ""),
            datos.get("Lote / OF", ""),
            datos.get("Código PS", ""),
            datos.get("Área", ""),
            datos.get("Propela / Cowles", ""),
            datos.get("Tara Total (kg)", ""),
            datos.get("Tara OF (kg)", ""),
            datos.get("Estatus Pesado", ""),
            datos.get("Operador", ""),
            datos.get("Supervisor", ""),
            datos.get("Auditor", ""),
            datos.get("Limpieza Dispensing", ""),
            datos.get("Checklist Tara", ""),
            datos.get("Checklist Limpieza", ""),
            datos.get("Limpieza Propela", ""),
            datos.get("Tiempo Std (min)", ""),
            datos.get("Rango Permitido", ""),
            datos.get("Tiempo Real Agitación (min)", ""),
            datos.get("Tiempo Prom Dispersión (min)", ""),
            datos.get("Adiciones / Materiales", ""),
            datos.get("Estatus Auditoría", ""),
            datos.get("Paro Emergencia", ""),
            datos.get("Observaciones", ""),
            datos.get("Firma Operador", ""),
            datos.get("Firma Encargado", "")
        ]
        
        hoja.append_row(fila)
        return True
    except Exception as e:
        st.warning(f"⚠️ Nota: Se guardó localmente, pero falló el envío a Google Sheets: {e}")
        return False

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
# MANEJO DE BASE DE DATOS LOCAL
# ---------------------------------------------------------
def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        df = pd.read_csv(ACTIVAS_FILE)
        
        # Corregir tipos de datos de texto para evitar TypeError al actualizar
        columnas_texto = [
            "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS", 
            "Area", "Operador", "Supervisor", "Auditor", "Limpieza_Dispensing", 
            "Checklist_Tara", "Checklist_Limpieza", "Limpieza_Propela", 
            "Estatus_Pesado", "Dificultades_Materiales_JSON", "Rango_Str", 
            "Hora_Inicio_Mezclado"
        ]
        for col in columnas_texto:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(object)
                
        if "En_Mezclado" in df.columns:
            df["En_Mezclado"] = df["En_Mezclado"].astype(bool)
            
        return df
        
    return pd.DataFrame(columns=[
        "ID", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS", 
        "Area", "Tara_Total_Kg", "Tara_OF_Kg", "Operador", "Supervisor", "Auditor",
        "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza",
        "Limpieza_Propela", "Estatus_Pesado", "En_Mezclado", "Dificultades_Materiales_JSON", 
        "Tiempo_Target_Min", "Min_Permitido", "Max_Permitido", "Rango_Str", "Hora_Inicio_Mezclado"
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
        "Limpieza_Propela", "Estatus_Pesado", "Tiempo_Std_Min", "Rango_Permitido", 
        "Tiempo_Real_Min", "Tiempo_Prom_Dispersion", "Dificultades_Materiales", 
        "Estatus_Auditoria", "Paro_Emergencia", "Observaciones", 
        "Firma_Operador", "Firma_Encargado"
    ])

def guardar_en_historial_local(registro):
    df_actual = cargar_historial()
    nuevo_df = pd.DataFrame([registro])
    df_actualizado = pd.concat([df_actual, nuevo_df], ignore_index=True)
    df_actualizado.to_csv(HISTORIAL_FILE, index=False)

# ---------------------------------------------------------
# NAVEGACIÓN Y MENÚ LATERAL
# ---------------------------------------------------------
st.sidebar.title("⚙️ Control Molienda MES")
st.sidebar.caption("Módulo de Pesado y Agitación en Cowles")

menu = st.sidebar.radio(
    "Selecciona Área / Navegación:", 
    [
        "🌀 Monitor de Mezclado en Cowles (En Vivo)", 
        "📦 Área de Pesado y Espera de O.F.", 
        "📋 Registrar Nueva O.F. (Pesado)", 
        "📊 Hoja de Procesos (Historial)"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refrescar Pantalla", use_container_width=True):
    st.rerun()

# ---------------------------------------------------------
# 1. MONITOR DE MEZCLADO EN COWLES (SOLO MEZCLADO ACTIVO)
# ---------------------------------------------------------
if menu == "🌀 Monitor de Mezclado en Cowles (En Vivo)":
    st.title("🌀 Monitor de Mezclado en Cowles")
    st.caption("Seguimiento exclusivo de O.F. que se están agitando en tanque en este momento")
    
    df_activas = cargar_activas()
    df_mezclando = df_activas[df_activas["En_Mezclado"] == True] if not df_activas.empty else pd.DataFrame()
    
    if df_mezclando.empty:
        st.info("ℹ️ No hay mezclas activas en Cowles en este momento. Las O.F. en preparado o espera están en la pestaña 'Área de Pesado y Espera'.")
    else:
        st.subheader(f"⚡ Agitaciones Activas: {len(df_mezclando)}")
        ahora = datetime.now()
        
        for idx, row in df_mezclando.iterrows():
            hora_inicio = datetime.strptime(str(row["Hora_Inicio_Mezclado"]), "%Y-%m-%d %H:%M:%S")
            minutos_transcurridos = (ahora - hora_inicio).total_seconds() / 60.0
            
            titulo_bloque = (
                f"🌀 {row['Propela']} | "
                f"O.F.: {row['Orden_Fabricacion_Lote']} | "
                f"Depto: {row['Departamento']} | "
                f"Tiempo: {minutos_transcurridos:.1f} min"
            )
            
            with st.expander(titulo_bloque, expanded=True):
                c1, c2, c3 = st.columns([3, 2, 2.5])
                
                with c1:
                    st.markdown(f"### {row['Propela']}")
                    st.write(f"**O.F. / Lote:** `{row['Orden_Fabricacion_Lote']}` | **Código PS:** `{row['Codigo_PS']}`")
                    st.write(f"**Tara Total:** `{row['Tara_Total_Kg']} kg` | **Tara O.F.:** `{row['Tara_OF_Kg']} kg`")
                    st.write(f"**Op:** `{row['Operador']}` | **Sup:** `{row['Supervisor']}` | **Auditor:** `{row['Auditor']}`")
                    st.caption(f"Inicio Mezclado: {hora_inicio.strftime('%H:%M:%S')} | Limpieza Propela: {row['Limpieza_Propela']}")
                
                with c2:
                    st.metric("Tiempo Mezclando", f"{minutos_transcurridos:.1f} min", delta=f"Rango Std: {row['Rango_Str']}")
                
                with c3:
                    if minutos_transcurridos >= row["Min_Permitido"]:
                        st.markdown(
                            f"""
                            <div style="background-color: #B71C1C; padding: 12px; border-radius: 8px; text-align: center; color: white; font-weight: bold;">
                                🚨 ¡TIEMPO CUMPLIDO! <br>
                                <span style="font-size: 18px;">¡APAGAR COWLES!</span><br>
                                ({minutos_transcurridos:.1f} min transcurridos)
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        falta = row["Min_Permitido"] - minutos_transcurridos
                        st.info(f"⏳ Agitando... Faltan approx. **{falta:.1f} min** para el tiempo mínimo.")

                st.markdown("---")
                st.subheader("🏁 Finalizar y Registrar Salida de Agitación")
                
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    tiempo_disp = st.number_input("⏱️ Tiempo Prom. Dispersión (min):", min_value=0.0, value=minutos_transcurridos, step=0.5, key=f"disp_{row['ID']}")
                    paro_emergencia = st.checkbox("⚠️ Paro de Emergencia / Falla", key=f"paro_{row['ID']}")

                with col_c2:
                    firma_op = st.text_input("✍️ Firma Operador:", value=row['Operador'], key=f"f_op_{row['ID']}")
                    obs = st.text_area("Observaciones:", key=f"obs_{row['ID']}", placeholder="Muestras OK, adición de solvente...")

                with col_c3:
                    firma_enc = st.text_input("✍️ Firma Encargado:", value=row['Supervisor'], key=f"f_enc_{row['ID']}")

                if st.button("💾 Finalizar Agitación y Exportar a Google Sheets", key=f"btn_fin_{row['ID']}", use_container_width=True):
                    tiempo_final = round(minutos_transcurridos, 1)
                    cumple = (row["Min_Permitido"] <= tiempo_final <= row["Max_Permitido"]) and not paro_emergencia
                    
                    estatus_audit = "PARO DE EMERGENCIA" if paro_emergencia else ("CUMPLE" if cumple else "DESVIACIÓN")

                    datos_gsheets = {
                        "ID Orden": row["ID"],
                        "Fecha Fin": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Departamento": row["Departamento"],
                        "Lote / OF": row["Orden_Fabricacion_Lote"],
                        "Código PS": row["Codigo_PS"],
                        "Área": row["Area"],
                        "Propela / Cowles": row["Propela"],
                        "Tara Total (kg)": row["Tara_Total_Kg"],
                        "Tara OF (kg)": row["Tara_OF_Kg"],
                        "Estatus Pesado": row["Estatus_Pesado"],
                        "Operador": row["Operador"],
                        "Supervisor": row["Supervisor"],
                        "Auditor": row["Auditor"],
                        "Limpieza Dispensing": row["Limpieza_Dispensing"],
                        "Checklist Tara": row["Checklist_Tara"],
                        "Checklist Limpieza": row["Checklist_Limpieza"],
                        "Limpieza Propela": row["Limpieza_Propela"],
                        "Tiempo Std (min)": row["Tiempo_Target_Min"],
                        "Rango Permitido": row["Rango_Str"],
                        "Tiempo Real Agitación (min)": tiempo_final,
                        "Tiempo Prom Dispersión (min)": tiempo_disp,
                        "Adiciones / Materiales": row["Dificultades_Materiales_JSON"],
                        "Estatus Auditoría": estatus_audit,
                        "Paro Emergencia": "SÍ" if paro_emergencia else "NO",
                        "Observaciones": obs if obs else "Sin observaciones",
                        "Firma Operador": firma_op,
                        "Firma Encargado": firma_enc
                    }

                    guardar_en_historial_local(datos_gsheets)
                    exito_gsheets = guardar_en_google_sheets(datos_gsheets)

                    df_activas = df_activas[df_activas["ID"] != row["ID"]]
                    guardar_activas(df_activas)

                    if exito_gsheets:
                        st.success(f"✅ Agitación finalizada y registrada con éxito en Google Sheets (`{WORKSHEET_PROPELAS}`).")
                    else:
                        st.success(f"✅ Agitación finalizada y registrada en la base de datos local.")
                    st.rerun()

# ---------------------------------------------------------
# 2. ÁREA DE PESADO Y ESPERA DE O.F. (PREVIO A MEZCLAR)
# ---------------------------------------------------------
elif menu == "📦 Área de Pesado y Espera de O.F.":
    st.title("📦 Área de Pesado y Espera de Materiales")
    st.caption("Administra las O.F. en preparación antes de pasarlas a agitación en Cowles")

    df_activas = cargar_activas()
    df_espera = df_activas[df_activas["En_Mezclado"] == False] if not df_activas.empty else pd.DataFrame()

    if df_espera.empty:
        st.info("No hay O.F. pendientes en el área de pesado.")
    else:
        st.subheader(f"📋 Órdenes en Pesado / Espera: {len(df_espera)}")
        
        for idx, row in df_espera.iterrows():
            titulo = f"📦 O.F.: {row['Orden_Fabricacion_Lote']} | Estatus: {row['Estatus_Pesado']} | Depto: {row['Departamento']}"
            
            with st.expander(titulo, expanded=True):
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.write(f"**Código PS:** `{row['Codigo_PS']}` | **Área:** `{row['Area']}`")
                    st.write(f"**Tara Total:** `{row['Tara_Total_Kg']} kg` | **Tara O.F.:** `{row['Tara_OF_Kg']} kg`")
                    st.write(f"**Operador:** `{row['Operador']}` | **Supervisor:** `{row['Supervisor']}` | **Auditor:** `{row['Auditor']}`")
                    st.caption(f"Dispensing: {row['Limpieza_Dispensing']} | Chk Tara: {row['Checklist_Tara']} | Chk Limpieza: {row['Checklist_Limpieza']}")

                with col2:
                    nuevo_estatus = st.selectbox(
                        "Estatus en Pesado:",
                        ESTADOS_PESADO,
                        index=ESTADOS_PESADO.index(row['Estatus_Pesado']) if row['Estatus_Pesado'] in ESTADOS_PESADO else 0,
                        key=f"est_pes_{row['ID']}"
                    )
                    
                    propela_sel = st.selectbox(
                        "Asignar Cowles / Propela:",
                        LISTA_PROPELAS,
                        index=LISTA_PROPELAS.index(row['Propela']) if row['Propela'] in LISTA_PROPELAS else 0,
                        key=f"prop_{row['ID']}"
                    )

                    if (nuevo_estatus != row['Estatus_Pesado']) or (propela_sel != row['Propela']):
                        df_activas.loc[df_activas["ID"] == row["ID"], "Estatus_Pesado"] = nuevo_estatus
                        df_activas.loc[df_activas["ID"] == row["ID"], "Propela"] = propela_sel
                        guardar_activas(df_activas)
                        st.rerun()

                    # PASAR A MEZCLAR EN COWLES
                    st.markdown("---")
                    if st.button(f"🚀 Meter a Mezclar ({propela_sel})", key=f"btn_start_{row['ID']}", use_container_width=True):
                        # Asegurar tipo de objeto antes de asignar texto
                        df_activas["Hora_Inicio_Mezclado"] = df_activas["Hora_Inicio_Mezclado"].astype(object)
                        df_activas.loc[df_activas["ID"] == row["ID"], "En_Mezclado"] = True
                        df_activas.loc[df_activas["ID"] == row["ID"], "Hora_Inicio_Mezclado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        guardar_activas(df_activas)
                        st.success(f"🚀 O.F. {row['Orden_Fabricacion_Lote']} enviada al Monitor de Mezclado en Vivo.")
                        st.rerun()

# ---------------------------------------------------------
# 3. REGISTRAR NUEVA O.F. (CAPTURA EN PESADO)
# ---------------------------------------------------------
elif menu == "📋 Registrar Nueva O.F. (Pesado)":
    st.title("📄 Registrar Nueva O.F. en Pesado")
    st.caption("Captura inicial del lote antes de pasar a agitación")

    df_activas = cargar_activas()

    with st.form("form_registro_of"):
        st.subheader("📌 1. Identificación y Generales")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            depto = st.selectbox("Departamento:", ["T1", "T2"])
            operador = st.text_input("Operador:", placeholder="Nombre operador")
        with col2:
            fecha_aud = st.date_input("Fecha:", datetime.now())
            supervisor = st.text_input("Supervisor:", placeholder="Nombre supervisor")
        with col3:
            codigo_ps = st.text_input("Código PS:", placeholder="Ej. PS-8821")
            auditor = st.text_input("Auditor:", placeholder="Nombre auditor")
        with col4:
            lote = st.text_input("Lote / O.F.:", placeholder="Ej. 1582548")
            area = st.selectbox("Área:", ["Manual Dispensing", "Automático"])

        st.markdown("---")
        st.subheader("⚖️ 2. Pesos, Taras e Inspección")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            tara_total = st.number_input("Tara Total (kg):", min_value=0.0, value=250.0, step=10.0)
            tara_of = st.number_input("Tara O.F. (kg):", min_value=0.0, value=15.0, step=0.5)
        with c2:
            limpieza_dispensing = st.selectbox("Limpieza Dispensing:", ["Buena", "Regular", "Mala"])
            limpieza_propela = st.selectbox("Limpieza Propela:", ["Buena", "Regular", "Mala"])
        with c3:
            chk_tara = st.selectbox("Checklist Tara:", ["SÍ", "NO", "N/A"])
            chk_limpieza = st.selectbox("Checklist Limpieza:", ["SÍ", "NO", "N/A"])
        with c4:
            propela_inicial = st.selectbox("Cowles Propuesto:", LISTA_PROPELAS)
            estatus_pesado = st.selectbox("Estatus en Pesado:", ESTADOS_PESADO)

        tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(tara_total)
        st.info(f"📋 **Tiempo Estándar Calculado por Tara Total ({tara_total} kg):** `{rango_str}` (Objetivo: `{tiempo_target} min`)")

        st.markdown("---")
        st.subheader("📦 3. Materiales / Observaciones de Adición")
        
        df_mat_default = pd.DataFrame([
            {"CODIGO": "", "KG EN OF": 0.0, "KG AGREGADOS": 0.0, "OBSERVACIONES": ""}
            for _ in range(3)
        ])
        
        tabla_materiales = st.data_editor(
            df_mat_default, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_mat_pesado"
        )

        btn_iniciar = st.form_submit_button("💾 Guardar O.F. en Área de Pesado", use_container_width=True)

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
                "Propela": propela_inicial,
                "Orden_Fabricacion_Lote": str(lote),
                "Codigo_PS": str(codigo_ps),
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
                "Estatus_Pesado": estatus_pesado,
                "En_Mezclado": False,
                "Dificultades_Materiales_JSON": mat_json_str,
                "Tiempo_Target_Min": tiempo_target,
                "Min_Permitido": min_p,
                "Max_Permitido": max_p,
                "Rango_Str": rango_str,
                "Hora_Inicio_Mezclado": ""
            }

            df_actualizado = pd.concat([df_activas, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_activas(df_actualizado)

            st.success(f"✅ O.F. **{lote}** registrada exitosamente en el Área de Pesado.")
            st.balloons()

# ---------------------------------------------------------
# 4. HOJA DE PROCESOS (HISTORIAL DIGITAL)
# ---------------------------------------------------------
elif menu == "📊 Hoja de Procesos (Historial)":
    st.title("📊 Hoja de Procesos Digital")
    st.caption("Histórico local de auditorías completadas")

    df_historial = cargar_historial()

    if df_historial.empty:
        st.info("No hay auditorías registradas en el historial.")
    else:
        st.dataframe(df_historial, use_container_width=True)

        csv_bytes = df_historial.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Hoja de Procesos en CSV / Excel",
            data=csv_bytes,
            file_name=f"hoja_de_procesos_propelas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
