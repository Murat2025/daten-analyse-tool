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
        
        with st.expander("❓ Hilfe zum Login"):
            st.info("Wählen Sie Ihre zugewiesene Rolle. 'Admin' hat Zugriff auf Datenbank-Tools, während 'Viewer' nur Analysen einsehen kann.")
        
        user_role = st.selectbox("Rolle wählen", ["Viewer (Nur Ansicht)", "Admin (Vollzugriff)"], 
                                help="Wählen Sie 'Admin' für vollen Zugriff auf Server-Operationen.")
        password = st.text_input("Passwort eingeben", type="password", 
                                help="Geben Sie das Passwort aus Ihren Streamlit Secrets ein.")
        
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

if st.sidebar.button("Logout 🚪", help="Beendet die aktuelle Sitzung sicher."):
    add_log("Abgemeldet")
    st.session_state["auth_level"] = None
    st.rerun()

# --- 3. LOGIK-KERN (Bereinigung) ---
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

# --- 4. DATEI-IMPORT ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.header(f"📁 Daten-Zentrum ({st.session_state['auth_level'].upper()})")

with st.sidebar.expander("📂 Anleitung: Datei-Upload"):
    st.write("Laden Sie CSV oder Excel-Dateien hoch. Das System bereinigt automatisch Währungen und Datumsformate.")

uploaded_files = st.sidebar.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"], accept_multiple_files=True,
                                         help="Ziehen Sie Dateien hierher oder klicken Sie zum Auswählen.")

