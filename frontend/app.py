import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as components
import requests
import time

API_DETECTAR_IDIOMA = "http://127.0.0.1:8000/api/detectar_idioma"
API_ANALIZAR = "http://127.0.0.1:8000/api/analizar"

# ---------- CONFIG ----------
st.set_page_config(                 #Define el título de la página y su icono en la pestaña del navegador (modificable)
    page_title="Proyecto Verid.IA",
    page_icon="✔",
    layout="wide"
)

# ---------- CSS ----------  
# Código encargado del diseño (colores, tipo de celda, botones, área de texto) de la web en ese orden, formato html, botón principal
st.markdown("""     
<style>

.main {
    background-color: #white;  #crema, si no gusta se puede cambiar a blanco
}

.block-container {
    padding-top: 2rem;
}

.stButton>button {
    background-color: #b6c35d; /* botón verde */
    color: #000000; 
    border-radius: 10px;
    padding: 10px 20px; /* más grande */
    font-weight: bold;
    font-size: 16px; /* aumenta tamaño del texto */
}

textarea {
    border-radius:10px !important;
}

div[data-modal-container="true"] [data-testid="baseButton-secondary"] {
    display: none !important;
}

</style>
""", unsafe_allow_html=True)

# ---------- FUNCIÓN API ----------
def llamar_api(endpoint, data, files=None):
    try:
        response = requests.post(endpoint, data=data, files=files)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

# ---------- IDIOMAS ----------
languages = {       #Los idiomas seleccionables en el desplegable
    "🇪🇸 Español": "es",
    "🇬🇧 English": "en",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
    "🇮🇹 Italiano": "it",
    "🇵🇹 Português": "pt",
    "🇷🇺 Русский": "ru",
    "🇸🇦 العربية": "ar",
    "🇷🇴 Română": "ro",
    "🇳🇱 Neerlandés": "nl",
    "🇨🇦 Catalán": "ca",
    "🇵🇱 Polaco": "pl",
    "🇺🇦 Ucraniano": "uk",
}

languages_input = {     #La traducción de todos los elementos visibles por pantalla a los demás idiomas (faltan idiomas)
    "Español": {
        "text_label": "Texto del anuncio",
        "url_label": "URL del anuncio",
        "imagen_label": "Imagen del anuncio",
        "anuncio_label": "Analizar anuncio",
        "file_label": "Sube una imagen del anuncio",
        "func_label": "Introduce un anuncio para detectar posibles fraudes.",
        "info_label": "Detecta anuncios de trabajo potencialmente fraudulentos. Puede elegir una de las siguientes tres opciones (Copiar Texto / Copiar URL / Subir una imagen) para comprobarlo.",
        "info_anuncio_label": "Información del anuncio",
        "copiar_label": "Copia aquí tu anuncio (Texto/URL/Imagen)",
        "previa_label": "Vista previa",
        "info_imagen_label": "Sube una imagen para verla aquí",
        "borrar_texto_label": "Borrar texto",
        "borrar_url_label": "Borrar URL",
        "spinner_label": "Analizando anuncio...",
        "mode_label": "Seleccione un modo de uso",
        "mode_label_one": "Analizar anuncio",
        "mode_label_two": "Mostrar estadísticas"

    },
    "English": {
        "text_label": "Advertisement's text",
        "url_label": "Advertisement URL",
        "imagen_label": "Advertisement image",
        "anuncio_label": "Analyse advertisement",
        "file_label": "Upload image of advertisement to view it here",
        "func_label": "Insert an advertisement to detect potential fraud.",
        "info_label": "Detects potentially fraudulent job postings. You may select one of the following three options (Copy Text / Copy URL / Upload an image) to verify this.",
        "info_anuncio_label": "Advertisement´s information",
        "copiar_label": "Paste your advertisement here (Text/URL/Image)",
        "previa_label": "Preview",
        "info_imagen_label": "Upload an image to view it here",
        "borrar_texto_label": "Erase text",
        "borrar_url_label": "Erase URL",
        "spinner_label": "Analysing advertisement...",
        "mode_label": "Select a usage mode",
        "mode_label_one": "Analyse advertisement",
        "mode_label_two": "Show statistics"

    },
    "Français": {
        "text_label": "Texte de l'annonce",
        "url_label": "URL de l'annonce",
        "imagen_label": "Image de l'annonce",
        "anuncio_label": "Analyser l'annonce",
        "file_label": "Télécharger image de l'annonce pour la voir ici",
        "func_label": "Insérer un annonce pour détecter les fraudes potentielles.",
        "info_label": "Détecte les offres d'emploi potentiellement frauduleuses. Vous pouvez choisir l'une des trois options suivantes (Copier le texte / Copier l'URL / Télécharger une image) pour le vérifier.",
        "info_anuncio_label": "Information de l'annonce",
        "copiar_label": "Copiez ici votre annonce (texte/URL/image)",
        "previa_label": "Aperçu",
        "info_imagen_label": "Téléchargez une image pour la voir ici",
        "borrar_texto_label": "Effacer texte",
        "borrar_url_label": "Effacer URL",
        "spinner_label": "Analyse de l'annonce...",
        "mode_label": "Sélectionnez un mode d'utilisation",
        "mode_label_one": "Analyser l'annonce",
        "mode_label_two": "Afficher les statistiques"

    }
}

