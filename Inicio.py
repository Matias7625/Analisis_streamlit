import pandas as pd
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Monitoreo de Calidad del Aire - Universidad EAFIT",
    page_icon="🌿",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #f0f2f6;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title('🌿 Sistema de Monitoreo de Calidad del Aire - Universidad EAFIT')
st.markdown("""
    ### 🏫 Campus EAFIT - Medellín  
    Plataforma para analizar en tiempo real los niveles de gases ambientales (CO₂, COV, PM2.5)
    en salones, laboratorios y espacios comunes para garantizar un ambiente sano.
""")

# File uploader
uploaded_file = st.file_uploader('Cargar datos del sensor ambiental (CSV)', type=['csv'])

if uploaded_file is not None:
    try:
        # ============================
        # 🔧 1. CARGA Y CORRECCIÓN DE COLUMNAS
        # ============================

        df1 = pd.read_csv(uploaded_file)

        # Verificación obligatoria (solo para evitar errores inesperados)
        expected_columns = ['_value', '_time']
        for col in expected_columns:
            if col not in df1.columns:
                st.error(f"El archivo no contiene la columna obligatoria: {col}")
                st.stop()

        # Renombrar para que la app funcione
        df1 = df1.rename(columns={
            '_value': 'variable',
            '_time': 'Time'
        })

        # Convertir Time (formato RFC3339) a datetime
        df1['Time'] = pd.to_datetime(df1['Time'], errors='coerce')

        # Remover filas inválidas por si algún tiempo viene malo
        df1 = df1.dropna(subset=['Time'])

        # Establecer índice para gráficos
        df1 = df1.set_index('Time')

        # ============================
        # 🔧 2. TABS DE NAVEGACIÓN
        # ============================

        tab1, tab2, tab3, tab4 = st.tabs([
            "🌡 Monitoreo en Tiempo Real", 
            "📊 Análisis Ambiental", 
            "🔍 Filtros y Alertas", 
            "🏫 Información Institucional"
        ])

        # ==============================
        # TAB 1 - MONITOREO EN TIEMPO REAL
        # ==============================
        with tab1:
            st.subheader('Monitoreo de Calidad del Aire (CO₂ / COV / PM2.5)')

            col1, col2, col3 = st.columns(3)

            current_value = df1["variable"].iloc[-1]

            with col1:
                if current_value > 1200:
                    st.error(f"🚨 Actual: {current_value:.1f} ppm - NO SALUDABLE")
                elif current_value > 800:
                    st.warning(f"⚠ Actual: {current_value:.1f} ppm - ADVERTENCIA")
                else:
                    st.success(f"✅ Actual: {current_value:.1f} ppm - AIRE SANO")

            with col2:
                avg_value = df1["variable"].mean()
                st.metric("Promedio General", f"{avg_value:.1f} ppm")

            with col3:
                max_value = df1["variable"].max()
                st.metric("Valor Máximo Registrado", f"{max_value:.1f} ppm")

            # Selector gráfico
            chart_type = st.selectbox("Tipo de visualización", ["Línea", "Área", "Barra"])

            if chart_type == "Línea":
                st.line_chart(df1["variable"])
            elif chart_type == "Área":
                st.area_chart(df1["variable"])
            else:
                st.bar_chart(df1["variable"])

            if st.checkbox('Mostrar datos crudos del sensor'):
                st.dataframe(df1)

        # ==============================
        # TAB 2 - ANÁLISIS
        # ==============================
        with tab2:
            st.subheader('Análisis de Calidad del Aire')

            stats_df = df1["variable"].describe()

            col1, col2 = st.columns(2)

            with col1:
                st.write("#### Resumen Estadístico")
                st.dataframe(stats_df)

            with col2:
                st.write("#### Indicadores Ambientales (CO₂)")
                
                safety_threshold = 1200
                warning_threshold = 800
                
                high_readings = len(df1[df1["variable"] > safety_threshold])
                warning_readings = len(df1[df1["variable"] > warning_threshold])
                total_readings = len(df1)

                st.metric("Lecturas No Saludables (>1200 ppm)", f"{high_readings}")
                st.metric("Lecturas en Advertencia (>800 ppm)", f"{warning_readings}")
                st.metric("Tiempo de Aire Sano (%)", 
                         f"{(total_readings - high_readings)/total_readings*100:.1f}%")

        # ==============================
        # TAB 3 - FILTROS
        # ==============================
        with tab3:
            st.subheader('Filtros y Sistema de Alertas Ambientales')

            min_value = float(df1["variable"].min())
            max_value = float(df1["variable"].max())
            mean_value = float(df1["variable"].mean())

            st.write("### ⚠ Configuración de Alertas")
            alert_threshold = st.slider(
                'Umbral de alerta ambiental (ppm)',
                min_value=min_value,
                max_value=max_value,
                value=900.0,
                step=10.0
            )

            alert_count = len(df1[df1["variable"] > alert_threshold])
            st.info(f"Alertas activas: {alert_count} valores superan {alert_threshold} ppm")

            col1, col2 = st.columns(2)

            with col1:
                min_val = st.slider(
                    'Filtrar valores mínimos (ppm)',
                    min_value, max_value, mean_value, key="min_val"
                )
                st.dataframe(df1[df1["variable"] > min_val])

            with col2:
                max_val = st.slider(
                    'Filtrar valores máximos (ppm)',
                    min_value, max_value, mean_value, key="max_val"
                )
                st.dataframe(df1[df1["variable"] < max_val])

        # ==============================
        # TAB 4 - INFO
        # ==============================
        with tab4:
            st.subheader("Información Institucional - Universidad EAFIT")

            st.write("### 🌿 Sistema de Calidad del Aire")
            st.write("- Sensores compatibles: SCD-41, CCS811, MQ-135")
            st.write("- Variables medidas: CO₂, COV, PM2.5")
            st.write("- Umbrales recomendados para CO₂:")
            st.write("   - < 800 ppm — Nivel saludable")
            st.write("   - 800–1200 ppm — Advertencia")
            st.write("   - > 1200 ppm — Crítico")

    except Exception as e:
        st.error(f'Error al procesar archivo: {str(e)}')

else:
    st.info("""
    💡 *Instrucciones:*  
    - Cargue un archivo CSV con columnas `_value` y `_time`  
    - El sistema analizará automáticamente la calidad del aire  
    """)

