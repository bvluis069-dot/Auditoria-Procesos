import pandas as pd
import streamlit as st

# Definición de áreas de Recubrimientos
AREAS_RECUBRIMIENTOS = ["Recubrimientos", "RECUBRIMIENTOS", "Recubrimientos Línea 1"]

st.title("Hoja de Procesos Digital")

with st.form("form_control_molienda", clear_on_submit=False):

    # --- SECCIÓN 1: DATOS GENERALES ---
    col1, col2 = st.columns(2)
    with col1:
        departamento = st.selectbox("Departamento", ["T1", "T2"])
        orden_fabricacion = st.text_input("Orden de Fabricación / Lote")
        codigo_ps = st.text_input("Código PS")
    with col2:
        area = st.selectbox(
            "Área", ["Dispersión", "Molienda", "Recubrimientos", "Envasado"]
        )
        propela_cowles = st.text_input("Propela / Cowles")

    # --- SECCIÓN 2: PESOS Y TARA ---
    col3, col4 = st.columns(2)
    with col3:
        tara_total = st.number_input(
            "Tara Total (kg)", min_value=0.0, step=0.1
        )
    with col4:
        tara_of = st.number_input("Tara OF (kg)", min_value=0.0, step=0.1)

    # --- SECCIÓN 3: CONDICIONAL DE RECUBRIMIENTOS (TIEMPO PROPELA) ---
    st.markdown("---")
    st.subheader("Tiempos de Agitación")

    # Verificamos si la selección corresponde a Recubrimientos
    es_recubrimientos = area in AREAS_RECUBRIMIENTOS

    if es_recubrimientos:
        st.info("ℹ️ Área de Recubrimientos detectada: Ingrese el tiempo real de propela.")
        tiempo_real_ag = st.number_input(
            "Tiempo Real Agitación / Propela (min)",
            min_value=0,
            value=0,
            step=1,
            help="Habilitado por no contar con tiempo estandarizado en Recubrimientos.",
        )
    else:
        # Para áreas estandarizadas se deshabilita o asigna valor fijo
        tiempo_real_ag = st.number_input(
            "Tiempo Real Agitación / Propela (min)",
            value=0,
            disabled=True,
            help="El tiempo está estandarizado para esta área.",
        )

    # --- BOTÓN DE ENVÍO ---
    submitted = st.form_submit_button("Guardar Registro")

    if submitted:
        # Validación rápida para evitar enviar campos vacíos principales
        if not orden_fabricacion or not codigo_ps:
            st.error("⚠️ Por favor completa la Orden de Fabricación y Código PS antes de enviar.")
        else:
            from datetime import datetime

            fecha_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Mapeo exacto del diccionario alineado con las columnas de Google Sheets
            nuevo_registro = {
                "Fecha_Hora_Fin": fecha_fin,
                "Departamento": departamento,
                "Propela": propela_cowles,
                "Orden_Fabricacion_Lote": orden_fabricacion,
                "Codigo_PS": codigo_ps,
                "Area": area,
                "Tara_Total_Kg": tara_total,
                "Tara_OF_Kg": tara_of,
                "Tiempo_Real_Ag": tiempo_real_ag if es_recubrimientos else "Std",
            }

            # 1. Guardar/Añadir a Google Sheets (usando tu función de gspread)
            # sheet.append_row(list(nuevo_registro.values()))

            # 2. Guardar en session_state para la tabla visual
            if "historico" not in st.session_state:
                st.session_state.historico = pd.DataFrame()

            df_nuevo = pd.DataFrame([nuevo_registro])
            st.session_state.historico = pd.concat(
                [st.session_state.historico, df_nuevo], ignore_index=True
            )

            st.success("✅ Registro guardado exitosamente.")

# --- MOSTRAR TABLA LOCAL ---
if "historico" in st.session_state and not st.session_state.historico.empty:
    st.subheader("Histórico local de auditorías completadas")
    st.dataframe(st.session_state.historico, use_container_width=True)
