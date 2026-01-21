import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF

# --- 1. SETUP & LOGIN ---
st.set_page_config(page_title="DataPro AI Ultimate", page_icon="🚀", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("🔑 Master-Passwort", type="password", 
                      on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), 
                      key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. DATEN-BEREINIGUNG FUNKTION ---
def clean_data(df):
    # Entfernt komplett leere Zeilen und Spalten
    df = df.dropna(how='all').dropna(axis=1, how='all')
    # Versucht, Datumsspalten automatisch zu konvertieren
    for col in df.columns:
        if 'datum' in col.lower() or 'date' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass
    return df

# --- 3. HEADER & MULTI-FILE-LOGIK ---
st.title("🚀 DataPro AI: Ultimate Universal Suite")
st.sidebar.header("📁 Daten-Zentrum")
uploaded_files = st.sidebar.file_uploader("CSV-Dateien hochladen", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = {f.name: clean_data(pd.read_csv(f)) for f in uploaded_files}
    selected_file_name = st.sidebar.selectbox("Aktive Datei wählen", list(dfs.keys()))
    df = dfs[selected_file_name]
    
    # Automatische Erkennung aller Zahlenspalten
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 4. DASHBOARD & FILTER ---
        st.sidebar.divider()
        st.sidebar.subheader("📅 Zeit-Filter")
        start_row, end_row = st.sidebar.slider("Datenbereich wählen", 0, len(df), (0, len(df)))
        filtered_df = df.iloc[start_row:end_row]

        # Schnell-Metriken oben
        st.subheader(f"📊 Analyse: {selected_file_name}")
        m_cols = st.columns(min(len(num_cols), 4))
        for i, col in enumerate(num_cols[:4]):
            with m_cols[i]:
                current_val = filtered_df[col].iloc[-1] if not filtered_df[col].empty else 0
                st.metric(col, f"{current_val:,.2f}")

        # Multi-Kurven Chart
        selected_metrics = st.multiselect("Metriken vergleichen:", num_cols, default=num_cols[:1])
        fig = go.Figure()
        for m in selected_metrics:
            fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df[m], name=m, mode='lines+markers'))
        fig.update_layout(hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- 5. SMART QUERY ULTRA (Mit Ausreißer-Erkennung) ---
        st.divider()
        st.subheader("💬 Smart Query Ultra (KI)")
        user_query = st.text_input("Stelle eine Frage zu deinen Daten (z.B. 'Wann war das Maximum von " + num_cols[0] + "?')")
        
        ki_out = ""
        if user_query:
            q = user_query.lower()
            # Erkennt automatisch, welche Spalte gemeint ist
            matched_col = next((c for c in num_cols if c.lower() in q), num_cols[0])
            y_data = filtered_df[matched_col].values
            
            st.markdown("---")
            if "ausreißer" in q or "fehler" in q:
                mean, std = y_data.mean(), y_data.std()
                outliers = filtered_df[np.abs(filtered_df[matched_col] - mean) > (2 * std)]
                ki_out = f"Ausreißer-Check für '{matched_col}': {len(outliers)} verdächtige Werte gefunden."
                st.warning(f"🤖 {ki_out}")
                if not outliers.empty:
                    st.write(outliers)
            elif "hoch" in q or "max" in q:
                idx_max = filtered_df[matched_col].idxmax()
                ki_out = f"Maximum in '{matched_col}': {y_data.max():,.2f} in Zeile {idx_max}."
                st.success(f"🤖 {ki_out}")
            elif "vergleich" in q or "differenz" in q:
                diff = y_data[-1] - y_data[0]
                ki_out = f"Vergleich '{matched_col}': Start {y_data[0]:,.2f} -> Ende {y_data[-1]:,.2f} (Diff: {diff:,.2f})."
                st.info(f"🤖 {ki_out}")
            else:
                ki_out = f"Durchschnitt von '{matched_col}': {y_data.mean():,.2f}."
                st.write(f"🤖 {ki_out}")

        # --- 6. EXPORT ---
        st.divider()
        if st.button("📄 Profi-Report generieren"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "DataPro Ultimate Analysis Report", ln=True, align='C')
            pdf.set_font("Arial", "", 12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Datei: {selected_file_name}", ln=True)
            pdf.cell(200, 10, f"Bereich: Zeile {start_row} bis {end_row}", ln=True)
            if ki_out:
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, "KI-Analyse-Ergebnis:", ln=True)
                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, ki_out)
            
            st.download_button("📥 PDF herunterladen", pdf.output(dest="S").encode("latin-1"), "DataPro_Report.pdf")

    else:
        st.error("Diese CSV enthält keine Zahlen zum Analysieren.")
else:
    st.info("Bereit! Lade eine oder mehrere CSV-Dateien hoch. Ich bereinige die Daten automatisch und starte die KI.")