# ---------- TEXTOS RESULTADO ----------
UI_TEXTS = {    #Diccionario que recoje los resultados que vería el usuario por pantalla dependiendo del idioma que haya seleccionado (falta rellenar más)
    "es":{
        "result":" ✔ Resultado del análisis",
        "spanish_only_error": "Solo se permiten anuncios en español. Inténtalo de nuevo.",
        "data": "Introduce texto, url o sube una imagen", #MODIFICADO
        "data_add": "Solo puedes introducir una opción: texto, URL o imagen", #EXTRA
        "mode": "Detectar Idioma / Traducción",
        "lang_phrase": "Idioma detectado",
        "valid_phrase": "Texto válido para análisis",
        "original_phrase": "Texto original",
        "translated_phrase": "Texto traducido",
        "message": "Mensaje",
        "indicator": "Indicadores detectados",
        "trust": "Confianza",
        "green": "Riesgo bajo",
        "yellow": "Riesgo medio",
        "red": "Riesgo alto",
        "close": "Entendido", #EXTRA
        "detect": "Mostrar Detección/Traducción"  #EXTRA


    },
    "en":{
        "result":" ✔ Analysis Result",
        "spanish_only_error": "Only advertisements in Spanish are allowed. Try again.",
        "data": "Enter text, url or upload an image",
        "data_add": "You can only enter one option: text, URL or image",  
        "mode": "Detect Language / Translation",
        "lang_phrase": "Language detected",
        "valid_phrase": "Text suitable for analysis",
        "original_phrase": "Original text",
        "translated_phrase": "Translated text",
        "message": "Message",
        "indicator": "Indicators detected",
        "trust": "Trust",
        "green": "Low risk",
        "yellow": "Medium risk",
        "red": "High risk",
        "close": "Understood",
        "detect": "Check Detection/Translation"
    },
    "fr":{
        "result":" ✔ Résultat de l'analyse",
        "spanish_only_error": "Seules les annonces en espagnol sont autorisées. Réessayez.",
        "data": "Saisissez du texte, une URL ou téléchargez une image",
        "data_add": "Vous ne pouvez saisir qu'un seul élément : du texte, une URL ou une image",  
        "mode": "Détection de la langue / Traduction",
        "lang_phrase": "Langue détectée",
        "valid_phrase": "Texte valable pour l'analyse",
        "original_phrase": "Texte original",
        "translated_phrase": "Texte traduit",
        "message": "Message",
        "indicator": "Indicateurs détectés",
        "trust": "Confiance",
        "green": "Risque faible",
        "yellow": "Risque moyen",
        "red": "Risque élevé ",
        "close": "Compris",
        "detect": "Vérifier Détection/Traduction"
    }
}
translations = {  #Diccionario y funcion para traducir el mensaje desde el backend
    "es": {
        "valid": "El texto es en español ({idioma}) y es analizable.",
        "invalid": "Idioma no soportado. El idioma detectado es ({idioma}). Solo se admite español (es)."
    },
    "en": {
        "valid": "The text is in Spanish ({idioma}) and can be analyzed.",
        "invalid": "Unsupported language. The detected language is ({idioma}). Only Spanish (es) is allowed."
    },
    "fr": {
        "valid": "Le texte est en espagnol ({idioma}) et peut être analysé.",
        "invalid": "Langue non prise en charge. La langue détectée est ({idioma}). Seul l'espagnol (es) est autorisé."
    }
}
def traducir_mensaje(lang, idioma_detectado, es_analizable):
    key = "valid" if es_analizable else "invalid"
    
    texto = translations.get(lang, translations["en"])[key]
    return texto.format(idioma=idioma_detectado)

