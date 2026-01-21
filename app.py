import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests # Für die PHP-Live-Schnittstelle
from fpdf import FPDF
import io

# --- 1. SETUP & LOGIN (Sicherheits-Layer) ---
st.set_page_config(page_title="DataPro AI Ultimate Bridge", page_icon="🚀", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("🔑 Master-Passwort", type="password", 
                      on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), 
                      key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. AUTO-DATA-CLEANING ---
def clean_data(df):
    # Entfernt leere Zeilen/Spalten
    df = df.dropna(how='all').dropna(axis=1, how='all')
    # Datumskonvertierung
    for col in df.columns:
        if 'datum' in col.lower() or 'date' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass
    return df

# --- 3. MULTI-FORMAT-SUPPORT (CSV & XLSX) ---
st.title("🚀 DataPro AI: Ultimate Universal Bridge")
st.sidebar.header("📁 Daten-Zentrum")
uploaded_files = st.sidebar.file_uploader("CSV oder Excel hochladen", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    dfs = {}
    for f in uploaded_files:
        if f.name.endswith('.csv'):
            dfs[f.name] = clean_data(pd.read_csv(f))
        else:
            dfs[f.name] = clean_data(pd.read_excel(f))

    selected_file_name = st.sidebar.selectbox("Aktive Datei wählen", list(dfs.keys()))
    df = dfs[selected_file_name]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 4. ZEIT-SLIDER-FILTER ---
        st.sidebar.divider()
        start_row, end_row = st.sidebar.slider("Datenbereich (Zeilen)", 0, len(df), (0, len(df)))
        filtered_df = df.iloc[start_row:end_row]

        # --- 5. MULTI-KURVEN-VISUALISIERUNG ---
        st.subheader(f"📊 Analyse: {selected_file_name}")
        selected_metrics = st.multiselect("Metriken vergleichen:", num_cols, default=num_cols[:1])
        
        fig = go.Figure()
        for m in selected_metrics:
            fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df[m], name=m, mode='lines+markers'))
        fig.update_layout(hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- 6. SMART QUERY ULTRA (KI-Suche & Outlier) ---
        st.divider()
        st.subheader("💬 Smart Query Ultra")
        user_query = st.text_input("Frag die KI (z.B. 'Max von " + num_cols[0] + "' oder 'Ausreißer')")
        ki_out = ""
        if user_query:
            q = user_query.lower()
            matched_col = next((c for c in num_cols if c.lower() in q), num_cols[0])
            y_data = filtered_df[matched_col].values
            
            if "hoch" in q or "max" in q:
                ki_out = f"Maximum in '{matched_col}': {y_data.max():,.2f}."
                st.success(f"🤖 {ki_out}")
            elif "ausreißer" in q:
                mean, std = y_data.mean(), y_data.std()
                outliers = filtered_df[np.abs(filtered_df[matched_col] - mean) > (2 * std)]
                ki_out = f"Gefundene Ausreißer in '{matched_col}': {len(outliers)}."
                st.warning(f"🤖 {ki_out}")
            else:
                ki_out = f"Durchschnitt von '{matched_col}': {y_data.mean():,.2f}."
                st.info(f"🤖 {ki_out}")

        # --- 7. EXCEL-PHP-BRIDGE (VBA & PHP) ---
        st.divider()
        st.header("🔌 Excel-PHP-Bridge & Automation")
        tab_vba, tab_php = st.tabs(["📟 VBA-Makro-Generator", "🐘 PHP-Data-Bridge"])

        with tab_vba:
            st.subheader("Automatisches Excel-Makro")
            vba_task = st.selectbox("Makro-Ziel:", ["Reinigung", "Highlight Outliers"])
            vba_code = f"Sub DataPro_Automator()\n    ' Generiert für {selected_file_name}\n"
            if vba_task == "Reinigung":
                vba_code += "    Cells.SpecialCells(xlCellTypeBlanks).Delete\n    Columns.AutoFit\n"
            else:
                vba_code += f"    ' Markiere Zellen > {y_data.mean():.0f}\n    For Each c In UsedRange\n        If c.Value > {y_data.mean():.0f} Then c.Interior.Color = vbRed\n    Next c\n"
            vba_code += "End Sub"
            st.code(vba_code, language="vba")

        with tab_php:
            st.subheader("PHP Live-Schnittstelle")
            target_url = st.text_input("Ziel-URL deines PHP-Skripts:", "https://deine-seite.de/api/upload.php")
            
            if st.button("🚀 Daten jetzt an PHP-Server senden"):
                try:
                    json_payload = filtered_df.to_json(orient="records")
                    response = requests.post(target_url, json={"data": json_payload, "file": selected_file_name})
                    st.success(f"Server-Antwort: {response.text}")
                except Exception as e:
                    st.error(f"Fehler: {e}")
            
            st.divider()
            st.write("Vorschau PHP-Sicherheits-Skript (PDO):")
            php_pdo = "<?php\n$pdo = new PDO('mysql:host=localhost;dbname=db', 'user', 'pass');\n// Logik..."
            st.code(php_pdo, language="php")

        # --- 8. PROFI-PDF-EXPORT ---
        st.divider()
        if st.button("📄 Profi-Report generieren"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Business Intelligence Report", ln=True, align='C')
            pdf.set_font("Arial", "", 12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Datei: {selected_file_name}", ln=True)
            if ki_out: pdf.multi_cell(0, 10, f"KI-Ergebnis: {ki_out}")
            st.download_button("📥 PDF herunterladen", pdf.output(dest="S").encode("latin-1"), "Report.pdf")

    else:
        st.error("Keine numerischen Daten gefunden.")
else:
    st.info("Willkommen! Lade eine CSV oder Excel hoch, um die Bridge-Suite zu nutzen.")
