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

# Conexión a Google Sheets (Tu archivo JSON)
GOOGLE_CREDENTIALS = "mes-molienda-sanchez-7a9a01e5553d.json"
GOOGLE_SHEET_NAME = "Control_Molienda_MES"
WORKSHEET_PROPELAS = "Historial_Propelas"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

LISTA_PROPELAS = [f"PTPLSME{i:02d} - Tintas" for i in range(1, 12)] + [
    f"PTPLSME{i:02d} - Recubrimientos" for i in range(12, 16)
]

ESTADOS_PESADO = [
    "⚪ En Espera (Pesado)",
    "🟡 Pausado - Falta de Material",
    "🟢 Pesado Concluido - Listo para Mezclar"
]

OPCIONES_LIMPIEZA = ["Buena", "Regular", "Mala"]
OPCIONES_CHECKLIST = ["SÍ", "NO", "N/A"]

# ---------------------------------------------------------
# CONEXIÓN A GOOGLE SHEETS
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
            datos.get("Operador Pesado", ""),
            datos.get("Operador Mezclado", ""),
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

def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        df = pd.read_csv(ACTIVAS_FILE)
        columnas_texto = [
            "Tipo_Producto", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS", 
            "Area", "Operador", "Operador_Mezclado", "Supervisor", "Auditor", 
            "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza", "Limpieza_Propela", 
            "Estatus_Pesado", "Dificultades_Materiales_JSON", "Rango_Str", 
            "Hora_Inicio_Mezclado"
        ]
        for col in columnas_texto:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(object)
        if "En_Mezclado" in df.columns:
            df["En_Mezclado"] = df["En_Mezclado"].astype(bool)
        if "Operador_Mezclado" not in df.columns:
            df["Operador_Mezclado"] = df["Operador"]
        if "Tipo_Producto" not in df.columns:
            df["Tipo_Producto"] = "Tintas (Estándar)"
        return df
    
    return pd.DataFrame(columns=[
        "ID", "Tipo_Producto", "Departamento", "Propela", "Orden_Fabricacion_Lote", "Codigo_PS", 
        "Area", "Tara_Total_Kg", "Tara_OF_Kg", "Operador", "Operador_Mezclado", "Supervisor", "Auditor",
        "Limpieza_Dispensing", "Checklist_Tara", "Checklist_Limpieza",
        "Limpieza_Propela", "Estatus_Pesado", "En_Mezclado", "Dificultades_Materiales_JSON", 
        "Tiempo_Target_Min", "Min_Permitido", "Max_Permitido", "Rango_Str", "Hora_Inicio_Mezclado"
    ])

def guardar_activas(df):
    df.to_csv(ACTIVAS_FILE, index=False)

def cargar_historial():
    columnas_correctas = [
        "ID Orden", "Fecha Fin", "Departamento", "Lote / OF", "Código PS",
        "Área", "Propela / Cowles", "Tara Total (kg)", "Tara OF (kg)",
        "Estatus Pesado", "Operador Pesado", "Operador Mezclado", "Supervisor", "Auditor",
        "Limpieza Dispensing", "Checklist Tara", "Checklist Limpieza",
        "Limpieza Propela", "Tiempo Std (min)", "Rango Permitido",
        "Tiempo Real Agitación (min)", "Tiempo Prom Dispersión (min)", "Adiciones / Materiales",
        "Estatus Auditoría", "Paro Emergencia", "Observaciones",
        "Firma Operador", "Firma Encargado"
    ]
    if os.path.exists(HISTORIAL_FILE):
        df = pd.read_csv(HISTORIAL_FILE)
        for col in columnas_correctas:
            if col not in df.columns:
                df[col] = ""
        return df[columnas_correctas].fillna("")
    
    return pd.DataFrame(columns=columnas_correctas)

def guardar_en_historial_local(registro):
    df_actual = cargar_historial()
    nuevo_df = pd.DataFrame([registro])
    df_actualizado = pd.concat([df_actual, nuevo_df], ignore_index=True)
    df_actualizado.to_csv(HISTORIAL_FILE, index=False)

