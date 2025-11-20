import pandas as pd
import streamlit as st
from PIL import Image
import numpy as np
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

# Campus location (EAFIT)
campus_location = pd.DataFrame({
    'lat': [6.1991],
    'lon': [-75.5786],
    'location': ['Universidad EAFIT']
})

# Display map
st.subheader("📍 Ubicación del Campus EAFIT - Medellín")
st.map(campus_location, zoom=16)

# File uploader
uploaded_file = st.file_uploader('Cargar datos del sensor ambiental (CSV)', type=['csv'])

if uploaded_file is not None:
    try:
        # Load and process data
        df1 = pd.read_csv(uploaded_file)

        # Renombrar columnas según el archivo real
        df1 = df1.rename(columns={
            'value': 'variable',
            'timestamp': 'Time'
        })

        # Convertir timestamp de epoch nanosegundos → datetime real
        df1['Time'] = pd.to_datetime(df1['Time'], unit='ns')

        # Usamos Time como índice para gráficas y análisis
        df1 = df1.set_index('Time')

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🌡 Monitoreo en Tiempo Real", 
                                          "📊 Análisis Ambiental", 
                                          "🔍 Filtros y Alertas", 
                                          "🏫 Información Institucional"])

        # ---------------- TAB 1 ----------------
        with tab1:
            st.subheader('Monitoreo de Calidad del Aire (CO₂ / COV / PM2.5)')

            col1, col2, col3 = st.columns(3)

            # Current value
            current_value = df1["variable"].iloc[-1]

            with col1:
                if current_value > 1200:
                    st.error(f"🚨 Valor actual: {current_value:.1f} ppm - NO SALUDABLE")
                elif current_value > 800:
                    st.warning(f"⚠ Valor actual: {current_value:.1f} ppm - ADVERTENCIA")
                else:
                    st.success(f"✅ Valor actual: {current_value:.1f} ppm - AIRE SANO")

            with col2:
                avg_value = df1["variable"].mean()
                st.metric("Promedio General", f"{avg_value:.1f} ppm")

            with col3:
                max_value = df1["variable"].max()
                st.metric("Valor Máximo Registrado", f"{max_value:.1f} ppm")

            # Chart selector
            chart_type = st.selectbox("Tipo de visualización", ["Línea", "Área", "Barra"])

            if chart_type == "Línea":
                st.line_chart(df1["variable"])
            elif chart_type == "Área":
                st.area_chart(df1["variable"])
            else:
                st.bar_chart(df1["variable"])

            if st.checkbox('Mostrar datos crudos del sensor'):
                st.write(df1)

        # ---------------- TAB 2 ----------------
        with tab2:
            st.subheader('Análisis de Calidad del Aire y Estadísticas Ambientales')

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

        # ---------------- TAB 3 ----------------
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
                filtrado_df_min = df1[df1["variable"] > min_val]
                st.dataframe(filtrado_df_min)

            with col2:
                max_val = st.slider(
                    'Filtrar valores máximos (ppm)',
                    min_value, max_value, mean_value, key="max_val"
                )
                filtrado_df_max = df1[df1["variable"] < max_val]
                st.dataframe(filtrado_df_max)

        # ---------------- TAB 4 ----------------
        with tab4:
            st.subheader("Información Institucional - Universidad EAFIT")

            col1, col2 = st.columns(2)

            with col1:
                st.write("### 📍 Contacto")
                st.write("- Departamento de Infraestructura")
                st.write("- 📞 Teléfono: +57 (4) 261 95 00")
                st.write("- 📧 Email: ambiente@eafit.edu.co")
                st.write("- Dirección: Carrera 49 #7 Sur-50, Medellín")

            with col2:
                st.write("### 🌿 Sistema de Calidad del Aire")
                st.write("- Sensores recomendados: SCD-41, CCS811, MQ-135")
                st.write("- Variables medidas: CO₂, COV, PM2.5")
                st.write("- Umbral saludable CO₂: < 800 ppm")
                st.write("- Advertencia: 800–1200 ppm")
                st.write("- Crítico: >1200 ppm")
                st.write("- Frecuencia de lectura: cada 1–5 min")

                st.write("### 📋 Protocolos ambientales")
                st.write("1. >1200 ppm: evacuar y aumentar ventilación")
                st.write("2. >800 ppm: abrir ventanas y revisar flujo de aire")
                st.write("3. Revisiones semanales de sensores")

    except Exception as e:
        st.error(f'Error al procesar archivo: {str(e)}')
else:
    st.info("""
    💡 *Instrucciones:*  
    - Cargue un archivo CSV con datos del sensor ambiental  
    - Debe incluir las columnas: value y timestamp  
    - El sistema los analizará automáticamente
    """)

# Footer
st.markdown("""
    ---
    *Sistema desarrollado para la Universidad EAFIT* 🌿  
    Monitoreo ambiental para asegurar espacios saludables · Medellín, Colombia · 2024  
""")

