import pandas as pd
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Monitoreo de Calidad del Aire - Universidad EAFIT",
    page_icon="🌿",
    layout="wide"
)

# Header
st.title("🌿 Sistema de Monitoreo de Calidad del Aire - Universidad EAFIT")
st.markdown("""
    ### 🏫 Análisis de sensores ambientales exportados desde InfluxDB  
    Compatible con archivos CSV que incluyen `_time` y `_value`.
""")

# File uploader
uploaded_file = st.file_uploader("📂 Cargar archivo CSV exportado desde InfluxDB", type=["csv"])

if uploaded_file is not None:
    try:
        # ============================
        # 1. CARGA DEL ARCHIVO CSV
        # ============================
        df = pd.read_csv(uploaded_file)

        # ============================
        # 2. VALIDACIÓN DE COLUMNAS
        # ============================
        required_columns = ["_time", "_value"]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"❌ El archivo no contiene la columna obligatoria: {col}")
                st.stop()

        # ============================
        # 3. RENOMBRAR COLUMNAS
        # ============================
        df = df.rename(columns={
            "_time": "Time",
            "_value": "variable"
        })

        # ============================
        # 4. CONVERTIR TIME A DATETIME
        # ============================
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

        # Eliminar filas sin fecha válida
        df = df.dropna(subset=["Time"])

        # Ordenar por tiempo
        df = df.sort_values("Time")

        # Usar como índice
        df = df.set_index("Time")

        # ============================
        # 5. MOSTRAR PREVISUALIZACIÓN
        # ============================
        st.success("✅ Archivo cargado correctamente")
        st.write("Columnas detectadas:", list(df.columns))
        st.dataframe(df.head())

        # ============================
        # 6. DASHBOARD
        # ============================

        tab1, tab2, tab3 = st.tabs(["📈 Monitoreo", "📊 Estadísticas", "🚨 Alertas"])

        # -----------------------------------------
        # TAB 1 - MONITOREO
        # -----------------------------------------
        with tab1:
            st.subheader("📈 Monitoreo en tiempo real")

            current_value = df["variable"].iloc[-1]
            avg_value = df["variable"].mean()
            max_value = df["variable"].max()

            col1, col2, col3 = st.columns(3)
            col1.metric("Valor actual", f"{current_value:.2f}")
            col2.metric("Promedio", f"{avg_value:.2f}")
            col3.metric("Máximo registrado", f"{max_value:.2f}")

            # Gráfico
            st.line_chart(df["variable"])

        # -----------------------------------------
        # TAB 2 - ESTADÍSTICAS
        # -----------------------------------------
        with tab2:
            st.subheader("📊 Estadísticas del sensor")
            st.dataframe(df["variable"].describe())

        # -----------------------------------------
        # TAB 3 - ALERTAS
        # -----------------------------------------
        with tab3:
            st.subheader("🚨 Sistema de alertas ambientales")

            threshold = st.slider("Nivel crítico", min_value=float(df["variable"].min()),
                                  max_value=float(df["variable"].max()),
                                  value=float(df["variable"].mean()))

            alerts = df[df["variable"] > threshold]
            st.warning(f"Alertas detectadas: {len(alerts)}")

            st.dataframe(alerts)

    except Exception as e:
        st.error(f"⚠ Error al procesar archivo: {str(e)}")

else:
    st.info("💡 Cargue un archivo CSV con columnas `_time` y `_value` exportado desde InfluxDB.")