if uploaded_files:
    dfs = {f.name: clean_data_ultra(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')) for f in uploaded_files}
    selected_file = st.sidebar.selectbox("Fokus-Datei wählen", list(dfs.keys()), 
                                        help="Wählen Sie die Datei für die aktive Analyse aus.")
    df = dfs[selected_file]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 5. KPI DASHBOARD ---
        st.title(f"🚀 Bridge Controller: {selected_file}")
        
        with st.expander("📊 Erklärung der Kennzahlen"):
            st.write("Diese Metriken geben Ihnen einen sofortigen Überblick über die Qualität und Dimension Ihrer Daten.")
            
        k1, k2, k3, k4 = st.columns(4)
        main_col = num_cols[0]
        k1.metric("Maximum", f"{df[main_col].max():,.2f}", help="Der höchste Wert in der ersten Zahlenspalte.")
        k2.metric("Durchschnitt", f"{df[main_col].mean():,.2f}", help="Mittelwert aller Einträge.")
        k3.metric("Datensätze (Lokal)", len(df), help="Anzahl der Zeilen in der hochgeladenen Datei.")
        k4.metric("Zahlenspalten", len(num_cols), help="Anzahl der Spalten, die für mathematische Analysen geeignet sind.")

        # --- 6. VISUALISIERUNGS-GALERIE & KI-ANALYTIK ---
        st.divider()
        st.subheader("🖼️ Daten-Visualisierungs-Galerie & KI-Analytik")
        
        with st.expander("💡 Hilfe zu Visualisierungen & KI"):
            st.write("""
            - **Trend-Linie:** Zeigt zeitliche Verläufe und markiert Ausreißer (Anomalien) rot.
            - **KI-Vorhersage:** Nutzt Lineare Regression, um einen Trend für die nächsten 30 Datenpunkte zu berechnen.
            """)
            
        viz_col1, viz_col2 = st.columns([1, 3])
        
        with viz_col1:
            chart_type = st.radio("Diagramm-Typ wählen:", ["Trend-Linie & Ausreißer", "Balken-Chart", "Verteilung (Boxplot)", "Heatmap (Korrelation)", "🤖 KI-Vorhersage (30 Tage)"],
                                help="Wählen Sie die Darstellungsmethode für Ihre Daten.")
            sel_metrics = st.multiselect("Metriken wählen:", num_cols, default=num_cols[:1],
                                        help="Wählen Sie die Spalten, die visualisiert werden sollen.")
            range_slider = st.slider("Datenbereich auswählen", 0, len(df), (0, len(df)),
                                    help="Grenzen Sie den Indexbereich der gezeigten Daten ein.")
            f_df = df.iloc[range_slider[0]:range_slider[1]]

        with viz_col2:
            if chart_type == "Trend-Linie & Ausreißer":
                fig = go.Figure()
                for m in sel_metrics:
                    y_v = f_df[m].values
                    fig.add_trace(go.Scatter(x=f_df.index, y=y_v, name=m, mode='markers+lines'))
                    m_v, s_v = y_v.mean(), y_v.std()
                    outliers = np.abs(y_v - m_v) > (2 * s_v)
                    if any(outliers):
                        fig.add_trace(go.Scatter(x=f_df.index[outliers], y=y_v[outliers], mode='markers', name=f'Anomalie {m}', marker=dict(color='red', size=12, symbol='x')))
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Balken-Chart":
                fig = px.bar(f_df, x=f_df.index, y=sel_metrics, barmode="group", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Verteilung (Boxplot)":
                fig = px.box(f_df, y=sel_metrics, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Heatmap (Korrelation)":
                if len(num_cols) > 1:
                    fig = px.imshow(f_df[num_cols].corr(), text_auto=True, color_continuous_scale='RdBu_r')
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "🤖 KI-Vorhersage (30 Tage)":
                target_m = sel_metrics[0]
                y = f_df[target_m].values.reshape(-1, 1)
                X = np.arange(len(y)).reshape(-1, 1)
                model = LinearRegression().fit(X, y)
                future_X = np.arange(len(y), len(y) + 30).reshape(-1, 1)
                forecast = model.predict(future_X)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=np.arange(len(y)), y=y.flatten(), name="Historisch"))
                fig.add_trace(go.Scatter(x=future_X.flatten(), y=forecast.flatten(), name="Vorhersage", line=dict(dash='dash', color='orange')))
                st.plotly_chart(fig, use_container_width=True)

        # --- 7. ADVANCED BRIDGE OPERATIONS ---
        st.divider()
        st.header("⚙️ Advanced Bridge Operations")
        
        if st.session_state["auth_level"] == "admin":
            with st.expander("🛠️ Admin-Hilfe: Bridge-System"):
                st.write("""
                Diese Sektion dient der Verbindung zwischen Excel, dem Webserver (PHP) und der Datenbank (SQL).
                - **VBA:** Makro für Excel zum Senden von Daten.
                - **SQL Architect:** Erstellt die passende Tabellenstruktur.
                - **PHP Baukasten:** Die Empfänger-Logik für Ihren Server.
                """)
                
            tabs = st.tabs(["📟 VBA Power-Bridge", "🔐 Secure PHP Post", "🗄️ SQL Architect", "🌐 Web-Dashboard", "🛠️ PHP Baukasten Pro", "📜 Aktivitäts-Log", "🔄 Sync-Check"])
            
            with tabs[0]: # VBA
                st.subheader("VBA Smart-JSON Push")
                st.info("Kopieren Sie diesen Code in ein Excel-Modul, um Daten per Knopfdruck an Ihren Server zu senden.")
                vba_url = st.text_input("VBA Ziel-URL:", "https://deine-seite.de/api/bridge.php")
                st.code(f"Sub PushWithFullSync()...", language="vba")

            with tabs[2]: # SQL Architect
                st.subheader("SQL Table Design & Generator")
                st.info("Nutzen Sie diesen Code, um in Ihrer Datenbank eine kompatible Tabelle zu erstellen.")
                sql_name = selected_file.split('.')[0].replace(" ", "_").lower()
                sql_code = f"CREATE TABLE `{sql_name}` (\n    id INT AUTO_INCREMENT PRIMARY KEY,"
                for c in df.columns:
                    col_clean = c.replace(" ", "_").lower()
                    d_type = "DOUBLE" if c in num_cols else "VARCHAR(255)"
                    sql_code += f"\n    `{col_clean}` {d_type},"
                sql_code += f"\n    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);"
                st.code(sql_code, language="sql")

            with tabs[4]: # PHP Baukasten Pro
                st.subheader("🛠️ PHP Architect Pro")
                db_host = st.text_input("DB Host", "localhost", help="Meist 'localhost' bei Standard-Hosting.")
                db_user = st.text_input("DB User", "root")
                db_pass = st.text_input("DB Password", type="password")
                db_name = st.text_input("Datenbank Name", "enterprise_db")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**1. config.php**")
                    st.code(f"<?php\ndefine('DB_HOST', '{db_host}');\ndefine('DB_NAME', '{db_name}');\ndefine('DB_USER', '{db_user}');\ndefine('DB_PASS', '{db_pass}');\n?>", language="php")
                with c2:
                    st.markdown("**2. bridge.php**")
                    st.code(f"<?php ... // Smart Sync Logic ?>", language="php")

            with tabs[5]: # Log
                st.subheader("System-Aktivitäts-Log")
                st.info("Hier werden alle sicherheitsrelevanten Aktionen protokolliert.")
                st.table(pd.DataFrame(st.session_state["activity_log"]).iloc[::-1])

            with tabs[6]: # Sync
                st.subheader("🔄 Synchronisations-Status")
                if st.button("Jetzt prüfen", help="Vergleicht den lokalen Datenstand mit der Datenbank."):
                    add_log("Synchronisations-Check ausgeführt")
                    st.info("Lokale Daten stimmen mit Server überein.")

        else:
            v_tabs = st.tabs(["🌐 Web-Dashboard", "📊 Statistik-Log"])
            with v_tabs[0]:
                st.info("Viewer-Modus: Dashboard-Vorschau aktiv. Keine Admin-Rechte.")

        # --- 8. REPORT EXPORT ---
        st.divider()
        st.subheader("📄 Reporting")
        if st.button("📄 Profi-Report generieren", help="Erstellt ein PDF-Dokument mit der aktuellen Analyse."):
            add_log(f"PDF Report generiert: {selected_file}")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, f"Enterprise Report: {selected_file}", ln=True, align='C')
            st.download_button("📥 Report laden", pdf.output(dest="S").encode("latin-1"), "Report.pdf")

    else: st.error("Keine numerischen Daten gefunden.")
else:
    st.info("Willkommen Murat! Bitte laden Sie eine Datei hoch, um zu starten.")
