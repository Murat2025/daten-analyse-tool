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

# --- 2. USER MANAGEMENT & LOGGING SYSTEM ---
if "activity_log" not in st.session_state:
    st.session_state["activity_log"] = []

def add_log(action):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    role = st.session_state.get("auth_level", "Unknown")
    st.session_state["activity_log"].append({
        "Zeitpunkt": now,
        "Rolle": role,
        "Aktion": action
    })

def login_system():
    if "auth_level" not in st.session_state:
        st.session_state["auth_level"] = None

    if st.session_state["auth_level"] is None:
        st.title("🔐 Enterprise Login")
        
        # HILFE-EXPANDER: LOGIN
        with st.expander("❓ Hilfe zum Login-System"):
            st.info("Wählen Sie Ihre Rolle aus. Admins haben Zugriff auf die Bridge-Konfiguration und SQL-Tools. Viewer können nur Daten einsehen und analysieren.")
        
        user_role = st.selectbox("Rolle wählen", ["Viewer (Nur Ansicht)", "Admin (Vollzugriff)"], 
                                help="Wählen Sie Admin für Vollzugriff auf Datenbank-Skripte.")
        password = st.text_input("Passwort eingeben", type="password", 
                                help="Das Passwort wird in den App-Secrets verwaltet.")
        
        if st.button("Anmelden"):
            try:
                if user_role == "Admin (Vollzugriff)" and password == st.secrets["admin_password"]:
                    st.session_state["auth_level"] = "admin"
                    add_log("Erfolgreicher Login als Admin")
                    st.rerun()
                elif user_role == "Viewer (Nur Ansicht)" and password == st.secrets["viewer_password"]:
                    st.session_state["auth_level"] = "viewer"
                    add_log("Erfolgreicher Login als Viewer")
                    st.rerun()
                else:
                    st.error("Ungültiges Passwort für diese Rolle.")
            except KeyError:
                st.error("Secrets (admin_password / viewer_password) nicht konfiguriert.")
        return False
    return True

if not login_system():
    st.stop()

# --- 3. DATEN-GENERATOR ---
def generate_demo_data():
    dates = pd.date_range(start="2025-10-01", periods=110)
    base_sales = np.linspace(1000, 2500, 110)
    noise = np.random.normal(0, 50, 110)
    sales = base_sales + noise
    sales[15], sales[45], sales[80] = 5000, 5200, 150 # Künstliche Ausreißer
    df_demo = pd.DataFrame({
        'Datum': dates,
        'Umsatz': np.round(sales, 2),
        'Menge': np.round(sales / 25).astype(int),
        'Kosten': np.round(sales * 0.6, 2),
        'Status': 'aktiv'
    })
    df_demo.loc[10, 'Status'] = 'löschen'
    return df_demo

# --- 4. LOGIK-KERN (Bereinigung) ---
def clean_data_ultra(df):
    df = df.dropna(how='all').dropna(axis=1, how='all')
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                temp_col = df[col].astype(str).str.replace(r'[€$%kg\s]', '', regex=True).str.replace(',', '.')
                df[col] = pd.to_numeric(temp_col)
            except: pass
        if 'datum' in col.lower() or 'date' in col.lower():
            try: df[col] = pd.to_datetime(df[col])
            except: pass
    return df

# --- 5. SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.header(f"📁 Daten-Zentrum ({st.session_state['auth_level'].upper()})")

# HILFE-EXPANDER: SIDEBAR
with st.sidebar.expander("📂 Hilfe: Datei-Management"):
    st.write("Laden Sie eigene CSV/XLSX Dateien hoch oder nutzen Sie den Testdaten-Button, um die KI-Funktionen sofort auszuprobieren.")

# Testdaten Button mit Tooltip
if st.sidebar.button("🧪 Testdaten generieren", help="Erstellt 110 synthetische Datensätze inkl. Anomalien für Demo-Zwecke."):
    st.session_state["demo_df"] = generate_demo_data()
    add_log("Demo-Daten generiert")
    st.sidebar.success("Testdaten geladen!")

uploaded_files = st.sidebar.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"], accept_multiple_files=True)

# Datenquelle bestimmen
dfs = {}
if uploaded_files:
    for f in uploaded_files:
        dfs[f.name] = clean_data_ultra(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f))
elif "demo_df" in st.session_state:
    dfs["Murat_Testdaten.xlsx"] = st.session_state["demo_df"]