translations_analisis = {  #Diccionario y funcion para traducir el mensaje desde el backend
    "es": {
        "valid": "El anuncio requiere atención debido a posibles riesgos.",
        "invalid": "Idioma no soportado. El idioma detectado es ({idioma}). Solo se admite español (es)."
    },
    "en": {
        "valid": "This advertisement requires your attention due to potential risks.",
        "invalid": "Unsupported language. The detected language is ({idioma}). Only Spanish (es) is allowed."
    },
    "fr": {
        "valid": "Cette annonce mérite votre attention en raison des risques potentiels qu'elle comporte.",
        "invalid": "Langue non prise en charge. La langue détectée est ({idioma}). Seul l'espagnol (es) est autorisé."
    }
}
def traducir_mensaje_analisis(lang, idioma_detectado):  
    key = "invalid" if idioma_detectado != "es" else "valid"
    
    texto = translations_analisis.get(lang, translations_analisis["en"])[key]
    return texto.format(idioma=idioma_detectado)

def semaforo(nivel=None):  #FUNCION PARA LOS COLORES DEL SEMÁFORO DE DENTRO DEL ANÁLISIS (EL SEMÁFORO GRANDE)
    html = f"""
    <html>
    <body style="margin:0; display:flex; justify-content:center; align-items:center;">

        <div style="
            display:flex;
            flex-direction:column;
            align-items:center;
            width:110px;
            padding:20px 15px;
            background:#111;
            border-radius:18px;
            box-shadow:0 5px 20px rgba(0,0,0,0.5);
            overflow:visible;
        ">
            
            <div style="
                width:60px;
                height:60px;
                border-radius:50%;
                margin:12px 0;
                background:{'red' if nivel=='rojo' else '#2b2b2b'};
                box-shadow:{'0 0 35px red' if nivel=='rojo' else 'none'};
                transition: all 0.3s ease;
            "></div>

            <div style="
                width:60px;
                height:60px;
                border-radius:50%;
                margin:12px 0;
                background:{'yellow' if nivel=='amarillo' else '#2b2b2b'};
                box-shadow:{'0 0 35px yellow' if nivel=='amarillo' else 'none'};
                transition: all 0.3s ease;
            "></div>

            <div style="
                width:60px;
                height:60px;
                border-radius:50%;
                margin:12px 0;
                background:{'green' if nivel=='verde' else '#2b2b2b'};
                box-shadow:{'0 0 35px green' if nivel=='verde' else 'none'};
                transition: all 0.3s ease;
            "></div>

        </div>

    </body>
    </html>
    """

    components.html(html, height=340)

placeholder = st.empty()
def animacion(color):  #FUNCIÓN PARA LA ANIMACIÓN DEL SEMÁFORO (ESTILO FORMULA 1)
    luces = {
        "rojo": "🔴 ⚫ ⚫",
        "ambar": "⚫ 🟡 ⚫",
        "verde": "⚫ ⚫ 🟢"
    }
    placeholder.markdown(
        f"<div style='font-size:20px; text-align:left'>{luces[color]}</div>",
        unsafe_allow_html=True
    )