def obtener_mapa_cowles_ocupados(df_activas):
    if df_activas.empty:
        return {}
    df_mezclando = df_activas[df_activas["En_Mezclado"] == True]
    mapa = {}
    for _, r in df_mezclando.iterrows():
        mapa[r["Propela"]] = str(r["Orden_Fabricacion_Lote"])
    return mapa

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
# 1. MONITOR DE MEZCLADO EN COWLES
# ---------------------------------------------------------
if menu == "🌀 Monitor de Mezclado en Cowles (En Vivo)":
    st.title("🌀 Monitor de Mezclado en Cowles")
    st.caption("Seguimiento exclusivo de O.F. que se están agitando en tanque en este momento")
    
    df_activas = cargar_activas()
    df_mezclando = df_activas[df_activas["En_Mezclado"] == True] if not df_activas.empty else pd.DataFrame()
    
    if df_mezclando.empty:
        st.info("ℹ️ No hay mezclas activas en Cowles en este momento.")
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
                    st.write(f"**Tipo:** `{row.get('Tipo_Producto', 'Tintas')}`")
                    st.write(f"**Op. Pesado:** `{row['Operador']}` | **Sup:** `{row['Supervisor']}` | **Auditor:** `{row['Auditor']}`")
                    st.caption(f"Inicio Mezclado: {hora_inicio.strftime('%H:%M:%S')}")
                
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
                st.subheader("⚙️ Configuración del Proceso de Mezclado")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    op_mezclado = st.text_input(
                        "👨‍🔧 Operador de Mezclado:", 
                        value=row['Operador_Mezclado'] if row['Operador_Mezclado'] else row['Operador'], 
                        key=f"op_mez_{row['ID']}"
                    )
                with col_m2:
                    limp_propela_val = st.selectbox(
                        "Limpieza Propela:", 
                        OPCIONES_LIMPIEZA, 
                        index=OPCIONES_LIMPIEZA.index(row['Limpieza_Propela']) if row['Limpieza_Propela'] in OPCIONES_LIMPIEZA else 0,
                        key=f"limp_prop_mez_{row['ID']}"
                    )
                with col_m3:
                    chk_limp_val = st.selectbox(
                        "Checklist Limpieza:", 
                        OPCIONES_CHECKLIST, 
                        index=OPCIONES_CHECKLIST.index(row['Checklist_Limpieza']) if row['Checklist_Limpieza'] in OPCIONES_CHECKLIST else 0,
                        key=f"chk_limp_mez_{row['ID']}"
                    )

                st.markdown("---")
                st.subheader("🏁 Finalizar y Registrar Salida de Agitación")
                
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    tiempo_disp = st.number_input("⏱️ Tiempo Prom. Dispersión (min):", min_value=0.0, value=minutos_transcurridos, step=0.5, key=f"disp_{row['ID']}")
                    paro_emergencia = st.checkbox("⚠️ Paro de Emergencia / Falla", key=f"paro_{row['ID']}")

                with col_c2:
                    firma_op = st.text_input("✍️ Firma Operador:", value=op_mezclado, key=f"f_op_{row['ID']}")
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
                        "Operador Pesado": row["Operador"],
                        "Operador Mezclado": op_mezclado,
                        "Supervisor": row["Supervisor"],
                        "Auditor": row["Auditor"],
                        "Limpieza Dispensing": row["Limpieza_Dispensing"],
                        "Checklist Tara": row["Checklist_Tara"],
                        "Checklist Limpieza": chk_limp_val,
                        "Limpieza Propela": limp_propela_val,
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
                        st.success(f"✅ Agitación finalizada y registrada con éxito en Google Sheets.")
                    else:
                        st.success(f"✅ Agitación finalizada y registrada en la base de datos local.")
                    st.rerun()