if dfs:
    selected_file = st.sidebar.selectbox("Fokus-Datei wählen", list(dfs.keys()), help="Wählen Sie die Datei für die aktive Analyse.")
    df = dfs[selected_file]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 6. KPI DASHBOARD ---
        st.title(f"🚀 Bridge Controller: {selected_file}")
        
        # HILFE-EXPANDER: DASHBOARD
        with st.expander("📊 Hilfe: Dashboard Kennzahlen"):
            st.write("Diese Kennzahlen geben einen schnellen Überblick über die statistische Verteilung der ersten numerischen Spalte.")

        k1, k2, k3, k4 = st.columns(4)
        main_col = num_cols[0]
        k1.metric("Maximum", f"{df[main_col].max():,.2f}", help="Höchster Einzelwert im Datensatz.")
        k2.metric("Durchschnitt", f"{df[main_col].mean():,.2f}", help="Arithmetisches Mittel aller Werte.")
        k3.metric("Datensätze", len(df), help="Gesamtanzahl der Zeilen in der Datei.")
        k4.metric("Zahlenspalten", len(num_cols), help="Anzahl der verwertbaren Datenspaltentypen.")

        # --- 7. VISUALISIERUNG & KI ---
        st.divider()
        st.subheader("🖼️ Visualisierung & KI-Analytik")
        
        # HILFE-EXPANDER: VIZ & KI
        with st.expander("🤖 Hilfe: Anomalien & Prognosen"):
            st.markdown("""
            **Trend-Linie:** Markiert Werte, die mehr als 2 Standardabweichungen vom Mittelwert abweichen, mit einem roten 'X'.
            **KI-Vorhersage:** Nutzt eine Lineare Regression, um basierend auf historischen Daten die nächsten 30 Punkte zu berechnen.
            """)

        viz_col1, viz_col2 = st.columns([1, 3])
        with viz_col1:
            chart_type = st.radio("Analyse-Modus wählen:", ["Trend-Linie & Ausreißer", "Balken-Chart", "🤖 KI-Vorhersage (30 Tage)"], 
                                help="Wählen Sie zwischen klassischer Analyse oder KI-gestützter Prognose.")
            sel_metrics = st.multiselect("Metriken wählen:", num_cols, default=num_cols[:1], 
                                        help="Wählen Sie die Datenreihen aus, die im Diagramm erscheinen sollen.")
            f_df = df

        with viz_col2:
            if "Trend" in chart_type:
                fig = go.Figure()
                for m in sel_metrics:
                    y_v = f_df[m].values
                    fig.add_trace(go.Scatter(x=f_df.index, y=y_v, name=m, mode='markers+lines'))
                    # Ausreißer-Logik (Standardabweichung)
                    m_v, s_v = y_v.mean(), y_v.std()
                    outliers = np.abs(y_v - m_v) > (2 * s_v)
                    if any(outliers):
                        fig.add_trace(go.Scatter(x=f_df.index[outliers], y=y_v[outliers], mode='markers', name=f'Anomalie {m}', 
                                               marker=dict(color='red', size=12, symbol='x')))
                st.plotly_chart(fig, use_container_width=True)
            
            elif "KI" in chart_type:
                target_m = sel_metrics[0]
                y = f_df[target_m].values.reshape(-1, 1)
                X = np.arange(len(y)).reshape(-1, 1)
                model = LinearRegression().fit(X, y)
                future_X = np.arange(len(y), len(y) + 30).reshape(-1, 1)
                forecast = model.predict(future_X)
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=y.flatten(), name="Historische Daten"))
                fig.add_trace(go.Scatter(x=np.arange(len(y), len(y)+30), y=forecast.flatten(), name="Vorhersage (30T)", line=dict(dash='dash', color='orange')))
                st.plotly_chart(fig, use_container_width=True)

        # --- 8. ADMIN OPERATIONS ---
        if st.session_state["auth_level"] == "admin":
            st.divider()
            st.header("⚙️ Advanced Bridge Operations")
            
            # HILFE-EXPANDER: BRIDGE
            with st.expander("📟 Hilfe: Excel & PHP Integration"):
                st.write("Verwenden Sie diese Codes, um eine dauerhafte Verbindung zwischen Ihren Excel-Arbeitsmappen und Ihrer Web-Datenbank herzustellen.")
            
            tabs = st.tabs(["📟 VBA Bridge", "🗄️ SQL Architect", "🛠️ PHP Baukasten"])
            
            with tabs[0]:
                st.subheader("VBA Sync-Code")
                st.info("Kopieren Sie diesen Code in Excel (Alt+F11), um Daten per Knopfdruck an den Server zu senden.")
                vba_url = st.text_input("VBA Ziel-URL:", "https://deine-seite.de/api/bridge.php", help="Die Adresse, unter der Ihr bridge.php Skript erreichbar ist.")
                st.code(f"Sub PushWithFullSync()...", language="vba")
            
            with tabs[1]:
                st.subheader("SQL Struktur")
                st.info("Diesen Code in phpMyAdmin ausführen, um die Tabelle anzulegen.")
                sql_name = selected_file.split('.')[0].replace(" ", "_").lower()
                st.code(f"CREATE TABLE `{sql_name}` (...);", language="sql", help="Generiertes Schema basierend auf der aktuellen Datei.")

    if st.sidebar.button("🚪 Abmelden", help="Sitzung beenden und zurück zum Login."):
        st.session_state["auth_level"] = None
        st.rerun()

else:
    st.info("Willkommen Murat! Laden Sie eine Datei hoch oder nutzen Sie 'Testdaten generieren' in der Sidebar.")