def mostrar_resultado_traduccion(res_seg, res_det, lang_ui):  #FUNCIÓN QUE LLAMA A LA API DETECTAR IDIOMA PARA MOSTRAR LOS RESULTADOS
    # Contenedor principal con borde
    with st.container(border=True):

        # --- CABECERA / IDIOMA DETECTADO ---
        st.markdown(f"""
            <div style="
                background-color: #f9fbf2; 
                padding: 20px; 
                border-radius: 15px; 
                border-left: 5px solid #b6c35d; 
                margin-bottom: 20px;
            ">
                <h3 style="color: #4a4a4a; margin: 0;">
                    🌍 {UI_TEXTS[lang_ui]["mode"]}
                </h3>
                <p style="font-size: 18px; color: #6b8e23; font-weight: bold; margin-top: 10px;">
                    {UI_TEXTS[lang_ui]['lang_phrase']}: {res_det.get('idioma_detectado', '').upper()}
                </p>
            </div>
        """, unsafe_allow_html=True)

        # --- MENSAJE DINÁMICO ---
        mensaje = traducir_mensaje(
            lang_ui,
            res_det["idioma_detectado"],
            res_det["es_analizable"]
        )

        # --- VALIDACIÓN ---
        color_box = "#b6c35d"
        texto_validacion = f"✅ {UI_TEXTS[lang_ui]['valid_phrase']}"

        st.markdown(f"""
            <div style="
                background-color: {color_box}; 
                color: white; 
                padding: 12px; 
                border-radius: 10px; 
                text-align: center; 
                font-weight: bold;
                margin-bottom: 25px;
            ">
                {texto_validacion}
            </div>
            <p style="font-style: italic; color: #555;">
                {mensaje}
            </p>
        """, unsafe_allow_html=True)

        # --- COMPARATIVA ---
        col_orig, col_trad = st.columns(2)

        with col_orig:
            st.markdown(f"""
                <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; height: 100%;">
                    <h4 style="color: #e89a40; margin-top: 0;">
                        {UI_TEXTS[lang_ui]['original_phrase']}
                    </h4>
                    <p style="color: #333; font-size: 14px;">
                        {res_det.get("original", "")}
                    </p>
                </div>
            """, unsafe_allow_html=True)

        with col_trad:
            st.markdown(f"""
                <div style="background-color: #f2f7e5; padding: 15px; border-radius: 10px; border: 1px solid #b6c35d; height: 100%;">
                    <h4 style="color: #6b8e23; margin-top: 0;">
                        {UI_TEXTS[lang_ui]['translated_phrase']}
                    </h4>
                    <p style="color: #333; font-size: 14px;">
                        {res_det.get("traducido", "")}
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
def mostrar_resultados(res_seg, res_det, lang_ui):   #FUNCIÓN QUE LLAMA A LA API ANALIZAR PARA MOSTRAR LOS RESULTADOS
    # Título de resultados
    st.subheader(UI_TEXTS[lang_ui]["result"])

    nivel = res_seg.get("nivel_seguridad")
    confianza = res_seg.get("confianza_seguridad", 0)
    confianza_pct = int(confianza * 100)

    nivel_config = {
        "verde":    {"color": "#16a34a", "bg": "#f0fdf4", "border": "#86efac", "icon": "✓", "label": UI_TEXTS[lang_ui]['green']},
        "amarillo": {"color": "#ca8a04", "bg": "#fefce8", "border": "#fde047", "icon": "⚠", "label": UI_TEXTS[lang_ui]['yellow']},
        "rojo":     {"color": "#dc2626", "bg": "#fff1f2", "border": "#fca5a5", "icon": "✕", "label": UI_TEXTS[lang_ui]['red']},
    }
    cfg = nivel_config.get(nivel, nivel_config["amarillo"])
    c, bg, bd, icon, lbl = cfg['color'], cfg['bg'], cfg['border'], cfg['icon'], cfg['label']

    st.markdown(f"""
    <div style="background:{bg};border:2px solid {bd};border-radius:14px;padding:22px 26px;margin-bottom:14px;">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;">
            <div style="width:54px;height:54px;border-radius:50%;background:white;border:2px solid {c};
                        display:flex;align-items:center;justify-content:center;
                        font-size:26px;color:{c};font-weight:700;flex-shrink:0;">
                {icon}
            </div>
            <div>
                <div style="font-size:28px;font-weight:700;color:{c};">{lbl}</div>
            </div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:7px;">
            <span style="font-size:16px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:1px;">
                {UI_TEXTS[lang_ui]['trust']}
            </span>
            <span style="font-size:22px;font-weight:700;color:{c};">{confianza_pct}%</span>
        </div>
        <div style="height:10px;background:#e5e7eb;border-radius:99px;overflow:hidden;">
            <div style="height:100%;width:{confianza_pct}%;background:{c};border-radius:99px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mensaje
    mensaje = traducir_mensaje_analisis(lang_ui, res_det["idioma_detectado"])
    st.markdown(f"""
    <div style="border-left:4px solid {c};background:#f9fafb;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:14px;">
        <div style="font-size:13px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#111827;margin-bottom:8px;">
            {UI_TEXTS[lang_ui]['message']}
        </div>
        <div style="font-size:17px;color:#374151;line-height:1.7;">{mensaje}</div>
    </div>
    """, unsafe_allow_html=True)

    # Indicadores
    indicadores = res_seg.get("indicadores", [])
    if indicadores and res_det["idioma_detectado"] == "es":
        items = "".join(
            f"<div style='padding:10px 0;border-bottom:1px solid #f3f4f6;display:flex;gap:10px;align-items:flex-start;'>"
            f"<span style='color:{c};font-weight:700;font-size:20px;'>›</span>"
            f"<span style='font-size:17px;color:#374151;line-height:1.6;'>{ind}</span></div>"
            for ind in indicadores
        )
        st.markdown(f"""
    <div style="background:#f9fafb;border:1.5px solid #e5e7eb;border-left:4px solid {c};border-radius:12px;padding:6px 20px 10px;">
        <div style="font-size:13px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#111827;padding:12px 0 8px;">
            {UI_TEXTS[lang_ui]['indicator']}
        </div>
        {items}
    </div>
    """, unsafe_allow_html=True)


# ---------- SIDEBAR ----------
with st.sidebar:    #Aquí es donde se ve el desplegable de los idiomas en el lateral izquierdo
    
    st.header("⚙️ Configuración / Configuration")      #Cabecera de configuración donde de momento solo están los idiomas (modificable)

    selected_name = st.selectbox(
        "🌍 Idioma / Language",
        list(languages.keys())
    )

    idioma_select = languages[selected_name]    #Variable que guarda el idioma seleccionado de todos los posibles
    lang_ui = idioma_select                     #Variable que guarda el idioma seleccionado de todos los posibles
    idioma_input = languages_input[selected_name.split(" ")[1]]     #Variable que guarda según el idioma seleccionado los elementos visibles por pantalla
    lang_ui_input = idioma_input        #Variable que guarda según el idioma seleccionado los elementos visibles por pantalla
    
    st.markdown(        #CAMBIO DE COLOR AL VIOLETA
    f"""
    <div style="
        background-color: #D9CCEE;     
        color: #000000;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 9999;
        pointer-events: none;
    ">
        {lang_ui_input['func_label']}
    </div>
    """,
    unsafe_allow_html=True
    )


# ---------- HEADER ----------
with st.container():
    #Este markdown hace de st.title()
    st.markdown("<h1 style='text-align:center; color:#8f9e25; font-size:60px;'>✔ Proyecto Verid.IA</h1>",unsafe_allow_html=True) #Título de la web en la cabecera (modificable) 
    st.caption(lang_ui_input["info_label"])     #Mensaje informativo

# ---------- MODO ----------        #Traducir también al idioma que se seleccione
with st.container():
    st.markdown(f"<h3 style='color:#6f4a8e;'>{lang_ui_input["mode_label"]}:</h3>", unsafe_allow_html=True)
    modo = st.radio("Selecciona un modo", [f"{lang_ui_input["mode_label_one"]}", f"{lang_ui_input["mode_label_two"]}"], horizontal=True, label_visibility="hidden")  #CAMBIO CUANDO SE INTRODUZCA EL ESTADISTICAS.PY

st.divider()    #Esto deja un espacio entre el desplegable de los idiomas y el mensaje de funcionalidad


# ---------- CSS para botón pequeño ----------
# Código encargado del diseño del botón de borrar de la web, formato html
st.markdown("""
<style>
.small-btn button {
    color: #c3a5c1      
    padding: 0.2rem 0.4rem;
    font-size: 14px;
    float: right;
}
</style>
""", unsafe_allow_html=True)

# ---------- Layout ----------

st.subheader(f"📄 {lang_ui_input["info_anuncio_label"]}")   #Subcabecera del comprobador de anuncios (modificable)

# Inicializar session_state si no existe
if "texto" not in st.session_state:
    st.session_state["texto"] = ""
if "url" not in st.session_state:
    st.session_state["url"] = ""
if "res_seg" not in st.session_state:       #CAMBIO 
    st.session_state["res_seg"] = None
if "res_det" not in st.session_state:
    st.session_state["res_det"] = None
if "lang_ui_resultado" not in st.session_state:
    st.session_state["lang_ui_resultado"] = None
if "expanded_ad_info" not in st.session_state:
    st.session_state["expanded_ad_info"] = True  # Abierto por defecto al inicio


with st.expander(f"📋 {lang_ui_input['copiar_label']}", expanded=st.session_state["expanded_ad_info"]):
    
    # ---------- TEXTO DEL ANUNCIO ----------
    col_text_label, col_text_btn = st.columns([9, 1])
    
    with col_text_label:
        st.markdown(f"*{lang_ui_input['text_label']}*")
    with col_text_btn:
        if st.button("🧹", key="clear_text", help=lang_ui_input["borrar_texto_label"]):
            st.session_state["texto"] = ""
    
    # Input
    text_input = st.text_area(
        "Text",
        key="texto",
        height=150
    )
    
    # ---------- URL DEL ANUNCIO ----------
    col_url_label, col_url_btn = st.columns([9, 1])
    
    with col_url_label:
        st.markdown(f"*{lang_ui_input['url_label']}*")
    with col_url_btn:
        if st.button("🧹", key="clear_url", help=lang_ui_input["borrar_url_label"]):
            st.session_state["url"] = ""
    
    # Input
    url_input = st.text_input(
        "URL",
        key="url"
    )
    
    # Parte donde se podía subir la imagen
    st.markdown(f"*{lang_ui_input['imagen_label']}*")
    uploaded_file = st.file_uploader(
        f"{lang_ui_input['file_label']}",
        key="imagen",
        type=["jpg", "jpeg", "png", "tiff"]
    )
    
    # ---------- VISTA PREVIA DE IMAGEN ----------
    st.subheader(f"🖼 {lang_ui_input['previa_label']}")
    
    if uploaded_file:
        st.image(uploaded_file, use_column_width=True)
    else:
        st.markdown(
            f"""
            <div style="
                background-color: #C3B1E1;
                color: #000000;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                z-index: 9999;
                pointer-events: none;
            ">
                {lang_ui_input['info_imagen_label']}
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------- BOTÓN ANALIZAR ----------
st.divider()
analyze = st.button(f"🔎 {lang_ui_input['anuncio_label']}")

# ---------- ANÁLISIS ----------
if analyze:
    # Validar que hay datos
    inputs_filled = sum([           #CAMBIO PARA MENSAJE DE ERROR (SOLO SE ELIGE UNA OPCION)
        bool(text_input.strip()),
        bool(url_input.strip()),
        bool(uploaded_file)
    ])

    if inputs_filled == 0:      #CAMBIO PARA MENSAJE DE ERROR (SOLO SE ELIGE UNA OPCION)
        st.warning(f"⚠️ {UI_TEXTS[lang_ui]['data']}")
        st.stop()

    if inputs_filled > 1:       #CAMBIO PARA MENSAJE DE ERROR (SOLO SE ELIGE UNA OPCION)
        st.warning(f"⚠️ {UI_TEXTS[lang_ui]['data_add']}")
        st.stop()
    
    # Cerrar el expander
    st.session_state["expanded_ad_info"] = False
    
    # Definir tipo de entrada
    if uploaded_file:
        tipo = "IMAGEN"
    elif url_input:
        tipo = "ENLACE"
    else:
        tipo = "TEXTO"
    
    # Preparar datos
    data = {
        "texto": text_input,
        "url": url_input,
        "idioma_destino": idioma_select,
        "tipo": tipo
    }
    
    files = {}
    if uploaded_file:
        files["foto"] = (
            uploaded_file.name,
            uploaded_file,
            uploaded_file.type
        )
     #DESDE ESTE IF AL FINAL TODO CAMBIO !!!
    if modo == f"{lang_ui_input["mode_label_one"]}":  #CONDICIÓN PARA EL ANÁLISIS DEL ANUNCIO (MODO 1)
        # Mostrar spinner mientras se analiza
        placeholder = st.empty()
        with st.spinner(f"{idioma_input['spinner_label']}"):
            # PASO 1: Detectar idioma
            animacion("rojo")
            time.sleep(1.5)

            animacion("ambar")
            time.sleep(1.5)

            animacion("verde")
            response_idioma = llamar_api(API_DETECTAR_IDIOMA, data, files)
            time.sleep(1.5)
            placeholder.empty()
        
        # Procesar respuesta
        if response_idioma and response_idioma.status_code == 200:
            res_det = response_idioma.json()
            
            # Verificar si es analizable PRIMERO
            if res_det.get("es_analizable"):
                # PASO 2: Analizar seguridad (sin mostrar nada todavía)
                if uploaded_file:
                    uploaded_file.seek(0)
                    files = {"foto": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                
                response_seguridad = llamar_api(API_ANALIZAR, data, files)
                
                if response_seguridad and response_seguridad.status_code == 200:
                    res_seg = response_seguridad.json()
                    
                    # ========== MOSTRAR PRIMERO: RESULTADOS DEL ANÁLISIS ==========
                    st.divider()
                    mostrar_resultados(res_seg, res_det, lang_ui)
                    
                    # ========== MOSTRAR DESPUÉS: INFORMACIÓN DE TRADUCCIÓN ==========
                    st.divider()

                    # Guardamos resultados en session_state para que sobrevivan al rerender
                    st.session_state["res_seg"] = res_seg
                    st.session_state["res_det"] = res_det
                    st.session_state["lang_ui_resultado"] = lang_ui
                    
                else:
                    st.error("❌ Error al conectar con la API de Análisis")
                    if response_seguridad:
                        st.write(f"Código de estado: {response_seguridad.status_code}")
            
            else:
                # Idioma no analizable - mostrar warning en popup
                idioma_detectado = res_det.get('idioma_detectado', 'desconocido')
                st.markdown(f"""
                <div style="
                    background-color: rgba(235, 226, 211, 1);
                    padding: 40px;
                    border-radius: 12px;
                    text-align: center;
                    max-width: 500px;
                    margin: 20px auto;
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
                    border: 2px solid rgba(232, 154, 64, 1);
                ">
                    <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
                    <p style="font-size: 20px; color: rgba(74, 72, 74, 1); margin: 0;">
                        {UI_TEXTS[lang_ui]["spanish_only_error"]}
                    </p>
                    <p style="font-size: 16px; color: rgba(74, 72, 74, 1); margin: 10px 0;">
                        🌍 {UI_TEXTS[lang_ui]['lang_phrase']}: <strong>{idioma_detectado.upper()}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
               #CAMBIO COLOR DEL BOTÓN DE CIERRE 
                st.markdown("""     
                    <style>

                    /* Solo el botón del warning (posición concreta) */
                    div[data-testid="stHorizontalBlock"] div:nth-of-type(2) button[kind="secondary"] {
                        background-color: #FFA94D !important;
                        color: #000000 !important;
                    }

                    </style>
                    """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button(f"✓ {UI_TEXTS[lang_ui]['close']}", key="close_warning", use_container_width=True, type="secondary"):
                        st.rerun()
        
        else:
            st.error("❌ Error al detectar el idioma")
            if response_idioma:
                st.write(f"Código de estado: {response_idioma.status_code}")

# ---------- MODAL TRADUCCIÓN ----------
# Este bloque vive FUERA del if analyze: para sobrevivir al rerender
if st.session_state.get("res_seg") is not None:
    _lang = st.session_state.get("lang_ui_resultado", "es")

    modal = Modal(
        f"{UI_TEXTS[_lang]['result']}",
        key="modal_resultado",
        max_width=700
    )

    #estado único de apertura (no del widget)
    if "open_modal" not in st.session_state:
        st.session_state.open_modal = False
    
    #CAMBIO COLOR DEL BOTÓN DE VER ANÁLISIS
    st.markdown("""
        <style>

        div[data-testid="stHorizontalBlock"] div:nth-child(2) div[data-testid="stButton"] button {
            background-color: #FFA94D !important;
            color: #000000 !important;
        }

        </style>
        """, unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

    with col_btn2:
        if st.button(
            f"🔎 {UI_TEXTS[_lang]['detect']}",
            use_container_width=True,
            key="abrir_modal_btn"
        ):
            st.session_state.open_modal = True

    #RESET automático cuando cambia el texto/idioma
    if "prev_res_seg" not in st.session_state:
        st.session_state.prev_res_seg = None

    current = st.session_state.get("res_seg")

    if current != st.session_state.prev_res_seg:
        st.session_state.prev_res_seg = current
        st.session_state.open_modal = False

    #RENDER CONTROLADO (SIN is_open)
    if st.session_state.open_modal:
        with modal.container():

            mostrar_resultado_traduccion(
                st.session_state["res_seg"],
                st.session_state["res_det"],
                _lang
            )

            if st.button(
                f"{UI_TEXTS[_lang]['close']}",
                key="cerrar_modal",
                type="primary"
            ):
                st.session_state.open_modal = False
                st.session_state["res_seg"] = None
                st.session_state["res_det"] = None
                st.rerun()


#Ejecución (local): streamlit run app.py
#Ejecución del streamlit: streamlit run frontend/app.py
#Ejecución del archivo si en la otra terminal se está ejecutando el uvicorn de traduccion.py: python frontend/app.py