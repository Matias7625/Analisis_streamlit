# app_eafit.py
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
import os

# ---- Config ----
CSV_DEFAULT_PATH = "/mnt/data/influxdata_2025-11-20T18_41_01Z.csv"  # <-- archivo que subiste
PAGE_TITLE = "Monitoreo de Calidad del Aire - Universidad EAFIT"
PAGE_ICON = "🌿"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 1.5rem; background-color: #f7f9fb; }
    .metric-card { background: #fff; padding: 12px; border-radius:10px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
    .small { font-size:0.9rem; color:#6c757d; }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 Sistema de Monitoreo de Calidad del Aire — Universidad EAFIT")
st.markdown("Plataforma para analizar en tiempo real niveles ambientales (ej. CO₂, COV, PM2.5) en espacios del campus.")

# Campus map
campus_location = pd.DataFrame({'lat':[6.1991], 'lon':[-75.5786], 'location':['Universidad EAFIT']})
st.subheader("📍 Ubicación: Campus EAFIT - Medellín")
st.map(campus_location, zoom=15)

# File upload OR read default CSV
st.subheader("🔁 Fuente de datos")
uploaded_file = st.file_uploader("Cargar CSV desde tu computador (opcional). Si no cargas nada, se usará el CSV por defecto del servidor.", type=["csv"])

use_default = False
if uploaded_file is None:
    if os.path.exists(CSV_DEFAULT_PATH):
        st.info(f"Usando archivo por defecto: `{CSV_DEFAULT_PATH}`")
        try:
            df_raw = pd.read_csv(CSV_DEFAULT_PATH)
            use_default = True
        except Exception as e:
            st.error(f"No se pudo leer el CSV por defecto: {e}")
            st.info("Carga manualmente el CSV usando el botón de arriba.")
            st.stop()
    else:
        st.info("No se cargó archivo y no se encontró CSV por defecto en el servidor. Cargue un archivo CSV.")
        st.stop()
else:
    try:
        df_raw = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error leyendo el CSV cargado: {e}")
        st.stop()

# ---- Auto-detección de columnas ----
def detect_time_col(df):
    candidates = ['time','Time','timestamp','Timestamp','date','Date','datetime','DateTime','_time']
    for c in candidates:
        if c in df.columns:
            return c
    # try to find column with datetime-like content
    for c in df.columns:
        sample = df[c].dropna().astype(str).iloc[:10].tolist()
        # quick heuristic: presence of "T" ISO or "-" and ":" for time
        if any(("T" in s and "-" in s) or (":" in s and "-" in s) or ("/" in s and ":" in s) for s in sample):
            return c
    return None

def detect_value_col(df, exclude_cols):
    # common names
    candidates = ['value','Value','valor','variable','mean','_value','field_value','measurement_value']
    for c in candidates:
        if c in df.columns and c not in exclude_cols:
            return c
    # fallback: numeric column with most non-null values
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    numeric_cols = [c for c in numeric_cols if c not in exclude_cols]
    if not numeric_cols:
        # try converting
        for c in df.columns:
            try:
                pd.to_numeric(df[c].dropna().iloc[:5])
                return c
            except Exception:
                continue
    if numeric_cols:
        # choose column with most non-null
        nonnull_counts = [(c, df[c].notnull().sum()) for c in numeric_cols]
        nonnull_counts.sort(key=lambda x: x[1], reverse=True)
        return nonnull_counts[0][0]
    return None

time_col = detect_time_col(df_raw)
value_col = detect_value_col(df_raw, exclude_cols=[time_col] if time_col else [])

st.write("**Detección automática de columnas**")
st.write(f"- Columna de tiempo detectada: `{time_col}`" if time_col else "- No se detectó columna de tiempo automáticamente.")
st.write(f"- Columna de valor detectada: `{value_col}`" if value_col else "- No se detectó columna de valor automáticamente.")

# If detection unsure, let user pick
if (time_col is None) or (value_col is None):
    st.warning("Selecciona manualmente las columnas si la detección automática no fue correcta.")
    cols = list(df_raw.columns)
    if time_col is None:
        time_col = st.selectbox("Selecciona la columna que contiene la marca temporal (Time / timestamp):", options=["(ninguna)"] + cols)
        if time_col == "(ninguna)":
            time_col = None
    if value_col is None:
        value_col = st.selectbox("Selecciona la columna que contiene la medición (valor):", options=["(ninguna)"] + cols)
        if value_col == "(ninguna)":
            value_col = None

if time_col is None or value_col is None:
    st.error("No fue posible identificar columnas de tiempo y/o valor. Revise el CSV y vuelva a intentar.")
    st.stop()

# Build df
df = df_raw.copy()
# Normalize columns
df = df.rename(columns={time_col: 'Time', value_col: 'variable'})

# Parse Time
try:
    df['Time'] = pd.to_datetime(df['Time'], infer_datetime_format=True, utc=False, errors='coerce')
except Exception:
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

if df['Time'].isna().all():
    st.error("La columna de tiempo no contiene valores convertibles a datetime. Verifique el formato.")
    st.stop()

df = df.set_index('Time').sort_index()
# Ensure variable numeric
df['variable'] = pd.to_numeric(df['variable'], errors='coerce')

if df['variable'].isna().all():
    st.error("La columna de valor no contiene números convertibles. Verifique el CSV.")
    st.stop()

# --- Aplicación principal ---
tab1, tab2, tab3, tab4 = st.tabs(["🌡 Monitoreo en Tiempo Real", "📊 Análisis Ambiental", "🔍 Filtros y Alertas", "🏫 Información EAFIT"])

# thresholds (ejemplo CO2 en ppm)
GOOD_THRESHOLD = 800
WARN_THRESHOLD = 1200

with tab1:
    st.subheader("Monitoreo — Últimos registros")
    latest = df["variable"].dropna().iloc[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        if latest > WARN_THRESHOLD:
            st.error(f"🚨 Valor actual: {latest:.1f} ppm — NO SALUDABLE")
        elif latest > GOOD_THRESHOLD:
            st.warning(f"⚠ Valor actual: {latest:.1f} ppm — ADVERTENCIA")
        else:
            st.success(f"✅ Valor actual: {latest:.1f} ppm — AIRE SANO")
    with col2:
        avg = df["variable"].mean()
        st.metric("Promedio", f"{avg:.1f} ppm")
    with col3:
        mx = df["variable"].max()
        mn = df["variable"].min()
        st.metric("Máx / Mín", f"{mx:.1f} / {mn:.1f} ppm")

    chart_type = st.selectbox("Tipo de visualización", ["Línea","Área","Barra"])
    if chart_type == "Línea":
        st.line_chart(df["variable"])
    elif chart_type == "Área":
        st.area_chart(df["variable"])
    else:
        st.bar_chart(df["variable"])

    if st.checkbox("Mostrar datos crudos"):
        st.dataframe(df.reset_index().tail(500))

with tab2:
    st.subheader("Análisis y Estadísticas")
    stats = df["variable"].describe().to_frame(name="value")
    st.dataframe(stats)

    total = len(df)
    high = (df["variable"] > WARN_THRESHOLD).sum()
    warn = ((df["variable"] > GOOD_THRESHOLD) & (df["variable"] <= WARN_THRESHOLD)).sum()
    safe = (df["variable"] <= GOOD_THRESHOLD).sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Lecturas No Saludables (>1200 ppm)", f"{high}", delta=f"{(high/total*100):.1f}%")
    c2.metric("Lecturas Advertencia (800-1200 ppm)", f"{warn}", delta=f"{(warn/total*100):.1f}%")
    c3.metric("Lecturas Saludables (<=800 ppm)", f"{safe}", delta=f"{(safe/total*100):.1f}%")

    st.markdown("### Distribución")
    st.hist_chart = st.download_button  # avoid linter warning
    st.bar_chart(df["variable"].resample("1H").mean().fillna(method="ffill"))

with tab3:
    st.subheader("Filtros y Alertas")
    min_v = float(df["variable"].min())
    max_v = float(df["variable"].max())
    mean_v = float(df["variable"].mean())

    alert_threshold = st.slider("Umbral de alerta (ppm)", min_value=min_v, max_value=max_v, value=(GOOD_THRESHOLD+WARN_THRESHOLD)/2.0, step=1.0)
    alert_count = (df["variable"] > alert_threshold).sum()
    st.info(f"Lecturas por encima del umbral: {alert_count}")

    colA, colB = st.columns(2)
    with colA:
        min_filter = st.number_input("Filtrar por mínimo (ppm)", value=float(mean_v))
        df_min = df[df["variable"] > min_filter]
        st.write(f"Registros con valor > {min_filter:.1f} ppm: {len(df_min)}")
        if st.button("Descargar filtrado (mín)"):
            csv = df_min.reset_index().to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV (mín)", data=csv, file_name="filtrado_min.csv", mime="text/csv")
    with colB:
        max_filter = st.number_input("Filtrar por máximo (ppm)", value=float(max_v), step=1.0)
        df_max = df[df["variable"] < max_filter]
        st.write(f"Registros con valor < {max_filter:.1f} ppm: {len(df_max)}")
        if st.button("Descargar filtrado (máx)"):
            csv = df_max.reset_index().to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV (máx)", data=csv, file_name="filtrado_max.csv", mime="text/csv")

with tab4:
    st.subheader("Información Institucional — Universidad EAFIT")
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Contacto")
        st.write("- Departamento de Infraestructura y Ambiente — EAFIT")
        st.write("- 📞 +57 (4) 261 95 00")
        st.write("- 📧 ambiente@eafit.edu.co")
    with col2:
        st.write("### Recomendaciones y sensores")
        st.write("- Sensores sugeridos: SCD-41, Sensirion, MQ-135 (COV), PMS7003 (PM2.5)")
        st.write("- Umbrales CO₂ (ejemplo): <800ppm sano, 800–1200ppm advertencia, >1200ppm crítico")
        st.write("- Acción: Ventilar, revisar extracción y aforo, calibrar sensores cada mes.")

# Footer
st.markdown("---")
st.markdown("Sistema adaptado para Universidad EAFIT · Monitorización ambiental · Script automático lee el CSV `/mnt/data/influxdata_2025-11-20T18_41_01Z.csv` si está disponible.")
