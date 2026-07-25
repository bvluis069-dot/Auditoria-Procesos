from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTRUCTURA DE COLUMNAS
# ==========================================
st.set_page_config(
    page_title="Control Molienda - MES", page_icon="📊", layout="wide"
)

# Definición estándar de columnas (alineadas exactamente con la plantilla de Google Sheets)
COLUMNAS_SISTEMA = [
    "Fecha_Hora_Fin",
    "Departamento",
    "Lote / OF",
    "Código PS",
    "Área",
    "Propela / Cowles",
    "Tara Total (kg)",
    "Tara OF (kg)",
    "Estatus Pesado",
    "Operador Pesado",
    "Operador Mezclado",
    "Supervisor",
    "Auditor",
    "Limpieza Dispensing",
    "Checklist Tara",
    "Checklist Limpieza",
    "Limpieza Propela",
    "Tiempo Std (min)",
    "Rango Permitido",
    "Tiempo Real Agitación (min)",
    "Tiempo Prom Dispersión (min)",
    "Adiciones / Materiales",
    "Estatus Auditoría",
    "Paro Emergencia",
    "Observaciones",
    "Firma Operador",
    "Firma Encargado",
]

# Palabras o identificadores clave para detectar Recubrimientos
OPCIONES_RECUBRIMIENTOS = [
    "Recubrimientos",
    "PTPLSME12 - Recubrimientos",
    "PTPLSME13 - Recubrimientos",
    "PTPLSME14 - Recubrimientos",
    "PTPLSME15 - Recubrimientos",
]


# ==========================================
# 2. CONEXIÓN A GOOGLE SHEETS
# ==========================================
@st.cache_resource
def conectar_google_sheets():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet = client.open("Control_Molienda_MES").sheet1
        return sheet
    except Exception as e:
        st.warning(
            f"⚠️ Sin conexión directa a Google Sheets ({e}). Guardando temporalmente en sesión local."
        )
        return None


sheet_gsheets = conectar_google_sheets()

# Inicialización de la tabla local vacía
if "historico" not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=COLUMNAS_SISTEMA)

# ==========================================
# 3. INTERFAZ DE USUARIO Y SELECTORES DINÁMICOS
# ==========================================
st.title("📊 Hoja de Procesos Digital - Control Molienda MES")
st.markdown("---")

# Selectores superiores (fuera del formulario para refrescar la interfaz al cambiar la opción)
col_top1, col_top2 = st.columns(2)
with col_top1:
    area_seleccionada = st.selectbox(
        "Área / Línea de Proceso",
        [
            "Dispersión Tintas",
            "Molienda Tintas",
            "Recubrimientos",
            "Línea Solventes",
        ],
        key="area_sel",
    )

with col_top2:
    propela_seleccionada = st.selectbox(
        "Propela / Cowles",
        [
            "PTPLSME01 - Dispersor Cowles 1",
            "PTPLSME02 - Dispersor Cowles 2",
            "PTPLSME12 - Recubrimientos",
            "PTPLSME13 - Recubrimientos",
            "PTPLSME14 - Recubrimientos",
            "PTPLSME15 - Recubrimientos",
        ],
        key="propela_sel",
    )

# Verificación condicional si pertenece a Recubrimientos
es_recubrimientos = (
    area_seleccionada in OPCIONES_RECUBRIMIENTOS
    or propela_seleccionada in OPCIONES_RECUBRIMIENTOS
    or "Recubrimientos" in area_seleccionada
    or "Recubrimientos" in propela_seleccionada
)

