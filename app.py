import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from fpdf import FPDF
import io

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

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("🔑 Master-Passwort", type="password", 
                      on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), 
                      key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. LOGIK-KERN (Ultra-Bereinigung & Währungen) ---
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

# --- 3. DATEI-IMPORT (Multi-Format Support) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.header("📁 Daten-Zentrum")
uploaded_files = st.sidebar.file_uploader("CSV oder Excel hochladen", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    dfs = {f.name: clean_data_ultra(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')) for f in uploaded_files}
    selected_file = st.sidebar.selectbox("Fokus-Datei wählen", list(dfs.keys()))
    df = dfs[selected_file]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if num_cols:
        # --- 4. KPI DASHBOARD ---
        st.title(f"🚀 Bridge Controller: {selected_file}")
        k1, k2, k3, k4 = st.columns(4)
        main_col = num_cols[0]
        k1.metric("Maximum", f"{df[main_col].max():,.2f}")
        k2.metric("Durchschnitt", f"{df[main_col].mean():,.2f}")
        k3.metric("Datensätze", len(df))
        k4.metric("Zahlenspalten", len(num_cols))

        # --- 5. VISUALISIERUNG & KORRELATION ---
        st.divider()
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📊 Trend-Analyse & Outlier-Detection")
            range_slider = st.sidebar.slider("Datenbereich (Zeilen)", 0, len(df), (0, len(df)))
            f_df = df.iloc[range_slider[0]:range_slider[1]]
            sel_metrics = st.multiselect("Metriken vergleichen:", num_cols, default=num_cols[:1])
            fig = go.Figure()
            for m in sel_metrics:
                y_vals = f_df[m].values
                fig.add_trace(go.Scatter(x=f_df.index, y=y_vals, name=m, mode='lines+markers'))
                mean_v, std_v = y_vals.mean(), y_vals.std()
                outlier_mask = np.abs(y_vals - mean_v) > (2 * std_v)
                if any(outlier_mask):
                    fig.add_trace(go.Scatter(x=f_df.index[outlier_mask], y=y_vals[outlier_mask], mode='markers', name=f'Outlier {m}', marker=dict(color='red', size=12, symbol='x')))
            fig.update_layout(hovermode="x unified", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("🔗 Korrelation")
            if len(num_cols) > 1:
                corr = f_df[num_cols].corr()
                fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r')
                st.plotly_chart(fig_corr, use_container_width=True)
            else: st.info("Mehr Spalten nötig.")

        # --- 6. SMART QUERY KI ---
        st.divider()
        st.subheader("💬 Smart Query KI")
        user_query = st.text_input("KI-Analyse (z.B. 'Was ist das Maximum?')")
        ki_out = ""
        if user_query:
            matched_col = next((c for c in num_cols if c.lower() in user_query.lower()), num_cols[0])
            ki_out = f"Analyse für '{matched_col}': Max {df[matched_col].max():,.2f}, Schnitt {df[matched_col].mean():,.2f}."
            st.info(f"🤖 {ki_out}")

        # --- 7. ADVANCED AUTOMATION BRIDGE ---
        st.divider()
        st.header("⚙️ Advanced Bridge Operations")
        t_vba, t_php, t_sql, t_web, t_build = st.tabs(["📟 VBA Pivot-Makro", "🔐 Secure PHP Post", "🗄️ SQL Architect", "🌐 Web-Dashboard", "🛠️ PHP Baukasten Pro"])

        with t_vba:
            st.subheader("Excel Pivot-Makro Generator")
            vba_code = f"""Sub CreatePivotTable()\n    ' Generiert für {selected_file}\n    Dim pc As PivotCache: Dim pt As PivotTable\n    Set pc = ActiveWorkbook.PivotCaches.Create(SourceType:=xlDatabase, SourceData:=ActiveSheet.UsedRange)\n    Set pt = pc.CreatePivotTable(TableDestination:=Sheets.Add.Range("A3"), TableName:="DataProPivot")\n    With pt.PivotFields("{num_cols[0]}")\n        .Orientation = xlDataField: .Function = xlSum: .NumberFormat = "#.##0,00"\n    End With\nEnd Sub"""
            st.code(vba_code, language="vba")

        with t_php:
            st.subheader("Sicherer Datentransfer (API)")
            api_token = st.text_input("Security Token:", "MY_SECRET_KEY_123")
            url = st.text_input("Ziel URL:", "https://deine-seite.de/api/upload.php")
            if st.button("🚀 Sicher an PHP senden"):
                try:
                    headers = {"Authorization": f"Bearer {api_token}"}
                    res = requests.post(url, json={"data": f_df.to_json(orient="records"), "file": selected_file}, headers=headers)
                    st.success(f"Status {res.status_code}: {res.text}")
                except Exception as e: st.error(f"Fehler: {e}")

        with t_sql:
            st.subheader("MySQL Create Table Generator")
            sql_name = selected_file.split('.')[0].replace(" ", "_").lower()
            sql = f"CREATE TABLE `{sql_name}` (\n    id INT AUTO_INCREMENT PRIMARY KEY,\n"
            for c in df.columns:
                dtype = "DOUBLE" if c in num_cols else "VARCHAR(255)"
                sql += f"    `{c.replace(' ', '_').lower()}` {dtype},\n"
            st.code(sql.rstrip(',\n') + "\n);", language="sql")

        with t_web:
            st.subheader("PHP Web-Interface & Realtime Chart")
            sql_name_web = selected_file.split('.')[0].replace(' ', '_').lower()
            st.write("Diese `chart.php` zeigt deine Daten als Echtzeit-Grafik an:")
            chart_php = f"""<?php
require 'db_connect.php';
$stmt = $pdo->query("SELECT id, {num_cols[0]} FROM {sql_name_web} ORDER BY id DESC LIMIT 20");
$data = $stmt->fetchAll(PDO::FETCH_ASSOC);
$labels = json_encode(array_column(array_reverse($data), 'id'));
$values = json_encode(array_column(array_reverse($data), '{num_cols[0]}'));
?>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<canvas id="myChart"></canvas>
<script>
new Chart(document.getElementById('myChart'), {{
    type: 'line',
    data: {{ labels: {labels}, datasets: [{{ label: '{num_cols[0]}', data: {values}, borderColor: 'blue' }}] }}
}});
</script>"""
            st.code(chart_php, language="php")
            st.download_button("Download chart.php", chart_php, "chart.php")

        with t_build:
            st.subheader("PHP Architect (Vollständiges Backend)")
            db_name = st.text_input("Datenbank Name", "analytics_db")
            sql_name_clean = selected_file.split('.')[0].replace(" ", "_").lower()
            
            db_php = f"<?php\n$pdo = new PDO('mysql:host=localhost;dbname={db_name}', 'root', '');\n?>"
            st.code(db_php, language="php")
            
            upload_php = f"""<?php
require 'db_connect.php';
$secret = "{api_token}";
if ($_SERVER['HTTP_AUTHORIZATION'] !== "Bearer " . $secret) {{ http_response_code(403); die(); }}
$input = json_decode(file_get_contents('php://input'), true);
$data = json_decode($input['data'], true);
foreach ($data as $row) {{
    $cols = implode(", ", array_keys($row));
    $pts = ":" . implode(", :", array_keys($row));
    $pdo->prepare("INSERT INTO {sql_name_clean} ($cols) VALUES ($pts)")->execute($row);
}}
echo "Daten gespeichert!"; ?>"""
            st.code(upload_php, language="php")
            st.download_button("Download upload.php", upload_php, "upload.php")

        # --- 8. REPORT EXPORT ---
        st.divider()
        if st.button("📄 Profi-Report generieren"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Enterprise Analysis Report", ln=True, align='C')
            st.download_button("📥 Report herunterladen", pdf.output(dest="S").encode("latin-1"), "Report.pdf")

    else: st.error("Keine numerischen Daten gefunden.")
else: st.info("Willkommen Murat! Lade eine Datei hoch, um das Bridge-System zu starten.")