# ---------------------------------------------------------
# 2. ÁREA DE PESADO Y ESPERA DE O.F.
# ---------------------------------------------------------
elif menu == "📦 Área de Pesado y Espera de O.F.":
    st.title("📦 Área de Pesado y Espera de Materiales")
    st.caption("Administra las O.F. en preparación o pausadas antes de pasarlas a agitación en Cowles")

    df_activas = cargar_activas()
    mapa_ocupados = obtener_mapa_cowles_ocupados(df_activas)
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
                    st.write(f"**Código PS:** `{row['Codigo_PS']}` | **Área:** `{row['Area']}` | **Tipo:** `{row.get('Tipo_Producto', 'Tintas')}`")
                    st.write(f"**Tara Total:** `{row['Tara_Total_Kg']} kg` | **Tara O.F.:** `{row['Tara_OF_Kg']} kg`")
                    st.write(f"**Op. Pesado:** `{row['Operador']}` | **Supervisor:** `{row['Supervisor']}` | **Auditor:** `{row['Auditor']}`")

                with col2:
                    nuevo_estatus = st.selectbox(
                        "Estatus en Pesado:",
                        ESTADOS_PESADO,
                        index=ESTADOS_PESADO.index(row['Estatus_Pesado']) if row['Estatus_Pesado'] in ESTADOS_PESADO else 0,
                        key=f"est_pes_{row['ID']}"
                    )
                    
                    opciones_cowles_format = []
                    index_actual = 0
                    for i, c in enumerate(LISTA_PROPELAS):
                        label = f"🔴 {c} (OCUPADO por O.F. {mapa_ocupados[c]})" if c in mapa_ocupados else f"🟢 {c}"
                        opciones_cowles_format.append(label)
                        if c == row['Propela']:
                            index_actual = i

                    cowles_seleccionado_label = st.selectbox(
                        "Asignar Cowles / Propela:",
                        opciones_cowles_format,
                        index=index_actual,
                        key=f"prop_{row['ID']}"
                    )
                    propela_sel = LISTA_PROPELAS[opciones_cowles_format.index(cowles_seleccionado_label)]

                    if (nuevo_estatus != row['Estatus_Pesado']) or (propela_sel != row['Propela']):
                        df_activas.loc[df_activas["ID"] == row["ID"], "Estatus_Pesado"] = nuevo_estatus
                        df_activas.loc[df_activas["ID"] == row["ID"], "Propela"] = propela_sel
                        guardar_activas(df_activas)
                        st.rerun()

                    st.markdown("---")
                    esta_ocupado = propela_sel in mapa_ocupados
                    if esta_ocupado:
                        st.error(f"🛑 **{propela_sel}** está **OCUPADO**.")
                        st.button("🚫 No se puede meter a mezclar", key=f"btn_disabled_{row['ID']}", disabled=True, use_container_width=True)
                    else:
                        if st.button(f"🚀 Meter a Mezclar ({propela_sel})", key=f"btn_start_{row['ID']}", use_container_width=True):
                            df_activas["Hora_Inicio_Mezclado"] = df_activas["Hora_Inicio_Mezclado"].astype(object)
                            df_activas.loc[df_activas["ID"] == row["ID"], "En_Mezclado"] = True
                            df_activas.loc[df_activas["ID"] == row["ID"], "Hora_Inicio_Mezclado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            guardar_activas(df_activas)
                            st.rerun()

                with st.expander("✏️ Editar Materiales y Datos", expanded=False):
                    try:
                        mat_list_actual = json.loads(row["Dificultades_Materiales_JSON"])
                    except:
                        mat_list_actual = [{"CODIGO": "", "KG EN OF": 0.0, "KG AGREGADOS": 0.0, "OBSERVACIONES": ""}]
                    
                    df_mat_edit = pd.DataFrame(mat_list_actual)
                    tabla_editada = st.data_editor(df_mat_edit, num_rows="dynamic", use_container_width=True, key=f"editor_edit_{row['ID']}")

                    if st.button("💾 Guardar Cambios en O.F.", key=f"btn_save_edit_{row['ID']}" ):
                        mat_updated_json = json.dumps(tabla_editada.dropna(how="all").to_dict(orient="records"))
                        df_activas.loc[df_activas["ID"] == row["ID"], "Dificultades_Materiales_JSON"] = mat_updated_json
                        guardar_activas(df_activas)
                        st.success("✅ Cambios guardados correctamente.")
                        st.rerun()

# ---------------------------------------------------------
# 3. REGISTRAR NUEVA O.F. (CAPTURA EN PESADO)
# ---------------------------------------------------------
elif menu == "📋 Registrar Nueva O.F. (Pesado)":
    st.title("📄 Registrar Nueva O.F. en Pesado")
    st.caption("Captura inicial del lote antes de pasar a agitación")

    df_activas = cargar_activas()
    mapa_ocupados = obtener_mapa_cowles_ocupados(df_activas)

    with st.form("form_registro_of"):
        st.subheader("📌 1. Identificación y Generales")
        tipo_producto = st.radio(
            "🧪 Tipo de Producto (Define la regla de tiempos):", 
            ["Tintas (Estándar)", "Recubrimientos (Manual)"], 
            horizontal=True
        )
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            depto = st.selectbox("Departamento:", ["T1", "T2"])
            operador = st.text_input("Operador Pesado:")
        with col2:
            fecha_aud = st.date_input("Fecha:", datetime.now())
            operador_mezclado_init = st.text_input("Operador Mezclado (Opcional):")
        with col3:
            codigo_ps = st.text_input("Código PS:")
            supervisor = st.text_input("Supervisor:")
        with col4:
            lote = st.text_input("Lote / O.F.:")
            auditor = st.text_input("Auditor:")

        st.markdown("---")
        st.subheader("⚖️ 2. Pesos, Taras e Inspección")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            tara_total = st.number_input("Tara Total (kg):", min_value=0.0, value=250.0, step=10.0)
            tara_of = st.number_input("Tara O.F. (kg):", min_value=0.0, value=15.0, step=0.5)
            area = st.selectbox("Área:", ["Manual Dispensing", "Automático"])
        with c2:
            limpieza_dispensing = st.selectbox("Limpieza Dispensing:", OPCIONES_LIMPIEZA)
            limpieza_propela = st.selectbox("Limpieza Propela:", OPCIONES_LIMPIEZA)
        with c3:
            chk_tara = st.selectbox("Checklist Tara:", OPCIONES_CHECKLIST)
            chk_limpieza = st.selectbox("Checklist Limpieza:", OPCIONES_CHECKLIST)
        with c4:
            opciones_cowles_formateadas = [
                f"🔴 {c} (OCUPADO por O.F. {mapa_ocupados[c]})" if c in mapa_ocupados else f"🟢 {c}"
                for c in LISTA_PROPELAS
            ]
            cowles_seleccionado_label = st.selectbox("Cowles Propuesto:", opciones_cowles_formateadas)
            propela_inicial = LISTA_PROPELAS[opciones_cowles_formateadas.index(cowles_seleccionado_label)]
            estatus_pesado = st.selectbox("Estatus en Pesado:", ESTADOS_PESADO)

        st.markdown("---")
        if tipo_producto == "Tintas (Estándar)":
            tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(tara_total)
            st.info(f"📋 **Tiempo Estándar (Tintas) por Tara Total ({tara_total} kg):** `{rango_str}` (Objetivo: `{tiempo_target} min`)")
        else:
            st.warning("⚠️ **Recubrimientos:** Ingrese el tiempo requerido.")
            tiempo_target = st.number_input("⏱️ Ingresar Tiempo de Propela Manual (min):", min_value=1.0, value=15.0, step=1.0)
            rango_str = f"{tiempo_target} min (Manual Recubrimientos)"
            min_p, max_p = tiempo_target, tiempo_target

        st.markdown("---")
        st.subheader("📦 3. Materiales / Fórmula de Pesado")
        
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
            st.error("❌ Los campos O.F./Lote, Operador Pesado y Auditor son obligatorios.")
        else:
            mat_dict = tabla_materiales.dropna(how="all").to_dict(orient="records")
            mat_json_str = json.dumps(mat_dict)

            nuevo_id = int(datetime.now().timestamp())
            op_mezclado_final = operador_mezclado_init if operador_mezclado_init.strip() else operador

            nueva_fila = {
                "ID": nuevo_id,
                "Tipo_Producto": tipo_producto,
                "Departamento": depto,
                "Propela": propela_inicial,
                "Orden_Fabricacion_Lote": str(lote),
                "Codigo_PS": str(codigo_ps),
                "Area": area,
                "Tara_Total_Kg": tara_total,
                "Tara_OF_Kg": tara_of,
                "Operador": operador,
                "Operador_Mezclado": op_mezclado_final,
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
            st.success(f"✅ O.F. **{lote}** registrada exitosamente.")
            st.balloons()

# ---------------------------------------------------------
# 4. HOJA DE PROCESOS (HISTORIAL DIGITAL CON TABLA DE INCIDENCIAS)
# ---------------------------------------------------------
elif menu == "📊 Hoja de Procesos (Historial)":
    st.title("📊 Hoja de Procesos Digital")
    st.caption("Histórico local de auditorías completadas y desglose de materiales / incidencias")

    df_historial = cargar_historial()

    if df_historial.empty:
        st.info("No hay auditorías registradas en el historial.")
    else:
        # Mostrar tabla principal resumida
        st.subheader("📋 Resumen General de Lotes")
        st.dataframe(df_historial.drop(columns=["Adiciones / Materiales"]), use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Desglose Detallado de Materiales e Incidencias por Lote / O.F.")
        
        # Selector para elegir de qué O.F. ver el detalle limpio de materiales
        lotes_disponibles = df_historial["Lote / OF"].unique().tolist()
        lote_seleccionado = st.selectbox("Seleccione la O.F. o Lote para revisar sus materiales y diferencias:", lotes_disponibles)

        if lote_seleccionado:
            fila_lote = df_historial[df_historial["Lote / OF"] == lote_seleccionado].iloc[0]
            json_materiales = fila_lote["Adiciones / Materiales"]

            st.write(f"**Código PS:** `{fila_lote['Código PS']}` | **Área:** `{fila_lote['Área']}` | **Fecha Fin:** `{fila_lote['Fecha Fin']}`")

            try:
                lista_mats = json.loads(json_materiales)
            except:
                lista_mats = []

            if lista_mats:
                df_mats = pd.DataFrame(lista_mats)
                
                # Normalizar nombres de columnas por seguridad
                df_mats.columns = [str(c).upper().strip() for c in df_mats.columns]
                
                # Asegurar columnas estándar
                for col_requerida in ["CODIGO", "KG EN OF", "KG AGREGADOS", "OBSERVACIONES"]:
                    if col_requerida not in df_mats.columns:
                        df_mats[col_requerida] = ""

                # CALCULAR DIFERENCIA AUTOMÁTICA (KG AGREGADOS - KG EN OF)
                df_mats["KG EN OF"] = pd.to_numeric(df_mats["KG EN OF"], errors="coerce").fillna(0.0)
                df_mats["KG AGREGADOS"] = pd.to_numeric(df_mats["KG AGREGADOS"], errors="coerce").fillna(0.0)
                
                df_mats["DIFERENCIA (kg)"] = df_mats["KG AGREGADOS"] - df_mats["KG EN OF"]
                
                # Crear columna de incidencias automática
                def evaluar_incidencia(row):
                    diff = abs(row["DIFERENCIA (kg)"])
                    obs = str(row["OBSERVACIONES"]).strip()
                    if diff > 0.01 or (obs and obs.lower() != "nan" and obs != ""):
                        return "⚠️ INCIDENCIA"
                    return "✔️ Conforme"

                df_mats["ESTATUS / INCIDENCIA"] = df_mats.apply(evaluar_incidencia, axis=1)

                # Reordenar columnas para visualización impecable
                cols_ordenadas = ["CODIGO", "KG EN OF", "KG AGREGADOS", "DIFERENCIA (kg)", "ESTATUS / INCIDENCIA", "OBSERVACIONES"]
                df_mats = df_mats[[c for c in cols_ordenadas if c in df_mats.columns]]

                # Filtrar solo materiales con incidencias si el usuario prefiere ver puras anomalías, o mostrar todo limpio
                solo_con_incidencias = st.checkbox("🔍 Mostrar únicamente materiales con diferencias o incidencias en este lote", value=False)
                
                if solo_con_incidencias:
                    df_mostrar = df_mats[df_mats["ESTATUS / INCIDENCIA"] == "⚠️ INCIDENCIA"]
                    if df_mostrar.empty:
                        st.success("✨ ¡Excelente! Este lote no registra diferencias de peso ni observaciones en sus materiales.")
                    else:
                        st.dataframe(df_mostrar, use_container_width=True)
                else:
                    st.dataframe(df_mats, use_container_width=True)
            else:
                st.info("No hay registros detallados de materiales para esta O.F.")

        st.markdown("---")
        csv_bytes = df_historial.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Hoja de Procesos Completa en CSV",
            data=csv_bytes,
            file_name=f"hoja_de_procesos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
