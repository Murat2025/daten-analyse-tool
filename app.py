import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from fpdf import FPDF
import io

# --- 1. SETUP & CUSTOM DESIGN (Enterprise Look) ---
st.set_page_config(page_title="DataPro AI | Enterprise Suite", page_icon="💎", layout="wide")

# Custom CSS für professionelles Dashboard-Design
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
    }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("🔑 Master-Passwort", type="password", 
                      on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), 
                      key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. ERWEITERTE DATEN-LOGIK (Ultra-Bereinigung) ---
def clean_data_ultra(df):
    # Entfernt leere Zeilen/Spalten
    df = df.dropna(how='all').dropna(axis=1, how='all')
    for col in df.columns:
        # Bereinigung von Währungen (€, $) und Einheiten (kg, %)
        if df[col].dtype == 'object':
            try:
                temp_col = df[col].astype(str).str.replace(r'[€$%kg\s]', '', regex=True).str.replace(',', '.')
                df[col] = pd.to_numeric(temp_col)
            except: pass
        # Datumskonvertierung
        if 'datum' in col.lower() or 'date' in col.lower():
            try: df[col] = pd.to_datetime(df[col])
            except: pass
    return df

# --- 3. DATEI-IMPORT (Multi-Format Support) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.header("📁 Daten-Zentrum")
uploaded_files = st.sidebar.file_uploader("CSV oder Excel hochladen", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    # Lade alle Dateien
    dfs = {f.name: clean_data_ultra(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)) for f in uploaded_files}
    selected_file = st.sidebar.selectbox("Fokus-Datei wählen", list(dfs.keys()))
    df = dfs[selected_file]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 4. KPI DASHBOARD ---
        st.title(f"💎 Intelligence Dashboard: {selected_file}")
        k1, k2, k3, k4 = st.columns(4)
        main_col = num_cols[0]
        
        k1.metric("Maximum", f"{df[main_col].max():,.2f}")
        k2.metric("Minimum", f"{df[main_col].min():,.2f}")
        k3.metric("Ø-Durchschnitt", f"{df[main_col].mean():,.2f}")
        k4.metric("Datensätze", len(df))

        # --- 5. INTERAKTIVE ANALYSE & AUSREISSER ---
        st.divider()
        st.sidebar.divider()
        range_slider = st.sidebar.slider("Datenbereich (Zeilen)", 0, len(df), (0, len(df)))
        f_df = df.iloc[range_slider[0]:range_slider[1]]
        
        st.subheader("📊 Visualisierter Trend & Outlier-Erkennung")
        selected_metrics = st.multiselect("Metriken vergleichen:", num_cols, default=num_cols[:1])
        
        fig = go.Figure()
        for m in selected_metrics:
            y_vals = f_df[m].values
            fig.add_trace(go.Scatter(x=f_df.index, y=y_vals, name=m, mode='lines+markers'))
            
            # Ausreißer-Logik (Standardabweichung > 2) markieren
            mean_v, std_v = y_vals.mean(), y_vals.std()
            outlier_mask = np.abs(y_vals - mean_v) > (2 * std_v)
            if any(outlier_mask):
                fig.add_trace(go.Scatter(
                    x=f_df.index[outlier_mask], y=y_vals[outlier_mask],
                    mode='markers', name=f'Ausreißer {m}',
                    marker=dict(color='red', size=12, symbol='x')
                ))
        
        fig.update_layout(hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- 6. SMART QUERY ULTRA ---
        st.subheader("💬 Smart Query")
        user_query = st.text_input("Stelle eine Frage zu deinen Daten:")
        ki_out = ""
        if user_query:
            matched_col = next((c for c in num_cols if c.lower() in user_query.lower()), num_cols[0])
            ki_out = f"Analyse für '{matched_col}': Max {df[matched_col].max():,.2f}, Schnitt {df[matched_col].mean():,.2f}."
            st.info(f"🤖 {ki_out}")

        # --- 7. AUTOMATION & BRIDGE (VBA, PHP, SQL, Baukasten) ---
        st.divider()
        st.header("⚙️ Automation Bridge & PHP Architect")
        t1, t2, t3, t4 = st.tabs(["📟 VBA Makros", "🐘 PHP Connect", "🗄️ SQL Schema", "🛠️ PHP Baukasten"])

        with t1:
            st.subheader("Excel-Automatisierung")
            vba_code = f"Sub DataPro_Automator()\n    ' Generiert für {selected_file}\n"
            vba_code += f"    MsgBox \"Analyse fertig! Max Wert: \" & {df[main_col].max()}\n"
            vba_code += "    Cells.SpecialCells(xlCellTypeBlanks).Delete\nEnd Sub"
            st.code(vba_code, language="vba")

        with t2:
            st.subheader("PHP Live-Schnittstelle")
            url = st.text_input("Ziel-URL (API):", "https://deine-seite.de/upload.php")
            if st.button("🚀 Daten an PHP senden"):
                try:
                    res = requests.post(url, json={"data": f_df.to_json(), "file": selected_file})
                    st.success(f"Status {res.status_code}: {res.text}")
                except Exception as e: st.error(f"Sende-Fehler: {e}")

        with t3:
            st.subheader("MySQL Create Table Generator")
            sql_name = selected_file.split('.')[0].replace(" ", "_")
            sql = f"CREATE TABLE `{sql_name}` (\n    id INT AUTO_INCREMENT PRIMARY KEY,\n"
            for c in df.columns:
                dtype = "DOUBLE" if c in num_cols else "VARCHAR(255)"
                sql += f"    `{c}` {dtype},\n"
            st.code(sql.rstrip(',\n') + "\n);", language="sql")

        with t4:
            st.subheader("Server-Dateien Generator")
            db_name = st.text_input("Datenbank Name", "analytics_db")
            db_php = f"<?php\n// db_connect.php\n$pdo = new PDO('mysql:host=localhost;dbname={db_name}', 'root', '');\n?>"
            st.code(db_php, language="php")
            st.download_button("Download db_connect.php", db_php, "db_connect.php")

        # --- 8. PDF REPORT ---
        st.divider()
        if st.button("📄 Profi-Report generieren"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Enterprise Analysis Report", ln=True, align='C')
            pdf.set_font("Arial", "", 12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Datei: {selected_file}", ln=True)
            if ki_out: pdf.multi_cell(0, 10, f"KI-Info: {ki_out}")
            st.download_button("📥 Report herunterladen", pdf.output(dest="S").encode("latin-1"), "Report.pdf")

    else:
        st.error("Keine numerischen Daten gefunden.")
else:
    st.info("Willkommen! Bitte lade eine CSV oder Excel Datei hoch.")
