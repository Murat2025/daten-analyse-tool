import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from fpdf import FPDF
import io
import datetime
from sklearn.linear_model import LinearRegression

# --- 1. SETUP & ENTERPRISE DESIGN ---
st.set_page_config(page_title="DataPro AI | Ultimate Bridge Suite", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #e1e4e8; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #f0f2f6; 
        border-radius: 5px; 
        padding: 10px; 
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. USER MANAGEMENT & LOGGING ---
if "activity_log" not in st.session_state:
    st.session_state["activity_log"] = []

def add_log(action):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    role = st.session_state.get("auth_level", "Unknown")
    st.session_state["activity_log"].append({"Zeitpunkt": now, "Rolle": role, "Aktion": action})

def login_system():
    if "auth_level" not in st.session_state:
        st.session_state["auth_level"] = None
    if st.session_state["auth_level"] is None:
        st.title("🔐 Enterprise Login")
        with st.expander("❓ Hilfe zum Login"):
            st.info("Admins sehen die Bridge-Tools, Viewer nur die Analyse.")
        user_role = st.selectbox("Rolle wählen", ["Viewer (Nur Ansicht)", "Admin (Vollzugriff)"])
        password = st.text_input("Passwort eingeben", type="password")
        if st.button("Anmelden"):
            try:
                if user_role == "Admin (Vollzugriff)" and password == st.secrets["admin_password"]:
                    st.session_state["auth_level"] = "admin"
                    st.rerun()
                elif user_role == "Viewer (Nur Ansicht)" and password == st.secrets["viewer_password"]:
                    st.session_state["auth_level"] = "viewer"
                    st.rerun()
                else: st.error("Falsches Passwort.")
            except: st.error("Secrets nicht konfiguriert.")
        return False
    return True

if not login_system():
    st.stop()

# --- 3. TESTDATEN-GENERATOR ---
def generate_demo_data():
    dates = pd.date_range(start="2025-10-01", periods=110)
    base_sales = np.linspace(1000, 2500, 110)
    sales = base_sales + np.random.normal(0, 50, 110)
    sales[15], sales[45], sales[80] = 5000, 5200, 150 
    df_demo = pd.DataFrame({
        'Datum': dates, 'Umsatz': np.round(sales, 2),
        'Menge': np.round(sales / 25).astype(int),
        'Kosten': np.round(sales * 0.6, 2), 'Status': 'aktiv'
    })
    df_demo.loc[10, 'Status'] = 'löschen'
    return df_demo

# --- 4. DATA CLEANING ---
def clean_data_ultra(df):
    df = df.dropna(how='all').dropna(axis=1, how='all')
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                temp = df[col].astype(str).str.replace(r'[€$%kg\s]', '', regex=True).str.replace(',', '.')
                df[col] = pd.to_numeric(temp)
            except: pass
        if 'datum' in col.lower() or 'date' in col.lower():
            try: df[col] = pd.to_datetime(df[col])
            except: pass
    return df

# --- 5. SIDEBAR & IMPORT ---
st.sidebar.header(f"📁 Daten ({st.session_state['auth_level'].upper()})")
if st.sidebar.button("🧪 Testdaten generieren"):
    st.session_state["demo_df"] = generate_demo_data()
    st.sidebar.success("Testdaten geladen!")

uploaded_files = st.sidebar.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"], accept_multiple_files=True)

dfs = {}
if uploaded_files:
    for f in uploaded_files:
        dfs[f.name] = clean_data_ultra(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f))
elif "demo_df" in st.session_state:
    dfs["Murat_Testdaten.xlsx"] = st.session_state["demo_df"]

