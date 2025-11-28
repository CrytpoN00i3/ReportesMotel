import streamlit as st
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Generador de Reportes Analytics", layout="wide")

# --- BARRA LATERAL: API KEY ---
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Ingresa tu Gemini API Key", type="password")
    st.markdown("[Obtener API Key gratis](https://aistudio.google.com/app/apikey)")
    st.info("Nota: Este script usa el modelo 'gemini-2.5-flash'. Asegúrate de que tu API Key tenga acceso.")

# --- INTERFAZ PRINCIPAL ---
st.title("📊 Generador de Reportes PDF Automático")
st.markdown("Crea reportes profesionales a partir de capturas de pantalla de Meta Business Suite.")

# --- INPUTS DEL USUARIO (NOMBRE Y PERIODO) ---
st.subheader("1. Detalles del Reporte")
col1, col2 = st.columns(2)

with col1:
    # Aquí el usuario escribe el nombre del motel
    motel_name = st.text_input("Nombre del Negocio / Motel", value="", placeholder="Ej: Motel Dulce Boca")

with col2:
    # Aquí el usuario escribe el periodo (fechas)
    period = st.text_input("Periodo del Reporte", value="", placeholder="Ej: Octubre - Noviembre 2025")

# --- SUBIDA DE IMÁGENES ---
st.subheader("2. Subir Evidencias")
uploaded_files = st.file_uploader(
    "Sube tus capturas de pantalla (JPG, PNG)", 
    accept_multiple_files=True, 
    type=['jpg', 'jpeg', 'png']
)

# --- LÓGICA DE GENERACIÓN ---
if st.button("Generar Reporte"):
    
    # Validaciones previas
    if not api_key:
        st.warning("⚠️ Por favor ingresa tu API Key en la barra lateral izquierda.")
        st.stop()
    
    if not uploaded_files:
        st.warning("⚠️ Por favor sube al menos una captura de pantalla.")
        st.stop()
        
    if not motel_name or not period:
        st.warning("⚠️ Por favor completa el Nombre del Negocio y el Periodo.")
        st.stop()

    # Configurar API
    genai.configure(api_key=api_key)
    
    with st.spinner(f'Analizando imágenes para {motel_name}... (Modelo: Gemini 2.5 Flash)'):
        try:
            # 1. Preparar imágenes para la API
            image_parts = []
            for uploaded_file in uploaded_files:
                bytes_data = uploaded_file.getvalue()
                image_parts.append({
                    "mime_type": uploaded_file.type,
                    "data": bytes_data
                })

            # 2. El Prompt Maestro
            # Pasamos las variables motel_name y period al prompt para que la IA sepa el contexto
            system_prompt = f"""
            You are a Data Extraction Bot. Analyze these screenshots of Meta Business Suite analytics.
            Aggregate data into a single JSON object.
            
            CONTEXT:
            Business Name: {motel_name}
            Report Period: {period}
            
            RULES:
            1. Extract the exact numbers found in the images.
            2. If a metric shows a negative trend (e.g., "▼ 39.9%"), extract the value as a negative number (-39.9).
            3. If a metric shows a positive trend, extract it as positive.
            4. If a metric is NOT found in any screenshot, use 0.
            5. Return ONLY valid JSON. No markdown formatting (no ```json).
            
            REQUIRED JSON STRUCTURE:
            {{
                "report_metadata": {{ 
                    "motel_name": "{motel_name}", 
                    "period": "{period}" 
                }},
                "facebook": {{
                    "views": Number (integer),
                    "views_trend": Number (float),
                    "reach": Number (integer),
                    "reach_trend": Number (float),
                    "visits": Number (integer),
                    "visits_trend": Number (float)
                }},
                "instagram": {{
                    "views": Number (integer),
                    "views_trend": Number (float),
                    "interactions": Number (integer),
                    "interactions_trend": Number (float)
                }},
                "demographics": {{
                    "gender": {{ 
                        "men_percentage": Number, 
                        "women_percentage": Number 
                    }},
                    "top_cities": [ 
                        {{ "city": "String", "percentage": Number }} 
                    ]
                }}
            }}
            """

            # 3. Llamada a la API (Modelo Actualizado)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = model.generate_content([system_prompt, *image_parts])
            
            # 4. Limpieza de la respuesta
            json_text = response.text.replace('```json', '').replace('```', '').strip()
            
            # Debug (opcional): ver qué devolvió la IA en bruto si falla el JSON
            # st.write(json_text) 
            
            data = json.loads(json_text)
            
            # 5. Renderizar HTML
            # Añadimos la fecha de generación automática
            data['generation_date'] = datetime.now().strftime("%d/%m/%Y")
            
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('report_template.html')
            
            html_output = template.render(data)
            
            # 6. Éxito y Descarga
            st.success("¡Reporte generado con éxito!")
            st.markdown(f"**Negocio:** {motel_name} | **Periodo:** {period}")
            
            # Botón de Descarga
            st.download_button(
                label="📥 Descargar Reporte HTML (Para guardar como PDF)",
                data=html_output,
                file_name=f"Reporte_{motel_name.replace(' ', '_')}_{period.replace(' ', '_')}.html",
                mime="text/html"
            )
            
            # Vista previa de los datos extraídos
            with st.expander("Ver datos extraídos (JSON)"):
                st.json(data)

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
            st.info("Intenta nuevamente. Si el error persiste, verifica que las imágenes sean claras y tu API Key sea correcta.")
