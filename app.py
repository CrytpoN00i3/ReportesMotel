import streamlit as st
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Generador de Reportes Meta", layout="wide")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    # La API Key solo es necesaria si usamos el modo de imágenes
    api_key = st.text_input("Ingresa tu Gemini API Key", type="password")
    st.markdown("[Obtener API Key gratis](https://aistudio.google.com/app/apikey)")

# --- INTERFAZ PRINCIPAL ---
st.title("📊 Generador de Reportes: Desempeño en Redes Sociales")
st.markdown("Genera un informe formal y estructurado.")

# --- SELECCIÓN DE MODO ---
mode = st.radio("Selecciona el método de entrada:", ["📸 Subir Imágenes (IA Automática)", "📝 Pegar JSON (Manual)"], horizontal=True)

# --- INPUTS COMUNES ---
col1, col2 = st.columns(2)
with col1:
    motel_name = st.text_input("Nombre del Negocio", placeholder="Ej: Motel Dulce Boca")
with col2:
    period = st.text_input("Periodo del Reporte", placeholder="Ej: Octubre - Noviembre")

# --- VARIABLES DE ESTADO ---
data = None
json_input = None
uploaded_files = None

# --- MODO 1: IMÁGENES ---
if mode == "📸 Subir Imágenes (IA Automática)":
    st.info("📱 **Tip Móvil:** Si la subida se congela, intenta seleccionar las fotos desde la opción 'Archivos'.")
    uploaded_files = st.file_uploader(
        "Sube las evidencias", 
        accept_multiple_files=True, 
        type=['jpg', 'jpeg', 'png', 'webp'],
        help="Selecciona todas las capturas necesarias."
    )
    
    # Feedback visual
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} imágenes cargadas en memoria.")

# --- MODO 2: JSON ---
elif mode == "📝 Pegar JSON (Manual)":
    st.info("Usa este modo si prefieres extraer los datos con otro chat (ChatGPT, Claude) y solo quieres generar el PDF.")
    json_input = st.text_area("Pega aquí el código JSON:", height=300, help="Asegúrate de que siga la estructura correcta.")
    
    with st.expander("Ver Estructura JSON Requerida (Copiar esto para el prompt)"):
        st.code("""
{
    "meta": { "business": "Nombre", "period": "Periodo" },
    "facebook": {
        "views": 0, "views_trend": 0,
        "reach": 0, "reach_trend": 0,
        "visits": 0, "visits_trend": 0,
        "followers": 0, "followers_trend": 0
    },
    "instagram": {
        "views": 0, "views_trend": 0,
        "reach": 0, "reach_trend": 0,
        "interactions": 0, "interactions_trend": 0,
        "visits": 0, "visits_trend": 0
    },
    "messaging": {
        "total_contacts": 0, "total_contacts_trend": 0,
        "new_contacts": 0, "new_contacts_trend": 0,
        "response_time": "0s"
    },
    "demographics": {
        "men_pct": 0, "women_pct": 0,
        "ages": [ { "range": "25-34", "pct": 0 } ],
        "cities": [ { "name": "Ciudad", "pct": 0 } ]
    }
}
        """, language='json')

# --- FUNCIÓN DE COMPRESIÓN SEGURA ---
def process_images_safe(files):
    processed = []
    for f in files:
        try:
            bytes_data = f.getvalue()
            processed.append({
                "mime_type": f.type if f.type != "application/octet-stream" else "image/jpeg",
                "data": bytes_data
            })
        except Exception as e:
            st.error(f"Error con el archivo {f.name}: {e}")
    return processed

# --- BOTÓN GENERAR ---
if st.button("Generar Reporte"):
    
    # VALIDACIONES SEGÚN MODO
    if mode == "📸 Subir Imágenes (IA Automática)":
        if not api_key:
            st.error("⚠️ Para usar IA necesitas la API Key.")
            st.stop()
        if not uploaded_files:
            st.warning("⚠️ Sube al menos una imagen.")
            st.stop()
            
        # PROCESAMIENTO IA
        genai.configure(api_key=api_key)
        with st.spinner('Conectando con Google Gemini 2.5...'):
            try:
                image_parts = process_images_safe(uploaded_files)
                
                system_prompt = f"""
                You are a Professional Data Analyst. Analyze these Meta Business Suite screenshots.
                Generate a STRICT JSON object.
                CONTEXT: Business: {motel_name}, Period: {period}
                RULES: 
                1. Extract numbers exactly. 
                2. Negative trends as negative numbers. 
                3. JSON format only.
                
                REQUIRED JSON STRUCTURE:
                {{
                    "meta": {{ "business": "{motel_name}", "period": "{period}" }},
                    "facebook": {{ "views": 0, "views_trend": 0, "reach": 0, "reach_trend": 0, "visits": 0, "visits_trend": 0, "followers": 0, "followers_trend": 0 }},
                    "instagram": {{ "views": 0, "views_trend": 0, "reach": 0, "reach_trend": 0, "interactions": 0, "interactions_trend": 0, "visits": 0, "visits_trend": 0 }},
                    "messaging": {{ "total_contacts": 0, "total_contacts_trend": 0, "new_contacts": 0, "new_contacts_trend": 0, "response_time": "0s" }},
                    "demographics": {{ "men_pct": 0, "women_pct": 0, "ages": [ {{ "range": "String", "pct": Number }} ], "cities": [ {{ "name": "String", "pct": Number }} ] }}
                }}
                """
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content([system_prompt, *image_parts])
                json_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(json_text)
                
            except Exception as e:
                st.error(f"Error de IA: {e}")
                st.stop()

    elif mode == "📝 Pegar JSON (Manual)":
        if not json_input:
            st.warning("⚠️ Pega el código JSON primero.")
            st.stop()
        try:
            data = json.loads(json_input)
            # Sobreescribir metadatos con los inputs de texto para asegurar consistencia
            if motel_name: data['meta']['business'] = motel_name
            if period: data['meta']['period'] = period
        except json.JSONDecodeError:
            st.error("❌ El texto pegado no es un JSON válido. Revisa las comillas o corchetes.")
            st.stop()

    # --- RENDERIZADO DEL REPORTE (COMÚN) ---
    if data:
        try:
            data['date_generated'] = datetime.now().strftime("%d/%m/%Y")
            
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('report_template.html')
            html_output = template.render(data)
            
            st.success("¡Informe generado correctamente!")
            
            # Botón de Descarga
            file_label = f"Informe_{data['meta']['business'].replace(' ', '_')}.html"
            st.download_button(
                label="📥 Descargar Informe PDF (HTML)",
                data=html_output,
                file_name=file_label,
                mime="text/html"
            )
        except Exception as e:
            st.error(f"Error al generar el HTML: {e}")