if dfs:
    selected_file = st.sidebar.selectbox("Fokus-Datei", list(dfs.keys()))
    df = dfs[selected_file]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        st.title(f"🚀 Bridge Controller: {selected_file}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Maximum", f"{df[num_cols[0]].max():,.2f}", help="Höchster Wert")
        k2.metric("Durchschnitt", f"{df[num_cols[0]].mean():,.2f}")
        k3.metric("Datensätze", len(df))
        k4.metric("Zahlenspalten", len(num_cols))

        # --- VISUALISIERUNG & KI ---
        st.divider()
        viz_col1, viz_col2 = st.columns([1, 3])
        with viz_col1:
            chart_type = st.radio("Analyse:", ["Trend", "🤖 KI-Vorhersage"], help="Trend zeigt Anomalien, KI zeigt Prognose.")
            sel_metrics = st.multiselect("Metriken:", num_cols, default=num_cols[:1])
        
        with viz_col2:
            if "Trend" in chart_type:
                fig = go.Figure()
                for m in sel_metrics:
                    y_v = df[m].values
                    fig.add_trace(go.Scatter(y=y_v, name=m, mode='markers+lines'))
                    m_v, s_v = y_v.mean(), y_v.std()
                    outliers = np.abs(y_v - m_v) > (2 * s_v)
                    if any(outliers):
                        fig.add_trace(go.Scatter(x=df.index[outliers], y=y_v[outliers], mode='markers', name=f'Anomalie {m}', marker=dict(color='red', size=12, symbol='x')))
                st.plotly_chart(fig, use_container_width=True)
            elif "KI" in chart_type:
                target = sel_metrics[0]
                y = df[target].values.reshape(-1, 1)
                X = np.arange(len(y)).reshape(-1, 1)
                model = LinearRegression().fit(X, y)
                pred = model.predict(np.arange(len(y), len(y)+30).reshape(-1, 1))
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=y.flatten(), name="Historisch"))
                fig.add_trace(go.Scatter(x=np.arange(len(y), len(y)+30), y=pred.flatten(), name="30T Prognose", line=dict(dash='dash', color='orange')))
                st.plotly_chart(fig, use_container_width=True)

        # --- ADVANCED BRIDGE OPERATIONS (ALLE FUNKTIONEN!) ---
        if st.session_state["auth_level"] == "admin":
            st.divider()
            st.header("⚙️ Advanced Bridge Operations")
            with st.expander("📟 Hilfe: Excel & PHP Integration"):
                st.info("Hier konfigurieren Sie die automatische Verbindung zwischen Excel und Ihrer Datenbank.")
            
            tabs = st.tabs(["📟 VBA Bridge", "🗄️ SQL Architect", "🛠️ PHP Baukasten Pro", "📜 Aktivitäts-Log"])
            
            with tabs[0]: # VBA
                st.subheader("VBA Sync-Code")
                vba_url = st.text_input("VBA Ziel-URL:", "https://deine-seite.de/api/bridge.php")
                st.code(f"""' VBA Code für Excel (Alt+F11)
Sub PushWithFullSync()
    Dim http As Object, url As String, payload As String
    ' ... Logik zum Senden der Tabelle als JSON ...
End Sub""", language="vba")
            
            with tabs[1]: # SQL
                st.subheader("SQL Table Design")
                sql_name = selected_file.split('.')[0].replace(" ", "_").lower()
                sql_code = f"CREATE TABLE `{sql_name}` (\n    id INT AUTO_INCREMENT PRIMARY KEY,"
                for c in df.columns:
                    col_clean = c.replace(" ", "_").lower()
                    sql_code += f"\n    `{col_clean}` VARCHAR(255),"
                sql_code += "\n    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);"
                st.code(sql_code, language="sql")
                
            with tabs[2]: # PHP
                st.subheader("PHP Sync Engine (Backup & Upsert)")
                st.code(f"""<?php
// PHP BRIDGE MIT AUTO-BACKUP & UPDATE LOGIK
require_once 'config.php';
// ... PDO Connection ...
// ... Backup Logik ...
// ... Insert/Update Logik ...
?>""", language="php")

            with tabs[3]: # Logs
                st.subheader("System-Logs")
                st.table(pd.DataFrame(st.session_state["activity_log"]).iloc[::-1])

    if st.sidebar.button("🚪 Abmelden"):
        st.session_state["auth_level"] = None
        st.rerun()
else:
    st.info("Willkommen Murat! Nutze die Sidebar zum Starten.")
