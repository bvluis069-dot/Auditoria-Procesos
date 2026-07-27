import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Control de Procesos — Pesado y Agitación",
    page_icon="⚙️",
    layout="wide"
)

# ─────────────────────────────────────────────
# CSS: Diseño formal, paleta industrial oscura
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.85rem;
    color: #8b949e;
    padding: 4px 0;
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: #e6edf3 !important;
}

/* Títulos principales */
h1 { 
    font-weight: 700 !important; 
    font-size: 1.6rem !important;
    color: #e6edf3 !important;
    border-bottom: 2px solid #1f6feb;
    padding-bottom: 10px;
    margin-bottom: 4px !important;
}
h2 { 
    font-weight: 600 !important; 
    font-size: 1.15rem !important;
    color: #c9d1d9 !important;
}
h3 { 
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: #8b949e !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Cards / secciones */
.card-section {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.card-section-title {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
}

/* Tarjeta de propela destacada */
.propela-card {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #1f6feb;
    border-left: 4px solid #1f6feb;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 16px;
}
.propela-card-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: #58a6ff;
    margin-bottom: 4px;
}
.propela-card-sub {
    font-size: 0.8rem;
    color: #6e7681;
}

/* Chip de estado */
.chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}
.chip-green  { background: #1a3a2a; color: #3fb950; border: 1px solid #2ea043; }
.chip-yellow { background: #3a2d0e; color: #d29922; border: 1px solid #9e6a03; }
.chip-red    { background: #3a0e0e; color: #f85149; border: 1px solid #b91c1c; }
.chip-blue   { background: #0d2240; color: #58a6ff; border: 1px solid #1f6feb; }
.chip-gray   { background: #21262d; color: #8b949e; border: 1px solid #30363d; }

/* Métricas personalizadas */
.metric-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 14px 18px;
    text-align: center;
}
.metric-box .metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: #58a6ff;
    line-height: 1.1;
}
.metric-box .metric-lbl {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #6e7681;
    margin-top: 4px;
}

/* Alerta tiempo cumplido */
.alert-stop {
    background: linear-gradient(135deg, #3a0e0e, #1a0505);
    border: 2px solid #f85149;
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
    animation: pulse-border 1.5s ease-in-out infinite;
}
.alert-stop .alert-title {
    font-size: 1rem;
    font-weight: 700;
    color: #f85149;
    letter-spacing: 0.04em;
}
.alert-stop .alert-sub {
    font-size: 0.82rem;
    color: #ffa198;
    margin-top: 4px;
}

@keyframes pulse-border {
    0%, 100% { border-color: #f85149; }
    50%       { border-color: #ff7b72; box-shadow: 0 0 12px rgba(248,81,73,0.4); }
}

/* Info box pendiente */
.alert-wait {
    background: #0d2014;
    border: 1px solid #2ea043;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #7ee787;
}

/* Tabla operador */
.op-row {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 6px;
}
.op-row .op-icon {
    font-size: 1.2rem;
    width: 30px;
    text-align: center;
}
.op-row .op-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6e7681;
}
.op-row .op-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: #e6edf3;
}

/* Divider con texto */
.section-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 20px 0 16px 0;
}
.section-divider .divider-line {
    flex: 1;
    height: 1px;
    background: #21262d;
}
.section-divider .divider-text {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6e7681;
    white-space: nowrap;
}

/* Botón primario */
.stButton > button[kind="primary"] {
    background: #1f6feb !important;
    border: 1px solid #388bfd !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}
.stButton > button[kind="primary"]:hover {
    background: #388bfd !important;
}

/* Botón de cancelar / error */
.btn-cancel > button {
    background: #1a0505 !important;
    border: 1px solid #6e1a1a !important;
    color: #f85149 !important;
    font-weight: 600 !important;
}
.btn-cancel > button:hover {
    background: #3a0e0e !important;
    border-color: #f85149 !important;
}

/* Caption / subtítulo página */
.page-caption {
    font-size: 0.82rem;
    color: #6e7681;
    margin-top: -8px;
    margin-bottom: 20px;
}

/* Inline data chip */
.data-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 1px 7px;
    color: #c9d1d9;
    display: inline-block;
}

/* Badge propela disponible / ocupada */
.badge-libre    { color: #3fb950; font-weight: 700; }
.badge-ocupado  { color: #f85149; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# JS: Web Notifications + Sonido
# ─────────────────────────────────────
st.markdown("""
<script>
// Solicitar permiso de notificaciones al cargar
if ("Notification" in window) {
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }
}

// Función global para enviar notificación
function notificarPropela(titulo, cuerpo) {
    if ("Notification" in window && Notification.permission === "granted") {
        const n = new Notification(titulo, {
            body: cuerpo,
            icon: "https://cdn-icons-png.flaticon.com/512/2821/2821637.png",
            requireInteraction: true
        });
        // Sonido de alerta (beep simple)
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880;
            gain.gain.value = 0.3;
            osc.start();
            setTimeout(() => { osc.stop(); ctx.close(); }, 600);
        } catch(e) {}
    }
}

// Exponer para Streamlit via window
window._notificarPropela = notificarPropela;
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# Constantes
# ─────────────────────────────────────
ACTIVAS_FILE   = "auditorias_activas.csv"
HISTORIAL_FILE = "hoja_de_procesos_agitacion.csv"
ERRORES_FILE   = "procesos_cancelados.csv"

GOOGLE_CREDENTIALS  = "mes-molienda-sanchez-7a9a01e5553d.json"
GOOGLE_SHEET_NAME   = "Control_Molienda_MES"
WORKSHEET_PROPELAS  = "Historial_Propelas"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

LISTA_PROPELAS = [f"PTPLSME{i:02d} - Tintas" for i in range(1, 12)] + [
    f"PTPLSME{i:02d} - Recubrimientos" for i in range(12, 16)
]

ESTADOS_PESADO = [
    "En Espera (Pesado)",
    "Pausado — Falta de Material",
    "Pesado Concluido — Listo para Mezclar"
]

OPCIONES_LIMPIEZA  = ["Buena", "Regular", "Mala"]
OPCIONES_CHECKLIST = ["SÍ", "NO", "N/A"]

MOTIVOS_CANCELACION = [
    "Error de captura de datos",
    "O.F. cancelada por producción",
    "Material incorrecto",
    "Falla de equipo (Cowles)",
    "Contaminación / producto fuera de spec",
    "Orden duplicada",
    "Otro (especificar en observaciones)"
]

# ─────────────────────────────────────
# Google Sheets
# ─────────────────────────────────────
@st.cache_resource
def conectar_google_sheets():
    try:
        creds  = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client.open(GOOGLE_SHEET_NAME)
    except Exception:
        return None

def guardar_en_google_sheets(datos):
    try:
        libro = conectar_google_sheets()
        if not libro:
            return False
        hoja = libro.worksheet(WORKSHEET_PROPELAS)
        fila = [
            datos.get("ID Orden",""), datos.get("Fecha Fin",""),
            datos.get("Departamento",""), datos.get("Lote / OF",""),
            datos.get("Código PS",""), datos.get("Área",""),
            datos.get("Propela / Cowles",""), datos.get("Tara Total (kg)",""),
            datos.get("Tara OF (kg)",""), datos.get("Estatus Pesado",""),
            datos.get("Operador Pesado",""), datos.get("Operador Mezclado",""),
            datos.get("Supervisor",""), datos.get("Auditor",""),
            datos.get("Limpieza Dispensing",""), datos.get("Checklist Tara",""),
            datos.get("Checklist Limpieza",""), datos.get("Limpieza Propela",""),
            datos.get("Tiempo Std (min)",""), datos.get("Rango Permitido",""),
            datos.get("Tiempo Real Agitación (min)",""),
            datos.get("Tiempo Prom Dispersión (min)",""),
            datos.get("Adiciones / Materiales",""), datos.get("Estatus Auditoría",""),
            datos.get("Paro Emergencia",""), datos.get("Observaciones",""),
            datos.get("Firma Operador",""), datos.get("Firma Encargado","")
        ]
        hoja.append_row(fila)
        return True
    except Exception as e:
        st.warning(f"Nota: guardado localmente. Falla Google Sheets: {e}")
        return False

# ─────────────────────────────────────
# Lógica de tiempos
# ─────────────────────────────────────
def calcular_regla_tiempo(tara_total_kg):
    if tara_total_kg <= 200:
        return 10.0, "10 min", 10.0, 10.0
    elif tara_total_kg <= 500:
        return 17.5, "15 a 20 min", 15.0, 20.0
    else:
        return 27.5, "25 a 30 min", 25.0, 30.0

# ─────────────────────────────────────
# CSV helpers
# ─────────────────────────────────────
def cargar_activas():
    if os.path.exists(ACTIVAS_FILE):
        df = pd.read_csv(ACTIVAS_FILE)
        cols_texto = [
            "Tipo_Producto","Departamento","Propela","Orden_Fabricacion_Lote","Codigo_PS",
            "Area","Operador","Operador_Mezclado","Supervisor","Auditor",
            "Limpieza_Dispensing","Checklist_Tara","Checklist_Limpieza","Limpieza_Propela",
            "Estatus_Pesado","Dificultades_Materiales_JSON","Rango_Str","Hora_Inicio_Mezclado"
        ]
        for c in cols_texto:
            if c in df.columns:
                df[c] = df[c].fillna("").astype(object)
        if "En_Mezclado" in df.columns:
            df["En_Mezclado"] = df["En_Mezclado"].astype(bool)
        if "Operador_Mezclado" not in df.columns:
            df["Operador_Mezclado"] = df["Operador"]
        if "Tipo_Producto" not in df.columns:
            df["Tipo_Producto"] = "Tintas (Estándar)"
        return df
    return pd.DataFrame(columns=[
        "ID","Tipo_Producto","Departamento","Propela","Orden_Fabricacion_Lote","Codigo_PS",
        "Area","Tara_Total_Kg","Tara_OF_Kg","Operador","Operador_Mezclado","Supervisor","Auditor",
        "Limpieza_Dispensing","Checklist_Tara","Checklist_Limpieza","Limpieza_Propela",
        "Estatus_Pesado","En_Mezclado","Dificultades_Materiales_JSON",
        "Tiempo_Target_Min","Min_Permitido","Max_Permitido","Rango_Str","Hora_Inicio_Mezclado"
    ])

def guardar_activas(df):
    df.to_csv(ACTIVAS_FILE, index=False)

def cargar_historial():
    cols = [
        "ID Orden","Fecha Fin","Departamento","Lote / OF","Código PS",
        "Área","Propela / Cowles","Tara Total (kg)","Tara OF (kg)",
        "Estatus Pesado","Operador Pesado","Operador Mezclado","Supervisor","Auditor",
        "Limpieza Dispensing","Checklist Tara","Checklist Limpieza",
        "Limpieza Propela","Tiempo Std (min)","Rango Permitido",
        "Tiempo Real Agitación (min)","Tiempo Prom Dispersión (min)",
        "Adiciones / Materiales","Estatus Auditoría","Paro Emergencia",
        "Observaciones","Firma Operador","Firma Encargado"
    ]
    if os.path.exists(HISTORIAL_FILE):
        df = pd.read_csv(HISTORIAL_FILE)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df[cols].fillna("")
    return pd.DataFrame(columns=cols)

def guardar_en_historial_local(registro):
    df = cargar_historial()
    df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    df.to_csv(HISTORIAL_FILE, index=False)

def cargar_errores():
    cols = [
        "ID Orden","Fecha Cancelación","Motivo","Observaciones Cancelación",
        "Cancelado Por","Departamento","Lote / OF","Código PS",
        "Propela","Fase al Cancelar","Tiempo Transcurrido (min)"
    ]
    if os.path.exists(ERRORES_FILE):
        df = pd.read_csv(ERRORES_FILE)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df[cols].fillna("")
    return pd.DataFrame(columns=cols)

def guardar_en_errores(registro):
    df = cargar_errores()
    df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    df.to_csv(ERRORES_FILE, index=False)

def obtener_mapa_cowles_ocupados(df_activas):
    if df_activas.empty:
        return {}
    mapa = {}
    for _, r in df_activas[df_activas["En_Mezclado"] == True].iterrows():
        mapa[r["Propela"]] = str(r["Orden_Fabricacion_Lote"])
    return mapa

# ─────────────────────────────────────
# Helper visual
# ─────────────────────────────────────
def chip_estatus(texto):
    texto_lower = texto.lower()
    if "concluido" in texto_lower or "listo" in texto_lower:
        cls = "chip-green"
    elif "pausado" in texto_lower or "falta" in texto_lower:
        cls = "chip-yellow"
    elif "espera" in texto_lower:
        cls = "chip-gray"
    else:
        cls = "chip-blue"
    return f'<span class="chip {cls}">{texto}</span>'

def notif_js(titulo, cuerpo):
    """Inyecta JS para disparar notificación del sistema."""
    return f"""
    <script>
    (function() {{
        if ("Notification" in window && Notification.permission === "granted") {{
            const n = new Notification({json.dumps(titulo)}, {{
                body: {json.dumps(cuerpo)},
                requireInteraction: true
            }});
        }} else if ("Notification" in window && Notification.permission !== "denied") {{
            Notification.requestPermission().then(p => {{
                if (p === "granted") {{
                    new Notification({json.dumps(titulo)}, {{
                        body: {json.dumps(cuerpo)},
                        requireInteraction: true
                    }});
                }}
            }});
        }}
    }})();
    </script>
    """

# ═══════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 8px 0;">
        <div style="font-size:0.65rem; text-transform:uppercase; letter-spacing:0.12em; color:#6e7681; margin-bottom:2px;">
            GRUPO SÁNCHEZ · MES
        </div>
        <div style="font-size:1.1rem; font-weight:700; color:#e6edf3;">
            Control Molienda
        </div>
        <div style="font-size:0.78rem; color:#6e7681;">Pesado y Agitación en Cowles</div>
    </div>
    <hr style="border:none; border-top:1px solid #21262d; margin:12px 0 16px 0;">
    """, unsafe_allow_html=True)

    menu = st.radio(
        "Navegación",
        [
            "Monitor — Agitación en Vivo",
            "Área de Pesado y Espera",
            "Registrar Nueva O.F.",
            "Historial de Procesos",
            "Procesos Cancelados"
        ],
        label_visibility="collapsed"
    )

    st.markdown('<hr style="border:none; border-top:1px solid #21262d; margin:16px 0;">', unsafe_allow_html=True)
    if st.button("Actualizar pantalla", use_container_width=True):
        st.rerun()

    # Mini-resumen en sidebar
    df_tmp = cargar_activas()
    if not df_tmp.empty:
        activos_mez = int(df_tmp["En_Mezclado"].sum())
        activos_pes = int((df_tmp["En_Mezclado"] == False).sum())
        st.markdown(f"""
        <div style="background:#161b22; border:1px solid #30363d; border-radius:6px; padding:12px 14px; font-size:0.78rem;">
            <div style="color:#6e7681; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">Estado actual</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#8b949e;">En agitación</span>
                <span style="color:#3fb950; font-weight:700; font-family:monospace;">{activos_mez}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#8b949e;">En pesado/espera</span>
                <span style="color:#d29922; font-weight:700; font-family:monospace;">{activos_pes}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# VISTA 1 — MONITOR DE AGITACIÓN EN VIVO
# ═══════════════════════════════════════════════════════════
if menu == "Monitor — Agitación en Vivo":
    st.markdown("# Monitor de Agitación en Cowles")
    st.markdown('<div class="page-caption">Seguimiento en tiempo real de O.F. en proceso de agitación</div>', unsafe_allow_html=True)

    df_activas = cargar_activas()
    df_mezclando = df_activas[df_activas["En_Mezclado"] == True] if not df_activas.empty else pd.DataFrame()

    if df_mezclando.empty:
        st.markdown("""
        <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:40px;
                    text-align:center; color:#6e7681; margin-top:20px;">
            <div style="font-size:2rem; margin-bottom:8px;">⚙️</div>
            <div style="font-weight:600; color:#8b949e; margin-bottom:4px;">Sin agitaciones activas</div>
            <div style="font-size:0.82rem;">No hay O.F. en proceso de mezclado en este momento.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chip chip-green" style="margin-bottom:16px;">⚡ {len(df_mezclando)} agitación(es) activa(s)</div>', unsafe_allow_html=True)
        ahora = datetime.now()

        for idx, row in df_mezclando.iterrows():
            hora_inicio = datetime.strptime(str(row["Hora_Inicio_Mezclado"]), "%Y-%m-%d %H:%M:%S")
            mins_trans  = (ahora - hora_inicio).total_seconds() / 60.0
            tiempo_ok   = mins_trans >= row["Min_Permitido"]

            # Notificación JS si se acaba de cumplir el tiempo (ventana ±0.5 min)
            if tiempo_ok and mins_trans <= row["Min_Permitido"] + 0.5:
                st.markdown(notif_js(
                    f"⚠️ APAGAR COWLES — {row['Propela']}",
                    f"O.F. {row['Orden_Fabricacion_Lote']} ha alcanzado el tiempo mínimo ({row['Min_Permitido']} min). ¡Detener agitación!"
                ), unsafe_allow_html=True)

            with st.expander(
                f"{'🔴' if tiempo_ok else '🟢'}  {row['Propela']}  ·  O.F.: {row['Orden_Fabricacion_Lote']}  ·  {mins_trans:.1f} min transcurridos",
                expanded=True
            ):
                # ── Cabecera tarjeta
                st.markdown(f"""
                <div class="propela-card">
                    <div class="propela-card-title">{row['Propela']}</div>
                    <div class="propela-card-sub">
                        O.F. / Lote: <strong style="color:#c9d1d9">{row['Orden_Fabricacion_Lote']}</strong>
                        &nbsp;·&nbsp; Código PS: <strong style="color:#c9d1d9">{row['Codigo_PS']}</strong>
                        &nbsp;·&nbsp; Depto: <strong style="color:#c9d1d9">{row['Departamento']}</strong>
                        &nbsp;·&nbsp; Tipo: <strong style="color:#c9d1d9">{row.get('Tipo_Producto','Tintas')}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Fila de métricas
                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-val">{mins_trans:.1f}</div>
                        <div class="metric-lbl">Min. transcurridos</div>
                    </div>""", unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-val" style="color:#d29922;">{row['Rango_Str']}</div>
                        <div class="metric-lbl">Rango estándar</div>
                    </div>""", unsafe_allow_html=True)
                with mc3:
                    color_tara = "#58a6ff"
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-val" style="color:{color_tara};">{row['Tara_Total_Kg']} kg</div>
                        <div class="metric-lbl">Tara total</div>
                    </div>""", unsafe_allow_html=True)
                with mc4:
                    inicio_fmt = hora_inicio.strftime('%H:%M:%S')
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-val" style="font-size:1.3rem; color:#8b949e;">{inicio_fmt}</div>
                        <div class="metric-lbl">Hora de inicio</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Alerta de tiempo
                if tiempo_ok:
                    st.markdown(f"""
                    <div class="alert-stop">
                        <div class="alert-title">⛔ TIEMPO CUMPLIDO — APAGAR COWLES</div>
                        <div class="alert-sub">{mins_trans:.1f} min transcurridos · Rango: {row['Rango_Str']}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    falta = row["Min_Permitido"] - mins_trans
                    st.markdown(f"""
                    <div class="alert-wait">
                        ⏳ &nbsp;Agitando — faltan aproximadamente <strong>{falta:.1f} min</strong>
                        para alcanzar el tiempo mínimo establecido.
                    </div>""", unsafe_allow_html=True)

                # ── Sección: Configuración en Propela ────────────────────
                st.markdown("""
                <div class="section-divider">
                    <div class="divider-line"></div>
                    <div class="divider-text">Configuración en Propela</div>
                    <div class="divider-line"></div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div class="card-section">', unsafe_allow_html=True)
                st.markdown('<div class="card-section-title">Datos del equipo y operador asignado</div>', unsafe_allow_html=True)

                pr1, pr2, pr3, pr4 = st.columns([2, 1.5, 1.5, 2])

                with pr1:
                    # Cowles asignado (solo lectura visual, no cambia aquí)
                    st.markdown(f"""
                    <div style="margin-bottom:12px;">
                        <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.07em;
                                    color:#6e7681; margin-bottom:4px;">Cowles / Propela asignada</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;
                                    font-weight:700; color:#58a6ff;">{row['Propela']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Tara total (informativa)
                    st.markdown(f"""
                    <div>
                        <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.07em;
                                    color:#6e7681; margin-bottom:4px;">Tara total cargada</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;
                                    font-weight:700; color:#c9d1d9;">{row['Tara_Total_Kg']} kg</div>
                    </div>
                    """, unsafe_allow_html=True)

                with pr2:
                    limp_propela_val = st.selectbox(
                        "Limpieza de propela",
                        OPCIONES_LIMPIEZA,
                        index=OPCIONES_LIMPIEZA.index(row['Limpieza_Propela'])
                              if row['Limpieza_Propela'] in OPCIONES_LIMPIEZA else 0,
                        key=f"limp_prop_mez_{row['ID']}"
                    )

                with pr3:
                    chk_limp_val = st.selectbox(
                        "Checklist limpieza",
                        OPCIONES_CHECKLIST,
                        index=OPCIONES_CHECKLIST.index(row['Checklist_Limpieza'])
                              if row['Checklist_Limpieza'] in OPCIONES_CHECKLIST else 0,
                        key=f"chk_limp_mez_{row['ID']}"
                    )

                with pr4:
                    # Operador mezclado: si es el mismo que pesado se autocompleta
                    op_default = row['Operador_Mezclado'] if row['Operador_Mezclado'] else row['Operador']
                    mismo_operador = op_default == row['Operador']

                    st.markdown(f"""
                    <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.07em;
                                color:#6e7681; margin-bottom:4px;">Operador de mezclado</div>
                    """, unsafe_allow_html=True)

                    if mismo_operador:
                        st.markdown(f"""
                        <div style="background:#0d2240; border:1px solid #1f6feb; border-radius:5px;
                                    padding:6px 10px; font-size:0.82rem; color:#58a6ff; margin-bottom:6px;">
                            ↩ Mismo que pesado: <strong>{row['Operador']}</strong>
                        </div>
                        """, unsafe_allow_html=True)

                    op_mezclado = st.text_input(
                        "Operador de mezclado",
                        value=op_default,
                        key=f"op_mez_{row['ID']}",
                        label_visibility="collapsed",
                        placeholder="Nombre operador mezclado"
                    )

                st.markdown('</div>', unsafe_allow_html=True)  # /card-section

                # ── Sección: Finalizar ───────────────────────────────────
                st.markdown("""
                <div class="section-divider">
                    <div class="divider-line"></div>
                    <div class="divider-text">Cierre de proceso</div>
                    <div class="divider-line"></div>
                </div>
                """, unsafe_allow_html=True)

                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    tiempo_disp = st.number_input(
                        "Tiempo promedio dispersión (min)",
                        min_value=0.0, value=round(mins_trans, 1), step=0.5,
                        key=f"disp_{row['ID']}"
                    )
                    paro_emergencia = st.checkbox("Paro de emergencia / falla de equipo", key=f"paro_{row['ID']}")
                with fc2:
                    firma_op  = st.text_input("Firma operador", value=op_mezclado, key=f"f_op_{row['ID']}")
                    obs       = st.text_area("Observaciones", key=f"obs_{row['ID']}",
                                             placeholder="Muestras OK, adición de solvente…", height=90)
                with fc3:
                    firma_enc = st.text_input("Firma encargado / supervisor", value=row['Supervisor'],
                                             key=f"f_enc_{row['ID']}")

                col_fin, col_cancel = st.columns([3, 1])
                with col_fin:
                    if st.button("Finalizar agitación y exportar", key=f"btn_fin_{row['ID']}",
                                 use_container_width=True, type="primary"):
                        tiempo_final = round(mins_trans, 1)
                        cumple = (row["Min_Permitido"] <= tiempo_final <= row["Max_Permitido"]) and not paro_emergencia
                        estatus_audit = ("PARO DE EMERGENCIA" if paro_emergencia
                                         else ("CUMPLE" if cumple else "DESVIACIÓN"))

                        datos_gs = {
                            "ID Orden": row["ID"], "Fecha Fin": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Departamento": row["Departamento"], "Lote / OF": row["Orden_Fabricacion_Lote"],
                            "Código PS": row["Codigo_PS"], "Área": row["Area"],
                            "Propela / Cowles": row["Propela"],
                            "Tara Total (kg)": row["Tara_Total_Kg"], "Tara OF (kg)": row["Tara_OF_Kg"],
                            "Estatus Pesado": row["Estatus_Pesado"],
                            "Operador Pesado": row["Operador"], "Operador Mezclado": op_mezclado,
                            "Supervisor": row["Supervisor"], "Auditor": row["Auditor"],
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
                            "Firma Operador": firma_op, "Firma Encargado": firma_enc
                        }
                        guardar_en_historial_local(datos_gs)
                        exito = guardar_en_google_sheets(datos_gs)
                        df_activas = df_activas[df_activas["ID"] != row["ID"]]
                        guardar_activas(df_activas)
                        msg = "✅ Agitación finalizada y registrada en Google Sheets." if exito \
                              else "✅ Agitación finalizada y guardada localmente."
                        st.success(msg)
                        st.rerun()

                with col_cancel:
                    # Botón de cancelar / error
                    st.markdown('<div class="btn-cancel">', unsafe_allow_html=True)
                    if st.button("Cancelar / Error", key=f"btn_open_cancel_{row['ID']}",
                                 use_container_width=True):
                        st.session_state[f"show_cancel_{row['ID']}"] = True
                    st.markdown('</div>', unsafe_allow_html=True)

                # ── Panel de cancelación ──────────────────────────────
                if st.session_state.get(f"show_cancel_{row['ID']}", False):
                    st.markdown("""
                    <div style="background:#1a0505; border:1px solid #6e1a1a; border-radius:8px;
                                padding:18px 22px; margin-top:12px;">
                        <div style="font-size:0.72rem; font-weight:600; text-transform:uppercase;
                                    letter-spacing:0.08em; color:#f85149; margin-bottom:12px;">
                            ⚠️  Registrar cancelación o error de proceso
                        </div>
                    """, unsafe_allow_html=True)

                    can_col1, can_col2 = st.columns(2)
                    with can_col1:
                        motivo_cancel = st.selectbox(
                            "Motivo de cancelación",
                            MOTIVOS_CANCELACION,
                            key=f"motivo_cancel_{row['ID']}"
                        )
                        cancelado_por = st.text_input(
                            "Cancelado por (nombre)",
                            key=f"cancel_by_{row['ID']}"
                        )
                    with can_col2:
                        obs_cancel = st.text_area(
                            "Detalle / observaciones del error",
                            key=f"obs_cancel_{row['ID']}",
                            placeholder="Describir el error o motivo de cancelación…",
                            height=100
                        )

                    ca1, ca2 = st.columns(2)
                    with ca1:
                        st.markdown('<div class="btn-cancel">', unsafe_allow_html=True)
                        if st.button("Confirmar cancelación y eliminar proceso",
                                     key=f"btn_confirm_cancel_{row['ID']}",
                                     use_container_width=True):
                            if not cancelado_por.strip():
                                st.error("Indica quién cancela el proceso.")
                            else:
                                fase = "En mezclado" if row["En_Mezclado"] else "En pesado/espera"
                                registro_error = {
                                    "ID Orden": row["ID"],
                                    "Fecha Cancelación": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "Motivo": motivo_cancel,
                                    "Observaciones Cancelación": obs_cancel if obs_cancel else "Sin detalle",
                                    "Cancelado Por": cancelado_por,
                                    "Departamento": row["Departamento"],
                                    "Lote / OF": row["Orden_Fabricacion_Lote"],
                                    "Código PS": row["Codigo_PS"],
                                    "Propela": row["Propela"],
                                    "Fase al Cancelar": fase,
                                    "Tiempo Transcurrido (min)": round(mins_trans, 1)
                                }
                                guardar_en_errores(registro_error)
                                df_activas = df_activas[df_activas["ID"] != row["ID"]]
                                guardar_activas(df_activas)
                                st.warning(f"Proceso O.F. {row['Orden_Fabricacion_Lote']} cancelado y registrado.")
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with ca2:
                        if st.button("Mantener proceso (cerrar)",
                                     key=f"btn_keep_{row['ID']}",
                                     use_container_width=True):
                            st.session_state[f"show_cancel_{row['ID']}"] = False
                            st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# VISTA 2 — ÁREA DE PESADO Y ESPERA
# ═══════════════════════════════════════════════════════════
elif menu == "Área de Pesado y Espera":
    st.markdown("# Área de Pesado y Espera de Materiales")
    st.markdown('<div class="page-caption">Órdenes de fabricación en preparación o pausadas antes de pasar a agitación</div>',
                unsafe_allow_html=True)

    df_activas   = cargar_activas()
    mapa_ocupados = obtener_mapa_cowles_ocupados(df_activas)
    df_espera    = df_activas[df_activas["En_Mezclado"] == False] if not df_activas.empty else pd.DataFrame()

    if df_espera.empty:
        st.markdown("""
        <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:40px;
                    text-align:center; color:#6e7681; margin-top:20px;">
            <div style="font-size:2rem; margin-bottom:8px;">📦</div>
            <div style="font-weight:600; color:#8b949e; margin-bottom:4px;">Sin órdenes en pesado</div>
            <div style="font-size:0.82rem;">Registra una nueva O.F. para comenzar.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chip chip-yellow" style="margin-bottom:16px;">{len(df_espera)} orden(es) en espera</div>',
                    unsafe_allow_html=True)

        for idx, row in df_espera.iterrows():
            header = (f"📦  O.F.: {row['Orden_Fabricacion_Lote']}  ·  "
                      f"Depto: {row['Departamento']}  ·  {row['Estatus_Pesado']}")

            with st.expander(header, expanded=True):
                # Info general
                st.markdown(f"""
                <div class="propela-card">
                    <div class="propela-card-title">{row['Orden_Fabricacion_Lote']}</div>
                    <div class="propela-card-sub">
                        Código PS: <strong style="color:#c9d1d9">{row['Codigo_PS']}</strong>
                        &nbsp;·&nbsp; Área: <strong style="color:#c9d1d9">{row['Area']}</strong>
                        &nbsp;·&nbsp; Tipo: <strong style="color:#c9d1d9">{row.get('Tipo_Producto','Tintas')}</strong>
                        &nbsp;·&nbsp; Tara Total: <strong style="color:#c9d1d9">{row['Tara_Total_Kg']} kg</strong>
                        &nbsp;·&nbsp; Tara O.F.: <strong style="color:#c9d1d9">{row['Tara_OF_Kg']} kg</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                op_row_html = f"""
                <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:12px;">
                    <div class="op-row" style="display:inline-flex;"><span class="op-icon">👷</span>
                        <div><div class="op-label">Op. Pesado</div><div class="op-value">{row['Operador']}</div></div></div>
                    <div class="op-row" style="display:inline-flex;"><span class="op-icon">🔧</span>
                        <div><div class="op-label">Op. Mezclado</div>
                        <div class="op-value">{row['Operador_Mezclado'] if row['Operador_Mezclado'] else row['Operador']}</div></div></div>
                    <div class="op-row" style="display:inline-flex;"><span class="op-icon">👔</span>
                        <div><div class="op-label">Supervisor</div><div class="op-value">{row['Supervisor']}</div></div></div>
                    <div class="op-row" style="display:inline-flex;"><span class="op-icon">📋</span>
                        <div><div class="op-label">Auditor</div><div class="op-value">{row['Auditor']}</div></div></div>
                </div>
                """
                st.markdown(op_row_html, unsafe_allow_html=True)

                # Controles
                cc1, cc2 = st.columns([2, 2])
                with cc1:
                    nuevo_estatus = st.selectbox(
                        "Estatus en pesado",
                        ESTADOS_PESADO,
                        index=ESTADOS_PESADO.index(row['Estatus_Pesado'])
                              if row['Estatus_Pesado'] in ESTADOS_PESADO else 0,
                        key=f"est_pes_{row['ID']}"
                    )
                with cc2:
                    opciones_fmt = []
                    idx_actual   = 0
                    for i, c in enumerate(LISTA_PROPELAS):
                        if c in mapa_ocupados:
                            opciones_fmt.append(f"OCUPADO — {c}  (O.F. {mapa_ocupados[c]})")
                        else:
                            opciones_fmt.append(f"Libre  —  {c}")
                        if c == row['Propela']:
                            idx_actual = i

                    label_sel  = st.selectbox("Asignar Cowles / Propela", opciones_fmt,
                                              index=idx_actual, key=f"prop_{row['ID']}")
                    propela_sel = LISTA_PROPELAS[opciones_fmt.index(label_sel)]

                if (nuevo_estatus != row['Estatus_Pesado']) or (propela_sel != row['Propela']):
                    df_activas.loc[df_activas["ID"] == row["ID"], "Estatus_Pesado"] = nuevo_estatus
                    df_activas.loc[df_activas["ID"] == row["ID"], "Propela"]        = propela_sel
                    guardar_activas(df_activas)
                    st.rerun()

                esta_ocupado = propela_sel in mapa_ocupados
                col_start, col_err = st.columns([3, 1])
                with col_start:
                    if esta_ocupado:
                        st.markdown(f"""
                        <div style="background:#3a0e0e; border:1px solid #6e1a1a; border-radius:6px;
                                    padding:10px 14px; font-size:0.85rem; color:#f85149; margin-top:6px;">
                            🛑 <strong>{propela_sel}</strong> está ocupada por otra O.F.
                            No se puede iniciar mezclado.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        if st.button(f"Iniciar mezclado en  {propela_sel}",
                                     key=f"btn_start_{row['ID']}",
                                     use_container_width=True, type="primary"):
                            df_activas["Hora_Inicio_Mezclado"] = df_activas["Hora_Inicio_Mezclado"].astype(object)
                            df_activas.loc[df_activas["ID"] == row["ID"], "En_Mezclado"]         = True
                            df_activas.loc[df_activas["ID"] == row["ID"], "Hora_Inicio_Mezclado"] = \
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            guardar_activas(df_activas)
                            st.rerun()

                with col_err:
                    st.markdown('<div class="btn-cancel">', unsafe_allow_html=True)
                    if st.button("Cancelar / Error", key=f"btn_open_cancel_pes_{row['ID']}",
                                 use_container_width=True):
                        st.session_state[f"show_cancel_pes_{row['ID']}"] = True
                    st.markdown('</div>', unsafe_allow_html=True)

                # Panel cancelación en pesado
                if st.session_state.get(f"show_cancel_pes_{row['ID']}", False):
                    st.markdown("""
                    <div style="background:#1a0505; border:1px solid #6e1a1a; border-radius:8px;
                                padding:18px 22px; margin-top:12px;">
                        <div style="font-size:0.72rem; font-weight:600; text-transform:uppercase;
                                    letter-spacing:0.08em; color:#f85149; margin-bottom:12px;">
                            ⚠️  Registrar cancelación o error de proceso
                        </div>
                    """, unsafe_allow_html=True)

                    pc1, pc2 = st.columns(2)
                    with pc1:
                        motivo_p  = st.selectbox("Motivo", MOTIVOS_CANCELACION, key=f"motivo_pes_{row['ID']}")
                        cancel_by = st.text_input("Cancelado por", key=f"cancel_by_pes_{row['ID']}")
                    with pc2:
                        obs_p = st.text_area("Detalle del error", key=f"obs_pes_{row['ID']}",
                                             placeholder="Describir el problema…", height=100)

                    pb1, pb2 = st.columns(2)
                    with pb1:
                        st.markdown('<div class="btn-cancel">', unsafe_allow_html=True)
                        if st.button("Confirmar cancelación y eliminar",
                                     key=f"confirm_cancel_pes_{row['ID']}",
                                     use_container_width=True):
                            if not cancel_by.strip():
                                st.error("Indica quién cancela el proceso.")
                            else:
                                reg_err = {
                                    "ID Orden": row["ID"],
                                    "Fecha Cancelación": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "Motivo": motivo_p,
                                    "Observaciones Cancelación": obs_p if obs_p else "Sin detalle",
                                    "Cancelado Por": cancel_by,
                                    "Departamento": row["Departamento"],
                                    "Lote / OF": row["Orden_Fabricacion_Lote"],
                                    "Código PS": row["Codigo_PS"],
                                    "Propela": row["Propela"],
                                    "Fase al Cancelar": "En pesado / espera",
                                    "Tiempo Transcurrido (min)": 0
                                }
                                guardar_en_errores(reg_err)
                                df_activas = df_activas[df_activas["ID"] != row["ID"]]
                                guardar_activas(df_activas)
                                st.warning(f"O.F. {row['Orden_Fabricacion_Lote']} cancelada y registrada.")
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with pb2:
                        if st.button("Mantener proceso", key=f"keep_pes_{row['ID']}",
                                     use_container_width=True):
                            st.session_state[f"show_cancel_pes_{row['ID']}"] = False
                            st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

                # Editar materiales
                with st.expander("Editar materiales y datos de la O.F.", expanded=False):
                    try:
                        mat_list = json.loads(row["Dificultades_Materiales_JSON"])
                    except:
                        mat_list = [{"CODIGO":"","KG EN OF":0.0,"KG AGREGADOS":0.0,"OBSERVACIONES":""}]
                    df_mat = pd.DataFrame(mat_list)
                    tabla_ed = st.data_editor(df_mat, num_rows="dynamic",
                                              use_container_width=True, key=f"editor_edit_{row['ID']}")
                    if st.button("Guardar cambios en O.F.", key=f"btn_save_edit_{row['ID']}"):
                        mat_json = json.dumps(tabla_ed.dropna(how="all").to_dict(orient="records"))
                        df_activas.loc[df_activas["ID"] == row["ID"], "Dificultades_Materiales_JSON"] = mat_json
                        guardar_activas(df_activas)
                        st.success("Cambios guardados.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════
# VISTA 3 — REGISTRAR NUEVA O.F.
# ═══════════════════════════════════════════════════════════
elif menu == "Registrar Nueva O.F.":
    st.markdown("# Registrar Nueva Orden de Fabricación")
    st.markdown('<div class="page-caption">Captura inicial del lote antes de pasar a pesado y agitación</div>',
                unsafe_allow_html=True)

    df_activas    = cargar_activas()
    mapa_ocupados = obtener_mapa_cowles_ocupados(df_activas)

    with st.form("form_registro_of"):
        # ── Sección 1: Identificación ──────────────────────
        st.markdown('<div class="card-section">', unsafe_allow_html=True)
        st.markdown('<div class="card-section-title">1 · Identificación y generales</div>', unsafe_allow_html=True)

        tipo_producto = st.radio(
            "Tipo de producto",
            ["Tintas (Estándar)", "Recubrimientos (Manual)"],
            horizontal=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        g1, g2, g3, g4 = st.columns(4)
        with g1:
            depto    = st.selectbox("Departamento", ["T1", "T2"])
            operador = st.text_input("Operador pesado")
        with g2:
            fecha_aud             = st.date_input("Fecha", datetime.now())
            operador_mezclado_init = st.text_input("Operador mezclado (dejar vacío si es el mismo)")
        with g3:
            codigo_ps  = st.text_input("Código PS")
            supervisor = st.text_input("Supervisor")
        with g4:
            lote    = st.text_input("Lote / O.F.")
            auditor = st.text_input("Auditor")

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Sección 2: Pesos, taras e inspección ──────────
        st.markdown('<div class="card-section">', unsafe_allow_html=True)
        st.markdown('<div class="card-section-title">2 · Pesos, taras e inspección inicial</div>', unsafe_allow_html=True)

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            tara_total = st.number_input("Tara total (kg)", min_value=0.0, value=250.0, step=10.0)
            tara_of    = st.number_input("Tara O.F. (kg)",  min_value=0.0, value=15.0,  step=0.5)
            area       = st.selectbox("Área", ["Manual Dispensing", "Automático"])
        with p2:
            limpieza_dispensing = st.selectbox("Limpieza dispensing", OPCIONES_LIMPIEZA)
            limpieza_propela    = st.selectbox("Limpieza propela",    OPCIONES_LIMPIEZA)
        with p3:
            chk_tara     = st.selectbox("Checklist tara",     OPCIONES_CHECKLIST)
            chk_limpieza = st.selectbox("Checklist limpieza", OPCIONES_CHECKLIST)
        with p4:
            opciones_fmt = [
                f"OCUPADO — {c}  (O.F. {mapa_ocupados[c]})" if c in mapa_ocupados else f"Libre  —  {c}"
                for c in LISTA_PROPELAS
            ]
            label_cowles   = st.selectbox("Cowles propuesto", opciones_fmt)
            propela_inicial = LISTA_PROPELAS[opciones_fmt.index(label_cowles)]
            estatus_pesado  = st.selectbox("Estatus en pesado", ESTADOS_PESADO)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Sección 3: Tiempos ────────────────────────────
        st.markdown('<div class="card-section">', unsafe_allow_html=True)
        st.markdown('<div class="card-section-title">3 · Parámetros de tiempo de agitación</div>', unsafe_allow_html=True)

        if tipo_producto == "Tintas (Estándar)":
            tiempo_target, rango_str, min_p, max_p = calcular_regla_tiempo(tara_total)
            st.markdown(f"""
            <div style="background:#0d2240; border:1px solid #1f6feb; border-radius:6px;
                        padding:12px 16px; font-size:0.88rem; color:#c9d1d9;">
                <strong style="color:#58a6ff;">Tiempo estándar calculado</strong>
                &nbsp;·&nbsp; Tara: <span class="data-chip">{tara_total} kg</span>
                &nbsp;→&nbsp; Rango: <span class="data-chip">{rango_str}</span>
                &nbsp;·&nbsp; Objetivo: <span class="data-chip">{tiempo_target} min</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#3a2d0e; border:1px solid #9e6a03; border-radius:6px;
                        padding:10px 14px; font-size:0.82rem; color:#d29922; margin-bottom:8px;">
                Recubrimientos: ingrese manualmente el tiempo requerido por la formulación.
            </div>
            """, unsafe_allow_html=True)
            tiempo_target = st.number_input("Tiempo de propela manual (min)", min_value=1.0, value=15.0, step=1.0)
            rango_str     = f"{tiempo_target} min (Manual Recubrimientos)"
            min_p, max_p  = tiempo_target, tiempo_target

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Sección 4: Materiales ─────────────────────────
        st.markdown('<div class="card-section">', unsafe_allow_html=True)
        st.markdown('<div class="card-section-title">4 · Materiales / fórmula de pesado</div>', unsafe_allow_html=True)

        df_mat_default   = pd.DataFrame([
            {"CODIGO":"","KG EN OF":0.0,"KG AGREGADOS":0.0,"OBSERVACIONES":""}
            for _ in range(3)
        ])
        tabla_materiales = st.data_editor(df_mat_default, num_rows="dynamic",
                                          use_container_width=True, key="editor_mat_pesado")
        st.markdown('</div>', unsafe_allow_html=True)

        btn_iniciar = st.form_submit_button("Guardar O.F. en área de pesado",
                                            use_container_width=True, type="primary")

    if btn_iniciar:
        if not lote or not operador or not auditor:
            st.error("Los campos O.F./Lote, Operador pesado y Auditor son obligatorios.")
        else:
            mat_json = json.dumps(tabla_materiales.dropna(how="all").to_dict(orient="records"))
            nuevo_id = int(datetime.now().timestamp())
            op_mez_f = operador_mezclado_init.strip() if operador_mezclado_init.strip() else operador

            nueva_fila = {
                "ID": nuevo_id, "Tipo_Producto": tipo_producto,
                "Departamento": depto, "Propela": propela_inicial,
                "Orden_Fabricacion_Lote": str(lote), "Codigo_PS": str(codigo_ps),
                "Area": area, "Tara_Total_Kg": tara_total, "Tara_OF_Kg": tara_of,
                "Operador": operador, "Operador_Mezclado": op_mez_f,
                "Supervisor": supervisor, "Auditor": auditor,
                "Limpieza_Dispensing": limpieza_dispensing,
                "Checklist_Tara": chk_tara, "Checklist_Limpieza": chk_limpieza,
                "Limpieza_Propela": limpieza_propela, "Estatus_Pesado": estatus_pesado,
                "En_Mezclado": False, "Dificultades_Materiales_JSON": mat_json,
                "Tiempo_Target_Min": tiempo_target, "Min_Permitido": min_p,
                "Max_Permitido": max_p, "Rango_Str": rango_str, "Hora_Inicio_Mezclado": ""
            }
            df_act = pd.concat([df_activas, pd.DataFrame([nueva_fila])], ignore_index=True)
            guardar_activas(df_act)
            st.success(f"O.F. {lote} registrada exitosamente en el área de pesado.")
            st.balloons()


# ═══════════════════════════════════════════════════════════
# VISTA 4 — HISTORIAL DE PROCESOS
# ═══════════════════════════════════════════════════════════
elif menu == "Historial de Procesos":
    st.markdown("# Historial de Procesos")
    st.markdown('<div class="page-caption">Registro completo de auditorías y lotes finalizados</div>',
                unsafe_allow_html=True)

    df_hist = cargar_historial()
    if df_hist.empty:
        st.markdown("""
        <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:40px;
                    text-align:center; color:#6e7681; margin-top:20px;">
            <div style="font-size:2rem; margin-bottom:8px;">📊</div>
            <div style="font-weight:600; color:#8b949e;">Sin registros en el historial</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            st.markdown(f'<div class="chip chip-blue">{len(df_hist)} proceso(s) registrados</div>',
                        unsafe_allow_html=True)
        with col_f2:
            csv_bytes = df_hist.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV",
                data=csv_bytes,
                file_name=f"historial_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_hist.drop(columns=["Adiciones / Materiales"]), use_container_width=True, height=320)

        st.markdown("""
        <div class="section-divider">
            <div class="divider-line"></div>
            <div class="divider-text">Desglose de materiales por lote</div>
            <div class="divider-line"></div>
        </div>
        """, unsafe_allow_html=True)

        lote_sel = st.selectbox("Seleccionar O.F. / Lote",
                                df_hist["Lote / OF"].unique().tolist())
        if lote_sel:
            fila      = df_hist[df_hist["Lote / OF"] == lote_sel].iloc[0]
            json_mats = fila["Adiciones / Materiales"]

            st.markdown(f"""
            <div style="background:#161b22; border:1px solid #30363d; border-radius:6px;
                        padding:12px 16px; font-size:0.83rem; color:#8b949e; margin-bottom:12px;">
                Código PS: <span class="data-chip">{fila['Código PS']}</span>
                &nbsp;·&nbsp; Área: <span class="data-chip">{fila['Área']}</span>
                &nbsp;·&nbsp; Fecha fin: <span class="data-chip">{fila['Fecha Fin']}</span>
                &nbsp;·&nbsp; Estatus: <span class="data-chip">{fila['Estatus Auditoría']}</span>
            </div>
            """, unsafe_allow_html=True)

            try:
                lista_mats = json.loads(json_mats)
            except:
                lista_mats = []

            if lista_mats:
                df_m = pd.DataFrame(lista_mats)
                df_m.columns = [str(c).upper().strip() for c in df_m.columns]
                for col_r in ["CODIGO","KG EN OF","KG AGREGADOS","OBSERVACIONES"]:
                    if col_r not in df_m.columns:
                        df_m[col_r] = ""
                df_m["KG EN OF"]     = pd.to_numeric(df_m["KG EN OF"],     errors="coerce").fillna(0.0)
                df_m["KG AGREGADOS"] = pd.to_numeric(df_m["KG AGREGADOS"], errors="coerce").fillna(0.0)
                df_m["DIFERENCIA (kg)"] = df_m["KG AGREGADOS"] - df_m["KG EN OF"]
                df_m["ESTATUS"] = df_m.apply(
                    lambda r: "INCIDENCIA" if (abs(r["DIFERENCIA (kg)"]) > 0.01
                              or (str(r["OBSERVACIONES"]).strip() not in ("","nan")))
                              else "Conforme", axis=1
                )
                solo_inc = st.checkbox("Mostrar solo materiales con incidencias", value=False)
                df_show  = df_m[df_m["ESTATUS"] == "INCIDENCIA"] if solo_inc else df_m
                if df_show.empty and solo_inc:
                    st.success("Este lote no registra diferencias de peso ni incidencias.")
                else:
                    st.dataframe(df_show[["CODIGO","KG EN OF","KG AGREGADOS",
                                          "DIFERENCIA (kg)","ESTATUS","OBSERVACIONES"]],
                                 use_container_width=True)
            else:
                st.info("No hay detalle de materiales para esta O.F.")


# ═══════════════════════════════════════════════════════════
# VISTA 5 — PROCESOS CANCELADOS / ERRORES
# ═══════════════════════════════════════════════════════════
elif menu == "Procesos Cancelados":
    st.markdown("# Registro de Cancelaciones y Errores")
    st.markdown('<div class="page-caption">Trazabilidad de procesos eliminados o cancelados con su motivo</div>',
                unsafe_allow_html=True)

    df_err = cargar_errores()
    if df_err.empty:
        st.markdown("""
        <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:40px;
                    text-align:center; color:#6e7681; margin-top:20px;">
            <div style="font-size:2rem; margin-bottom:8px;">✅</div>
            <div style="font-weight:600; color:#8b949e;">Sin cancelaciones registradas</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_e1, col_e2 = st.columns([3, 1])
        with col_e1:
            st.markdown(f'<div class="chip chip-red">{len(df_err)} cancelación(es) registrada(s)</div>',
                        unsafe_allow_html=True)
        with col_e2:
            csv_e = df_err.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV",
                data=csv_e,
                file_name=f"cancelaciones_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_err, use_container_width=True, height=380)
