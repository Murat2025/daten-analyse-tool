import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from fpdf import FPDF
import io

# --- 1. SETUP & ENTERPRISE DESIGN ---
st.set_page_config(page_title="DataPro AI | Ultimate Enterprise Suite", page_icon="💎", layout="wide")

# Custom CSS für professionelles Dashboard-Styling
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

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("🔑 Master-Passwort", type="password", 
                      on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), 
                      key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. LOGIK-KERN (Ultra-Bereinigung) ---
def clean_data_ultra(df):
    # Entfernt leere Zeilen und Spalten
    df = df.dropna(how='all').dropna(axis=1, how='all')
    for col in df.columns:
        # Bereinigung von Währungen (€, $) und Einheiten (kg, %)
        if df[col].dtype == 'object':
            try:
                temp_col = df[col].astype(str).str.replace(r'[€$%kg\s]', '', regex=True).str.replace(',', '.')
                df[col] = pd.to_numeric(temp_col)
            except: pass
        # Automatische Datumskonvertierung
        if 'datum' in col.lower() or 'date' in col.lower():
            try: df[col] = pd.to_datetime(df[col])
            except: pass
    return df

# --- 3. DATEI-IMPORT (Multi-Format Support) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.header("📁 Daten-Zentrum")
uploaded_files = st.sidebar.file_uploader("CSV oder Excel hochladen", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    # Lade Dateien mit entsprechender Engine
    dfs = {f.name: clean_data_ultra(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')) for f in uploaded_files}
    selected_file = st.sidebar.selectbox("Fokus-Datei wählen", list(dfs.keys()))
    df = dfs[selected_file]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 4. KPI DASHBOARD ---
        st.title(f"🚀 Enterprise Intelligence: {selected_file}")
        k1, k2, k3, k4 = st.columns(4)
        main_col = num_cols[0]
        
        k1.metric("Maximum", f"{df[main_col].max():,.2f}")
        k2.metric("Durchschnitt", f"{df[main_col].mean():,.2f}")
        k3.metric("Datensätze", len(df))
        k4.metric("Spaltenanzahl", len(df.columns))

        # --- 5. VISUALISIERUNG & AUSREISSER ---
        st.sidebar.divider()
        range_slider = st.sidebar.slider("Datenbereich (Zeilen)", 0, len(df), (0, len(df)))
        f_df = df.iloc[range_slider[0]:range_slider[1]]
        
        st.subheader("📊 Trend-Analyse & Outlier-Detection")
        selected_metrics = st.multiselect("Metriken vergleichen:", num_cols, default=num_cols[:1])
        
        fig = go.Figure()
        for m in selected_metrics:
            y_vals = f_df[m].values
            fig.add_trace(go.Scatter(x=f_df.index, y=y_vals, name=m, mode='lines+markers'))
            
            # Outlier Detection (2x Standardabweichung)
            mean_v, std_v = y_vals.mean(), y_vals.std()
            outlier_mask = np.abs(y_vals - mean_v) > (2 * std_v)
            if any(outlier_mask):
                fig.add_trace(go.Scatter(
                    x=f_df.index[outlier_mask], y=y_vals[outlier_mask],
                    mode='markers', name=f'Outlier {m}',
                    marker=dict(color='red', size=12, symbol='x')
                ))
        
        fig.update_layout(hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- 6. SMART QUERY ULTRA ---
        st.divider()
        st.subheader("💬 Smart Query")
        user_query = st.text_input("KI-Analyse (z.B. 'Was ist das Maximum?')")
        ki_out = ""
        if user_query:
            matched_col = next((c for c in num_cols if c.lower() in user_query.lower()), num_cols[0])
            ki_out = f"Analyse für '{matched_col}': Max {df[matched_col].max():,.2f}, Schnitt {df[matched_col].mean():,.2f}."
            st.info(f"🤖 {ki_out}")

        # --- 7. AUTOMATION BRIDGE (VBA, PHP, SQL, Baukasten) ---
        st.divider()
        st.header("⚙️ Advanced Bridge Operations")
        t_vba, t_php, t_sql, t_build = st.tabs(["📟 Formel-VBA", "🔐 Secure PHP", "🗄️ SQL Architect", "🛠️ PHP Baukasten"])

        with t_vba:
            st.subheader("Excel Formel-Generator")
            last_row = len(df) + 1
            vba_code = f"""Sub AutoCalculate()
    ' Automatische Formeln für {selected_file}
    Dim lastRow As Long
    lastRow = Cells(Rows.Count, 1).End(xlUp).Row
    
    ' Summe am Ende der Hauptspalte
    Range("B" & lastRow + 1).Formula = "=SUM(B2:B" & lastRow & ")"
    
    ' Highlight über Durchschnitt ({df[main_col].mean():.2f})
    With Range("B2:B" & lastRow).FormatConditions.Add(xlCellValue, xlGreater, "={df[main_col].mean()}")
        .Interior.Color = RGB(255, 199, 206)
    End With
    MsgBox "Analyse abgeschlossen!", vbInformation
End Sub"""
            st.code(vba_code, language="vba")

        with t_php:
            st.subheader("Sicherer Datentransfer")
            api_token = st.text_input("Security Token:", "MY_SECRET_KEY_123")
            url = st.text_input("Ziel URL:", "https://deine-seite.de/upload.php")
            if st.button("🚀 Sicher an PHP senden"):
                try:
                    headers = {"Authorization": f"Bearer {api_token}"}
                    res = requests.post(url, json={"data": f_df.to_json(), "file": selected_file}, headers=headers)
                    st.success(f"Status {res.status_code}: {res.text}")
                except Exception as e: st.error(f"Fehler: {e}")

        with t_sql:
            st.subheader("SQL Schema")
            sql_name = selected_file.split('.')[0].replace(" ", "_")
            sql = f"CREATE TABLE `{sql_name}` (\n  id INT AUTO_INCREMENT PRIMARY KEY,\n"
            for c in df.columns:
                dtype = "DOUBLE" if c in num_cols else "VARCHAR(255)"
                sql += f"    `{c}` {dtype},\n"
            st.code(sql.rstrip(',\n') + "\n);", language="sql")

        with t_build:
            st.subheader("PHP Server-Dateien")
            db_name = st.text_input("DB Name", "analytics_db")
            db_php = f"<?php\n// db_connect.php\n$pdo = new PDO('mysql:host=localhost;dbname={db_name}', 'root', '');\n?>"
            st.code(db_php, language="php")
            st.download_button("Download db_connect.php", db_php, "db_connect.php")

        # --- 8. REPORT EXPORT ---
        st.divider()
        if st.button("📄 Profi-Report generieren"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Enterprise Analysis Report", ln=True, align='C')
            st.download_button("📥 Report herunterladen", pdf.output(dest="S").encode("latin-1"), "Report.pdf")

    else:
        st.error("Keine numerischen Daten gefunden.")
else:
    st.info("Willkommen! Bitte lade eine CSV oder Excel Datei hoch.")
