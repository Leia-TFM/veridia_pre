import streamlit as st
import streamlit.components.v1 as components
import requests

API_DETECTAR_IDIOMA = "http://127.0.0.1:8000/api/detectar_idioma"
API_ANALIZAR = "http://127.0.0.1:8000/api/analizar"

# ---------- CONFIG ----------
st.set_page_config(                 #Define el título de la página y su icono en la pestaña del navegador (modificable)
    page_title="Proyecto Verid.IA",
    page_icon="✔",
    layout="wide"
)

# ---------- CSS ----------  
# Código encargado del diseño (colores, tipo de celda, botones, área de texto) de la web en ese orden, formato html
st.markdown("""     
<style>

.main {
    background-color: #ebe2d3;  #crema, si no gusta se puede cambiar a blanco
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
    "🇷🇴 Română": "ro"
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
        "previa_label": "Vista previa",
        "info_imagen_label": "Sube una imagen para verla aquí",
        "borrar_texto_label": "Borrar texto",
        "borrar_url_label": "Borrar URL",
        "spinner_label": "Analizando anuncio...",
        "mode_label": "Seleccione un modo de uso",
        "mode_label_one": "Analizar anuncio",
        "mode_label_two": "Detectar Idioma / Traducción"

    },
    "English": {
        "text_label": "Job advertisement text",
        "url_label": "Advertisement URL",
        "imagen_label": "Advertisement image",
        "anuncio_label": "Analyse advertisement",
        "file_label": "Upload image of advertisement to view it here",
        "func_label": "Insert an advertisement to detect potential fraud.",
        "info_label": "Detects potentially fraudulent job postings. You may select one of the following three options (Copy Text / Copy URL / Upload an image) to verify this.",
        "info_anuncio_label": "Advertisement´s information",
        "previa_label": "Preview",
        "info_imagen_label": "Upload an image to view it here",
        "borrar_texto_label": "Erase text",
        "borrar_url_label": "Erase URL",
        "spinner_label": "Analysing advertisement...",
        "mode_label": "Select a usage mode",
        "mode_label_one": "Analyse advertisement",
        "mode_label_two": "Detect Language / Translation"

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
        "previa_label": "Aperçu",
        "info_imagen_label": "Téléchargez une image pour la voir ici",
        "borrar_texto_label": "Effacer texte",
        "borrar_url_label": "Effacer URL",
        "spinner_label": "Analyse de l'annonce...",
        "mode_label": "Sélectionnez un mode d'utilisation",
        "mode_label_one": "Analyser l'annonce",
        "mode_label_two": "Détection de la langue / Traduction"

    }
}

# ---------- SIDEBAR ----------
with st.sidebar:    #Aquí es donde se ve el desplegable de los idiomas en el lateral izquierdo
    
    st.header("⚙️ Configuración")      #Cabecera de configuración donde de momento solo están los idiomas (modificable)

    selected_name = st.selectbox(
        "🌍 Idioma / Language",
        list(languages.keys())
    )

    idioma_select = languages[selected_name]    #Variable que guarda el idioma seleccionado de todos los posibles
    lang_ui = idioma_select                     #Variable que guarda el idioma seleccionado de todos los posibles
    idioma_input = languages_input[selected_name.split(" ")[1]]     #Variable que guarda según el idioma seleccionado los elementos visibles por pantalla
    lang_ui_input = idioma_input        #Variable que guarda según el idioma seleccionado los elementos visibles por pantalla
    
    st.markdown(        #Lo podemos cambiar al naranja
    f"""
    <div style="
        background-color: #b6c35d;
        color: #000000;
        padding: 10px 20px;
        border-radius: 8px;
        border-left: 5px solid #8f9e25;
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
    modo = st.radio("Selecciona un modo", [f"{lang_ui_input["mode_label_one"]}", f"{lang_ui_input["mode_label_two"]}"], horizontal=True, label_visibility="hidden")

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

# ---------- TEXTO DEL ANUNCIO ----------
col_text_label, col_text_btn = st.columns([9,1])    #Localización del botón de borrar de esa parte y del área del texto

with col_text_label:    #Columna del área del texto
    st.markdown(f"**{lang_ui_input['text_label']}**") #Mensaje del área del texto
with col_text_btn:  #Columna del botón de borrar
    if st.button("🧹", key="clear_text", help=lang_ui_input["borrar_texto_label"]):
        st.session_state["texto"] = ""

# Input
text_input = st.text_area(
    "Text", 
    key="texto",
    height=150
)

# ---------- URL DEL ANUNCIO ----------
#Mismo funcionamiento que el texto
col_url_label, col_url_btn = st.columns([9,1])

with col_url_label:
    st.markdown(f"**{lang_ui_input['url_label']}**")
with col_url_btn:
    if st.button("🧹", key="clear_url", help=lang_ui_input["borrar_url_label"]):
        st.session_state["url"] = ""

# Input
url_input = st.text_input(
    "URL",  
    key="url"
)

#Parte donde se podía subir la imagen
st.markdown(f"**{lang_ui_input['imagen_label']}**")
uploaded_file = st.file_uploader(
        f"{lang_ui_input["file_label"]}",
        key="imagen",
        type=["jpg","jpeg","png","tiff"]
)

st.subheader(f"🖼 {lang_ui_input["previa_label"]}") #Si subes una imagen te muestra una vista previa de la misma

if uploaded_file:   #Comprobador de la imagen
    st.image(uploaded_file, use_column_width=True)
else:
    st.markdown(        #Lo podemos cambiar al naranja
    f"""
    <div style="
        background-color: #b6c35d;
        color: #000000;
        padding: 10px 20px;
        border-radius: 8px;
        border-left: 5px solid #b6c35d;
        font-weight: 500;
        z-index: 9999;
        pointer-events: none;
    ">
        {lang_ui_input['info_imagen_label']}
    </div>
    """,
    unsafe_allow_html=True
)


# ---------- BOTÓN ----------
st.divider()

analyze = st.button(f"🔎 {lang_ui_input['anuncio_label']}") #Botón que analiza el anuncio (modificable su visualización)

# ---------- TEXTOS RESULTADO ----------
UI_TEXTS = {    #Diccionario que recoje los resultados que vería el usuario por pantalla dependiendo del idioma que haya seleccionado (falta rellenar más)
    "es":{
        "result":" ✔ Resultado del análisis",
        "spanish_only_error": "Solo se permiten anuncios en español. Inténtalo de nuevo.",
        "data": "Introduce datos",
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


    },
    "en":{
        "result":" ✔ Analysis Result",
        "spanish_only_error": "Only advertisements in Spanish are allowed. Try again.",
        "data": "Enter data",
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
    },
    "fr":{
        "result":" ✔ Résultat de l'analyse",
        "spanish_only_error": "Seules les annonces en espagnol sont autorisées. Réessayez.",
        "data": "Saisir des données",
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

def semaforo(nivel=None):
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

# ---------- ANÁLISIS ----------
if analyze:

    if not text_input and not url_input and not uploaded_file:
        st.warning(f"⚠️ {UI_TEXTS[lang_ui]["data"]}")   #Traducir también con otra variable del idioma seleccionado
        st.stop()

    if uploaded_file:
        tipo = "IMAGEN"
    elif url_input:
        tipo = "ENLACE"
    else:
        tipo = "TEXTO"

    data = {    #Datos recibidos
        "texto": text_input,
        "url": url_input,
        "idioma_destino": idioma_select,
        "tipo": tipo
    }

    files = {}

    if uploaded_file: #Condición para las imágenes
        files["foto"] = (
            uploaded_file.name,
            uploaded_file,
            uploaded_file.type
        )

    endpoint = API_ANALIZAR if modo == f"{lang_ui_input["mode_label_one"]}" else API_DETECTAR_IDIOMA

    with st.spinner(idioma_input["spinner_label"]):
        response = llamar_api(endpoint, data, files)

    if response.status_code == 200:  #Significa que está correcto
        result = response.json()

        st.divider()
        st.subheader(UI_TEXTS[lang_ui]["result"])

       
        # ---------- ANALIZAR ----------
        if modo == f"{lang_ui_input["mode_label_one"]}":

            # idioma detectado
            st.info(f"{UI_TEXTS[lang_ui]["lang_phrase"]}: {result.get('idioma_detectado')}")

            nivel = result.get("nivel_seguridad")
            # SEMÁFORO  
            col1, col2 = st.columns([1,2])

            with col1:
                semaforo(nivel)

            with col2:
                st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
                if nivel == "verde":
                    st.success(f"🟢 {UI_TEXTS[lang_ui]['green']}")
                elif nivel == "amarillo":
                    st.warning(f"🟡 {UI_TEXTS[lang_ui]['yellow']}")
                elif nivel == "rojo":
                    st.error(f"🔴 {UI_TEXTS[lang_ui]['red']}")

            # PUNTUACIÓN (0–1 → lo pasamos a %)
            confianza = result.get("confianza_seguridad", 0)

            st.metric(f"{UI_TEXTS[lang_ui]["trust"]}", f"{int(confianza * 100)}%")
            st.progress(confianza)

            # MENSAJE
            st.subheader(f"{UI_TEXTS[lang_ui]["message"]}")
            mensaje = traducir_mensaje_analisis(
                lang_ui,
                result["idioma_detectado"]

            )
            st.write(mensaje)

            # INDICADORES
            st.subheader(f"{UI_TEXTS[lang_ui]["indicator"]}")

            indicadores = result.get("indicadores", [])
            if result["idioma_detectado"] == "es":
                for ind in indicadores:
                    st.write("•", ind)

        # ----------DETECTAR IDIOMA ----------
        else:
            st.subheader(f"🌍 {UI_TEXTS[lang_ui]["mode"]}")

            # idioma detectado
            st.info(f"{UI_TEXTS[lang_ui]["lang_phrase"]}: {result.get('idioma_detectado')}")

            # mensaje
            mensaje = traducir_mensaje(
                lang_ui,
                result["idioma_detectado"],
                result["es_analizable"]
            )
            st.write(mensaje)

            # comprobación
            if result.get("es_analizable"):
                st.success(f"{UI_TEXTS[lang_ui]["valid_phrase"]}")

                # original
                st.subheader(f"{UI_TEXTS[lang_ui]["original_phrase"]}")
                st.write(result.get("original"))

                # traducido
                st.subheader(f"{UI_TEXTS[lang_ui]["translated_phrase"]}")
                st.success(result.get("traducido"))

            else:
                
                # Mostrar igualmente el original si quieres
                st.subheader(f"{UI_TEXTS[lang_ui]["original_phrase"]}")
                st.write(result.get("original"))

                # Mostrar traducción vacía o lo que haya
                st.subheader(f"{UI_TEXTS[lang_ui]["translated_phrase"]}")
                st.write(result.get("traducido") or "No disponible")

    elif response.status_code == 400:       #Significa que no se ha podido realizar el análisis porque el anuncio no estaba en español

        error_msg = response.json()["detail"]
        st.warning(UI_TEXTS[lang_ui]["spanish_only_error"])

    else:       #Error de la API (no haría nada)
        st.error("❌ Error al conectar con la API")
        st.write(response.status_code)
        
#Ejecución (local): streamlit run app.py
#Ejecución del streamlit: streamlit run frontend/app.py
#Ejecución del archivo si en la otra terminal se está ejecutando el uvicorn de traduccion.py: python frontend/app.py