# ==========================================
# 4. FORMULARIO PRINCIPAL
# ==========================================
with st.form("form_proceso_molienda", clear_on_submit=False):
    st.subheader("📋 Datos Generales de la Orden")
    c1, c2, c3 = st.columns(3)
    with c1:
        departamento = st.selectbox("Departamento", ["T1", "T2"])
        lote_of = st.text_input("Lote / OF")
    with c2:
        codigo_ps = st.text_input("Código PS")
        estatus_pesado = st.selectbox(
            "Estatus Pesado", ["Conforme", "No Conforme", "Pendiente"]
        )
    with c3:
        tara_total = st.number_input(
            "Tara Total (kg)", min_value=0.0, step=0.1, value=0.0
        )
        tara_of = st.number_input(
            "Tara OF (kg)", min_value=0.0, step=0.1, value=0.0
        )

    st.subheader("👥 Personal Operativo y Auditoría")
    c4, c5, c6 = st.columns(3)
    with c4:
        operador_pesado = st.text_input("Operador Pesado")
        operador_mezclado = st.text_input("Operador Mezclado")
    with c5:
        supervisor = st.text_input("Supervisor")
        auditor = st.text_input("Auditor")
    with c6:
        estatus_auditoria = st.selectbox(
            "Estatus Auditoría", ["Aprobado", "Con Observaciones", "Rechazado"]
        )
        paro_emergencia = st.radio(
            "¿Paro de Emergencia?", ["No", "Sí"], horizontal=True
        )

    st.subheader("✅ Checklists y Limpieza")
    c7, c8, c9, c10 = st.columns(4)
    with c7:
        limpieza_dispensing = st.selectbox(
            "Limpieza Dispensing", ["OK", "N/A", "Pendiente"]
        )
    with c8:
        checklist_tara = st.selectbox(
            "Checklist Tara", ["OK", "N/A", "Pendiente"]
        )
    with c9:
        checklist_limpieza = st.selectbox(
            "Checklist Limpieza", ["OK", "N/A", "Pendiente"]
        )
    with c10:
        limpieza_propela = st.selectbox(
            "Limpieza Propela", ["OK", "N/A", "Pendiente"]
        )

    # --- SECCIÓN CONDICIONAL DE TIEMPOS DE PROPELA ---
    st.subheader("⏱️ Control de Tiempos de Agitación / Propela")

    if es_recubrimientos:
        st.info(
            "💡 **Recubrimientos Detectado:** Los tiempos no están estandarizados para esta área. Ingrese el tiempo real de propela."
        )
        tiempo_real_ag = st.number_input(
            "Tiempo Real Agitación / Propela (min)",
            min_value=0.0,
            max_value=300.0,
            value=15.0,
            step=1.0,
        )
        tiempo_std = "Manual"
        rango_permitido = f"{tiempo_real_ag:.0f} min (Manual Recubrimientos)"
        tiempo_prom_disp = tiempo_real_ag
    else:
        st.success(
            "⚙️ **Área Tintas (Estandarizada):** El tiempo estándar se calcula según la Tara Total."
        )
        if tara_total <= 200:
            tiempo_std = 10.0
            rango_permitido = "10 min"
        elif 200 < tara_total <= 500:
            tiempo_std = 17.5
            rango_permitido = "15 a 20 min"
        else:
            tiempo_std = 27.5
            rango_permitido = "25 a 30 min"

        tiempo_real_ag = st.number_input(
            "Tiempo Real Agitación (min)",
            min_value=0.0,
            value=float(
                tiempo_std
                if isinstance(tiempo_std, (int, float))
                else 15.0
            ),
            step=1.0,
        )
        tiempo_prom_disp = tiempo_real_ag

    st.subheader("📝 Observaciones y Firmas")
    c11, c12 = st.columns(2)
    with c11:
        adiciones_materiales = st.text_area("Adiciones / Materiales", height=70)
        observaciones = st.text_area("Observaciones", height=70)
    with c12:
        firma_operador = st.text_input("Firma Operador (Iniciales / Empleado)")
        firma_encargado = st.text_input(
            "Firma Encargado (Iniciales / Empleado)"
        )

    btn_guardar = st.form_submit_button(
        "💾 Registrar en Base de Datos y Google Sheets",
        use_container_width=True,
    )

# ==========================================
# 5. GUARDADO Y REGISTRO EN GOOGLE SHEETS
# ==========================================
if btn_guardar:
    if not lote_of or not codigo_ps:
        st.error(
            "❌ Campos obligatorios faltantes: Registre el **Lote / OF** y el **Código PS**."
        )
    else:
        fecha_fin_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Diccionario con llaves idénticas a COLUMNAS_SISTEMA (Evita que aparezca 'None')
        registro_dict = {
            "Fecha_Hora_Fin": fecha_fin_str,
            "Departamento": departamento or "",
            "Lote / OF": lote_of or "",
            "Código PS": codigo_ps or "",
            "Área": area_seleccionada or "",
            "Propela / Cowles": propela_seleccionada or "",
            "Tara Total (kg)": float(tara_total),
            "Tara OF (kg)": float(tara_of),
            "Estatus Pesado": estatus_pesado or "",
            "Operador Pesado": operador_pesado or "",
            "Operador Mezclado": operador_mezclado or "",
            "Supervisor": supervisor or "",
            "Auditor": auditor or "",
            "Limpieza Dispensing": limpieza_dispensing or "",
            "Checklist Tara": checklist_tara or "",
            "Checklist Limpieza": checklist_limpieza or "",
            "Limpieza Propela": limpieza_propela or "",
            "Tiempo Std (min)": tiempo_std,
            "Rango Permitido": rango_permitido,
            "Tiempo Real Agitación (min)": float(tiempo_real_ag),
            "Tiempo Prom Dispersión (min)": float(tiempo_prom_disp),
            "Adiciones / Materiales": adiciones_materiales or "",
            "Estatus Auditoría": estatus_auditoria or "",
            "Paro Emergencia": paro_emergencia or "",
            "Observaciones": observaciones or "",
            "Firma Operador": firma_operador or "",
            "Firma Encargado": firma_encargado or "",
        }

        # 1. Enviar a Google Sheets
        if sheet_gsheets is not None:
            try:
                fila_gsheets = [
                    str(registro_dict[col]) for col in COLUMNAS_SISTEMA
                ]
                sheet_gsheets.append_row(fila_gsheets)
                st.success("✅ Guardado correctamente en Google Sheets.")
            except Exception as e:
                st.error(f"❌ Error al enviar a Google Sheets: {e}")

        # 2. Actualizar DataFrame en la sesión local sin 'None'
        nuevo_df = pd.DataFrame([registro_dict], columns=COLUMNAS_SISTEMA)
        st.session_state.historico = pd.concat(
            [st.session_state.historico, nuevo_df], ignore_index=True
        ).fillna("")

        st.toast("🎉 Registro procesado y guardado.", icon="💾")

# ==========================================
# 6. HISTÓRICO VISUAL
# ==========================================
st.markdown("---")
st.subheader("📈 Histórico local de auditorías completadas")

if (
    "historico" in st.session_state
    and not st.session_state.historico.empty
):
    st.dataframe(
        st.session_state.historico.fillna(""), use_container_width=True
    )
else:
    st.info("No hay registros capturados en esta sesión.")
