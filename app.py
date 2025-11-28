import streamlit as st
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime
from PIL import Image

# --- CONFIGURATION ---
# Page Config
st.set_page_config(page_title="Generador de Reportes Analytics", layout="wide")

# Sidebar for API Key
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Ingresa tu Gemini API Key", type="password")
    st.markdown("[Obtener API Key gratis](https://aistudio.google.com/app/apikey)")

# --- MAIN UI ---
st.title("📊 Generador de Reportes PDF Automático")
st.markdown("Sube capturas de pantalla de Meta Business Suite y obtén un reporte profesional listo para imprimir.")

col1, col2 = st.columns(2)
with col1:
    motel_name = st.text_input("Nombre del Negocio / Motel", value="Motel Dulce Boca")
with col2:
    period = st.text_input("Periodo del Reporte", value="Octubre - Noviembre")

uploaded_files = st.file_uploader("Sube tus capturas de pantalla (JPG, PNG)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

# --- LOGIC ---
if st.button("Generar Reporte") and uploaded_files and api_key:
    genai.configure(api_key=api_key)
    
    with st.spinner('Analizando imágenes y extrayendo datos con IA...'):
        try:
            # 1. Prepare Images for API
            image_parts = []
            for uploaded_file in uploaded_files:
                bytes_data = uploaded_file.getvalue()
                image_parts.append({
                    "mime_type": uploaded_file.type,
                    "data": bytes_data
                })

            # 2. Define the Prompt (The Brain)
            system_prompt = f"""
            You are a Data Extraction Bot. Analyze these screenshots of Meta Business Suite analytics.
            Aggregate data into a single JSON. 
            
            CONTEXT:
            Business Name: {motel_name}
            Period: {period}
            
            RULES:
            1. If a metric shows a negative trend (e.g., "▼ 39.9%"), extract the value as a negative number (-39.9).
            2. If a metric is missing, use 0.
            3. Return ONLY valid JSON. No markdown formatting.
            
            REQUIRED JSON STRUCTURE:
            {{
                "report_metadata": {{ "motel_name": "{motel_name}", "period": "{period}" }},
                "facebook": {{
                    "views": Number (int),
                    "views_trend": Number (float),
                    "reach": Number (int),
                    "reach_trend": Number (float),
                    "visits": Number (int),
                    "visits_trend": Number (float)
                }},
                "instagram": {{
                    "views": Number (int),
                    "views_trend": Number (float),
                    "interactions": Number (int),
                    "interactions_trend": Number (float)
                }},
                "demographics": {{
                    "gender": {{ "men_percentage": Number, "women_percentage": Number }},
                    "top_cities": [ {{ "city": "String", "percentage": Number }} ]
                }}
            }}
            """

            # 3. Call Gemini API
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content([system_prompt, *image_parts])
            
            # 4. Clean and Parse JSON
            json_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(json_text)
            
            # 5. Render HTML
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('report_template.html')
            
            # Add generation date
            data['generation_date'] = datetime.now().strftime("%d/%m/%Y")
            
            html_output = template.render(data)
            
            # 6. Display & Download
            st.success("¡Datos extraídos correctamente!")
            
            # Show Preview
            st.subheader("Vista Previa de Datos")
            st.json(data)
            
            # Download Button
            st.download_button(
                label="📥 Descargar Reporte HTML (Imprimir como PDF)",
                data=html_output,
                file_name=f"Reporte_{motel_name.replace(' ', '_')}.html",
                mime="text/html"
            )
            
            st.info("💡 **Tip:** Abre el archivo HTML descargado y usa **Ctrl+P (Guardar como PDF)** para obtener el documento final.")

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
            st.error("Asegúrate de que tu API Key sea válida y las imágenes sean legibles.")

elif st.button("Generar Reporte") and not api_key:
    st.warning("Por favor ingresa tu API Key en la barra lateral.")
