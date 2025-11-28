import streamlit as st
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Generador de Reportes Meta", layout="wide")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Ingresa tu Gemini API Key", type="password")
    st.markdown("[Obtener API Key gratis](https://aistudio.google.com/app/apikey)")

# --- INTERFAZ PRINCIPAL ---
st.title("📊 Generador de Reportes: Desempeño en Redes Sociales")
st.markdown("Genera un informe formal y estructurado a partir de capturas de Meta Business Suite.")

# --- INPUTS ---
col1, col2 = st.columns(2)
with col1:
    motel_name = st.text_input("Nombre del Negocio", placeholder="Ej: Motel Dulce Boca")
with col2:
    period = st.text_input("Periodo del Reporte", placeholder="Ej: Octubre - Noviembre")

uploaded_files = st.file_uploader("Sube las evidencias (Capturas de pantalla)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

# --- LÓGICA ---
if st.button("Generar Reporte"):
    if not api_key or not uploaded_files or not motel_name or not period:
        st.warning("⚠️ Por favor completa todos los campos y la API Key.")
        st.stop()

    genai.configure(api_key=api_key)
    
    with st.spinner('Procesando datos y estructurando el informe...'):
        try:
            # 1. Preparar imágenes
            image_parts = []
            for uploaded_file in uploaded_files:
                image_parts.append({
                    "mime_type": uploaded_file.type,
                    "data": uploaded_file.getvalue()
                })

            # 2. Prompt Estricto (Actualizado)
            system_prompt = f"""
            You are a Professional Data Analyst. Analyze these Meta Business Suite screenshots.
            Generate a STRICT JSON object based on the requirements below.

            CONTEXT:
            Business: {motel_name}
            Period: {period}

            DATA EXTRACTION RULES:
            1. **Facebook & Instagram**: Extract Views (Visualizaciones), Reach (Alcance), Interactions (Interacciones), and Followers (Seguidores/Me gusta).
            2. **Messaging**: Extract ONLY "Total Contacts" (Contactos totales), "New Contacts" (Contactos nuevos), and "Response Time" (Tiempo de respuesta). IGNORE "Orders" or "Busiest Day".
            3. **Demographics**: Extract Gender % and Top Cities with their %.
            4. **Trends**: If a trend is negative (e.g., ▼ 20%), extract as negative number (-20). If positive, extract as positive.

            REQUIRED JSON STRUCTURE:
            {{
                "meta": {{ "business": "{motel_name}", "period": "{period}" }},
                "facebook": {{
                    "views": Number, "views_trend": Number,
                    "reach": Number, "reach_trend": Number,
                    "visits": Number, "visits_trend": Number,
                    "followers": Number, "followers_trend": Number
                }},
                "instagram": {{
                    "views": Number, "views_trend": Number,
                    "reach": Number, "reach_trend": Number,
                    "interactions": Number, "interactions_trend": Number,
                    "visits": Number, "visits_trend": Number
                }},
                "messaging": {{
                    "total_contacts": Number, "total_contacts_trend": Number,
                    "new_contacts": Number, "new_contacts_trend": Number,
                    "response_time": "String (e.g., '18s')"
                }},
                "demographics": {{
                    "men_pct": Number, "women_pct": Number,
                    "cities": [ {{ "name": "String", "pct": Number }} ]
                }}
            }}
            """

            # 3. Generar con Gemini 2.5 Flash
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([system_prompt, *image_parts])
            
            # 4. Limpiar JSON
            json_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(json_text)
            data['date_generated'] = datetime.now().strftime("%d/%m/%Y")

            # 5. Renderizar
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('report_template.html')
            html_output = template.render(data)
            
            # 6. Descarga
            st.success("¡Informe generado correctamente!")
            st.download_button(
                label="📥 Descargar Informe PDF (HTML)",
                data=html_output,
                file_name=f"Informe_{motel_name.replace(' ', '_')}.html",
                mime="text/html"
            )
            
        except Exception as e:
            st.error(f"Error: {e}")
