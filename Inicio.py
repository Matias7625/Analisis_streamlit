import pandas as pd
import streamlit as st
import numpy as np

st.set_page_config(
    page_title="Monitoreo Calidad del Aire - EAFIT (Robusto)",
    page_icon="🌿",
    layout="wide"
)

st.title("🌿 Monitoreo de Calidad del Aire - EAFIT (Loader robusto)")
st.markdown("Sube tu CSV exportado desde Influx/Telegraf/Flux — el cargador detecta columna de tiempo y valor automáticamente.")

uploaded_file = st.file_uploader("Cargar CSV", type=["csv"])

def detect_time_column(df):
    candidates = ['_time','Time','time','timestamp','_timestamp','_start','time_ns','time_us','time_ms']
    for c in candidates:
        if c in df.columns:
            return c
    # try heuristics: any column with 'time' or '_time' substring
    for c in df.columns:
        if 'time' in c.lower():
            return c
    # fallback: find first column with ISO-like strings or long integers
    for c in df.columns:
        # try to detect RFC3339 strings in a sample
        sample = df[c].astype(str).head(20)
        if sample.str.contains(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}').any():
            return c
    # numeric-looking timestamp column (big ints)
    for c in df.columns:
        if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c]):
            # check magnitude - epoch seconds, ms, us, ns
            s = df[c].dropna().astype(np.int64)
            if len(s)==0:
                continue
            median = int(s.median())
            # plausible epoch ranges
            if median > 1e9:  # could be seconds or ms/us/ns
                return c
    return None

def detect_value_column(df, time_col):
    # common names
    candidates = ['_value','value','val','_measurement','measurement','_field','reading']
    for c in candidates:
        if c in df.columns and c != time_col:
            return c
    # else pick a numeric column that's not time
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != time_col]
    if numeric_cols:
        return numeric_cols[0]
    return None

def convert_time_series(series):
    # Try parse as datetime strings first
    try:
        res = pd.to_datetime(series, utc=True)
        if res.notna().sum() > 0:
            return res
    except Exception:
        pass
    # If numeric, guess unit by magnitude:
    s = series.dropna().astype(np.int64)
    if len(s)==0:
        return pd.to_datetime(series, errors='coerce')
    median = int(s.median())
    # guess:
    # seconds since epoch ~ 1e9 (around year 2001+)
    # milliseconds ~ 1e12
    # microseconds ~ 1e15
    # nanoseconds ~ 1e18
    if median > 1e17:
        unit = 'ns'
    elif median > 1e14:
        unit = 'us'
    elif median > 1e11:
        unit = 'ms'
    elif median > 1e9:
        unit = 's'
    else:
        unit = 's'
    try:
        return pd.to_datetime(series, unit=unit, utc=True)
    except Exception:
        return pd.to_datetime(series, errors='coerce')

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Columnas detectadas en CSV:", list(df.columns))

        # detect time column
        time_col = detect_time_column(df)
        if time_col is None:
            st.error("No se pudo detectar automáticamente la columna de tiempo. Asegúrate que el CSV tenga una columna tipo `_time`, `timestamp`, `Time` o similar.")
            st.stop()

        value_col = detect_value_column(df, time_col)
        if value_col is None:
            st.error("No se pudo detectar automáticamente la columna de valor (sensor). Revisa columnas numéricas en el CSV.")
            st.stop()

        st.success(f"Columna de tiempo detectada: **{time_col}**  ·  Columna de valor detectada: **{value_col}**")

        # attempt conversion
        df['__parsed_time'] = convert_time_series(df[time_col])
        # if parsed_time has many NaT, try alternative (e.g., strip trailing Z)
        if df['__parsed_time'].isna().mean() > 0.5:
            # try without UTC coercion
            df['__parsed_time'] = pd.to_datetime(df[time_col], errors='coerce')

        # drop rows without valid time
        before = len(df)
        df = df.dropna(subset=['__parsed_time'])
        after = len(df)
        if after == 0:
            st.error("Después de convertir, no quedan filas con fecha válida. Revisa el formato de tiempo en el CSV.")
            st.stop()
        if after < before:
            st.warning(f"Se eliminaron {before-after} filas sin timestamp válido.")

        # rename and set index
        df = df.rename(columns={value_col: 'variable'})
        df = df.set_index(pd.DatetimeIndex(df['__parsed_time']).tz_convert(None))
        # keep only variable for plotting by default, but keep full DF available
        df_plot = df[['variable']].sort_index()

        st.write("Rango de tiempo de los datos:", df_plot.index.min(), "→", df_plot.index.max())
        st.write("Primeras filas procesadas:")
        st.dataframe(df_plot.head(10))

        # basic checks on variable: convert to numeric if needed
        df_plot['variable'] = pd.to_numeric(df_plot['variable'], errors='coerce')
        if df_plot['variable'].isna().all():
            st.error("La columna de valor detectada no contiene números válidos.")
            st.stop()

        # simple dashboard
        st.subheader("Monitoreo rápido")
        col1, col2, col3 = st.columns(3)
        current = df_plot['variable'].iloc[-1]
        avg = df_plot['variable'].mean()
        mx = df_plot['variable'].max()
        with col1:
            st.metric("Último valor", f"{current:.2f}")
        with col2:
            st.metric("Promedio", f"{avg:.2f}")
        with col3:
            st.metric("Máximo", f"{mx:.2f}")

        chart_type = st.selectbox("Gráfico", ["Línea", "Área", "Barra"])
        if chart_type == "Línea":
            st.line_chart(df_plot['variable'])
        elif chart_type == "Área":
            st.area_chart(df_plot['variable'])
        else:
            st.bar_chart(df_plot['variable'])

        if st.checkbox("Mostrar DataFrame completo procesado"):
            st.dataframe(df_plot)

    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
else:
    st.info("Sube un CSV exportado desde Influx/Telegraf/Flux. El cargador detecta `_time`/`_value`, timestamps RFC3339 o epoch en s/ms/us/ns.")
