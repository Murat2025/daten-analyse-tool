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
import plotly.io as pio

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
    .anomaly-card {
        background-color: #fff3f3;
        border-left: 5px solid #ff4b4b;
        padding: 10px;
        margin-bottom: 5px;
        border-radius: 5px;
    }
    .ki-insight-box {
        background-color: #f0f7ff;
        border-left: 5px solid #007bff;
        padding: 15px;
        border-radius: 8px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. USER MANAGEMENT & LOGGING SYSTEM ---
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
            st.info("Admins sehen die Bridge-Tools (VBA/SQL/PHP), Viewer sehen nur die Analyse-Dashboards.")
        user_role = st.selectbox("Rolle wählen", ["Viewer (Nur Ansicht)", "Admin (Vollzugriff)"])
        password = st.text_input("Passwort eingeben", type="password")
        if st.button("Anmelden"):
            try:
                if user_role == "Admin (Vollzugriff)" and password == st.secrets["admin_password"]:
                    st.session_state["auth_level"] = "admin"
                    add_log("Login Admin erfolgreich")
                    st.rerun()
                elif user_role == "Viewer (Nur Ansicht)" and password == st.secrets["viewer_password"]:
                    st.session_state["auth_level"] = "viewer"
                    add_log("Login Viewer erfolgreich")
                    st.rerun()
                else: st.error("Passwort falsch.")
            except: st.error("Secrets (admin_password/viewer_password) fehlen.")
        return False
    return True

if not login_system():
    st.stop()

# --- 3. TESTDATEN-GENERATOR ---
def generate_demo_data():
    dates = pd.date_range(start="2025-01-01", periods=110)
    base_sales = np.linspace(1000, 2500, 110)
    noise = np.random.normal(0, 50, 110)
    sales = base_sales + noise
    sales[15], sales[45], sales[80] = 5000, 5200, 150 
    df_demo = pd.DataFrame({
        'Datum': dates,
        'Umsatz': np.round(sales, 2),
        'Menge': np.round(sales / 25).astype(int),
        'Kosten': np.round(sales * 0.6, 2),
        'Region': np.random.choice(['Nord', 'Süd', 'West', 'Ost'], 110),
        'Status': 'aktiv'
    })
    return df_demo

# --- 4. LOGIK-KERN (Bereinigung & Validierung) ---
def clean_and_validate(df):
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
    
    warnings = []
    num_df = df.select_dtypes(include=[np.number])
    if (num_df < 0).any().any():
        warnings.append("⚠️ Warnung: Negative Werte entdeckt!")
    return df, warnings

# --- 5. SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.header(f"📁 Daten ({st.session_state['auth_level'].upper()})")

if st.sidebar.button("🧪 Testdaten generieren"):
    st.session_state["demo_df"] = generate_demo_data()
    add_log("Demo-Daten erstellt")
    st.sidebar.success("Testdaten bereit!")

uploaded_files = st.sidebar.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"], accept_multiple_files=True)

dfs = {}
if uploaded_files:
    for f in uploaded_files:
        raw_df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
        dfs[f.name], _ = clean_and_validate(raw_df)
elif "demo_df" in st.session_state:
    dfs["Murat_Testdaten.xlsx"] = st.session_state["demo_df"]

if dfs:
    selected_file = st.sidebar.selectbox("Fokus-Datei wählen", list(dfs.keys()))
    df = dfs[selected_file].copy()
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()

    if num_cols:
        st.title(f"🚀 Bridge Controller: {selected_file}")
        
        # --- LIVE WÄHRUNGSRECHNER ---
        st.sidebar.divider()
        st.sidebar.subheader("💱 Live Währungsrechner")
        target_currency = st.sidebar.selectbox("Zielwährung:", ["EUR", "USD", "CHF", "GBP"])
        conversion_factor = 1.0
        if target_currency != "EUR":
            try:
                rates = requests.get(f"https://open.er-api.com/v6/latest/EUR").json()["rates"]
                conversion_factor = rates[target_currency]
                st.sidebar.info(f"Kurs: 1 EUR = {conversion_factor:.4f} {target_currency}")
            except: st.sidebar.error("API Fehler")

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        main_col = num_cols[0]
        k1.metric("Maximum", f"{df[main_col].max() * conversion_factor:,.2f} {target_currency}")
        k2.metric("Durchschnitt", f"{df[main_col].mean() * conversion_factor:,.2f} {target_currency}")
        k3.metric("Datensätze", len(df))
        anomaly_count = (np.abs(df[main_col] - df[main_col].mean()) > (2 * df[main_col].std())).sum()
        k4.metric("Anomalien", anomaly_count)

        # ANOMALIE-BENACHRICHTIGUNG
        st.subheader("🚨 Kritische Daten-Anomalien")
        anomalies = []
        df['diff'] = df[main_col].pct_change().abs()
        jumps = df[df['diff'] > 0.5]
        for idx, row in jumps.tail(3).iterrows():
            anomalies.append(f"Extremer Sprung (+{row['diff']*100:.1f}%) bei Index {idx}")
        z_scores = (df[main_col] - df[main_col].mean()) / df[main_col].std()
        outliers = df[z_scores.abs() > 3]
        for idx, row in outliers.tail(2).iterrows():
            anomalies.append(f"Statistischer Ausreißer bei Index {idx}")

        if anomalies:
            for a in anomalies: st.markdown(f"<div class='anomaly-card'>{a}</div>", unsafe_allow_html=True)
        else: st.success("Keine Anomalien gefunden.")

        # --- VISUALISIERUNG & MODI ---
        st.divider()
        viz_col1, viz_col2 = st.columns([1, 3])
        with viz_col1:
            chart_type = st.radio("Analyse-Modus:", ["Trend & Ausreißer", "🤖 KI-Vorhersage", "📈 Korrelation", "🔥 Heatmap", "📊 Pivot-Analyse"])
            sel_metrics = st.multiselect("Metriken:", num_cols, default=num_cols[:1])
            
            st.write("---")
            st.subheader("📥 Export Center")
            
            # Excel Export mit Robustheits-Fix
            output_excel = io.BytesIO()
            try:
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
            except:
                with pd.ExcelWriter(output_excel) as writer:
                    df.to_excel(writer, index=False)
            st.download_button(label="📊 Excel Download", data=output_excel.getvalue(), file_name=f"Clean_{selected_file}.xlsx")
            
            # Profi-PDF Report
            if st.button("📄 Profi-PDF Report"):
                add_log("PDF Export")
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt="Enterprise Analytics Report", ln=True, align='C')
                pdf.set_font("Arial", size=10)
                pdf.cell(200, 10, txt=f"Erstellt: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
                pdf.ln(10)
                pdf.cell(200, 10, txt=f"Datensatze: {len(df)} | Max: {df[main_col].max():,.2f}", ln=True)
                if 'current_fig' in st.session_state:
                    img_bytes = pio.to_image(st.session_state.current_fig, format="png")
                    pdf.image(io.BytesIO(img_bytes), x=10, y=None, w=190)
                st.download_button("📥 PDF Herunterladen", data=pdf.output(dest='S').encode('latin-1'), file_name="Report.pdf")
        
        with viz_col2:
            if chart_type == "Trend & Ausreißer":
                fig = go.Figure()
                for m in sel_metrics:
                    y_v = df[m].values * conversion_factor
                    fig.add_trace(go.Scatter(y=y_v, name=m, mode='markers+lines'))
                st.session_state.current_fig = fig
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "🤖 KI-Vorhersage":
                y = (df[main_col].values * conversion_factor).reshape(-1, 1)
                X = np.arange(len(y)).reshape(-1, 1)
                model = LinearRegression().fit(X, y)
                pred = model.predict(np.arange(len(y), len(y)+30).reshape(-1, 1))
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=y.flatten(), name="Historisch"))
                fig.add_trace(go.Scatter(x=np.arange(len(y), len(y)+30), y=pred.flatten(), name="KI-Prognose", line=dict(dash='dash')))
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "📈 Korrelation":
                col_x = st.selectbox("X-Achse:", num_cols, index=0)
                col_y = st.selectbox("Y-Achse:", num_cols, index=1)
                st.plotly_chart(px.scatter(df, x=col_x, y=col_y, trendline="ols", template="plotly_white"), use_container_width=True)
            elif chart_type == "🔥 Heatmap":
                if date_cols:
                    df['Wochentag'] = df[date_cols[0]].dt.day_name()
                    df['Monat_Name'] = df[date_cols[0]].dt.month_name()
                    heatmap_data = df.pivot_table(index='Wochentag', columns='Monat_Name', values=main_col, aggfunc='mean')
                    st.plotly_chart(px.imshow(heatmap_data, text_auto=True, color_continuous_scale='Viridis'), use_container_width=True)
            elif chart_type == "📊 Pivot-Analyse":
                p_index = st.selectbox("Gruppieren nach:", cat_cols if cat_cols else df.columns)
                p_values = st.selectbox("Werte:", num_cols)
                pivot_table = df.pivot_table(index=p_index, values=p_values, aggfunc='sum')
                st.dataframe(pivot_table, use_container_width=True)

        # --- ZEIT-ANALYSE ---
        if date_cols:
            st.divider()
            st.subheader("📅 Zeit-Analyse (Best Performance)")
            t1, t2 = st.columns(2)
            d_col = date_cols[0]
            with t1:
                df['Day'] = df[d_col].dt.day_name()
                st.plotly_chart(px.bar(df.groupby('Day')[main_col].sum().reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]), title="Umsatz nach Wochentag"), use_container_width=True)
            with t2:
                df['Month'] = df[d_col].dt.month_name()
                st.plotly_chart(px.bar(df.groupby('Month')[main_col].sum(), title="Umsatz nach Monat", color_discrete_sequence=['#00CC96']), use_container_width=True)

        # --- KI-INSIGHT-ENGINE ---
        st.divider()
        st.subheader("🤖 KI-Insight Zusammenfassung")
        trend = "steigend" if (df[main_col].tail(10).mean() > df[main_col].head(10).mean()) else "fallend"
        insight_text = f"Analyse abgeschlossen: Der Trend für {selected_file} ist **{trend}**. Datenqualitat: {'Kritisch' if anomaly_count > 5 else 'Gut'}."
        st.markdown(f"<div class='ki-insight-box'>{insight_text}</div>", unsafe_allow_html=True)

        # --- 8. ADVANCED BRIDGE OPERATIONS (VOLLSTÄNDIG) ---
        if st.session_state["auth_level"] == "admin":
            st.divider()
            st.header("⚙️ Advanced Bridge Operations")
            tabs = st.tabs(["📟 VBA Power-Bridge", "🗄️ SQL Architect Pro", "🛠️ PHP Secure Engine", "📜 Aktivitäts-Log"])
            
            with tabs[0]:
                st.subheader("VBA Sync-Makro mit Error Handling")
                vba_url = st.text_input("VBA API URL:", "https://deine-seite.de/api/bridge.php")
                st.code(f"""Sub SyncToCloud()
    On Error GoTo ErrorHandler
    Dim http As Object, payload As String
    ' ... JSON Generierung ...
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", "{vba_url}", False
    http.setRequestHeader "Content-Type", "application/json"
    http.Send payload
    If http.Status = 200 Then MsgBox "Sync erfolgreich!", vbInformation Else MsgBox "Fehler: " & http.Status
    Exit Sub
ErrorHandler:
    MsgBox "Verbindungsfehler!", vbCritical
End Sub""", language="vba")

            with tabs[1]:
                st.subheader("SQL Table & Index Architect")
                sql_name = selected_file.split('.')[0].replace(" ", "_").lower()
                st.code(f"""CREATE TABLE `{sql_name}` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datum DATETIME,
    wert DOUBLE,
    INDEX idx_datum (datum)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""", language="sql")
            
            with tabs[2]:
                st.subheader("PHP Secure Bridge Engine")
                st.code(f"""<?php
// Secure Upsert Logic
require_once 'config.php';
$data = json_decode(file_get_contents('php://input'), true);
if($data) {{
    // Auto-Backup & Upsert
    $pdo->exec("CREATE TABLE IF NOT EXISTS backup_... LIKE ...");
    echo "Processing " . count($data) . " rows.";
}}
?>""", language="php")

            with tabs[3]:
                st.subheader("System-Aktivitäts-Log")
                st.table(pd.DataFrame(st.session_state["activity_log"]).iloc[::-1])

    if st.sidebar.button("Logout 🚪"):
        st.session_state["auth_level"] = None
        st.rerun()
else:
    st.info("Willkommen Murat! Nutze die Sidebar zum Starten.")
