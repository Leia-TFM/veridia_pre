import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/traducir"

# -------- Título (Se está Votando Ahora...) --------

st.set_page_config(page_title="fAIr Job", page_icon="🚦")

st.title("🚦 fAIr Job - Detector de Riesgo")

# -------- Idiomas --------
languages = {
    "Inglés": "en",
    "Español": "es",
    "Francés": "fr",
    "Alemán": "de",
    "Italiano": "it",
    "Portugués": "pt",
    "Ruso": "ru",
    "Árabe": "ar"
}

UI_TEXTS = {
    "es": {
        "result": "🚦 Resultado del análisis",
        "low": "🟢 Riesgo bajo",
        "medium": "🟡 Riesgo medio",
        "high": "🔴 Riesgo alto",
        "score": "Puntuación de riesgo",
        "message": "Mensaje",
        "motives": "Motivos detectados"
    },
    "en": {
        "result": "🚦 Analysis Result",
        "low": "🟢 Low Risk",
        "medium": "🟡 Medium Risk",
        "high": "🔴 High Risk",
        "score": "Risk Score",
        "message": "Message",
        "motives": "Detected Reasons"
    },
    "fr": {
        "result": "🚦 Résultat de l'analyse",
        "low": "🟢 Risque faible",
        "medium": "🟡 Risque moyen",
        "high": "🔴 Risque élevé",
        "score": "Score de risque",
        "message": "Message",
        "motives": "Motifs détectés"
    }
}

selected_name = st.selectbox("Idioma de respuesta:", list(languages.keys()))
idioma = languages[selected_name]
lang_ui = idioma

# -------- Inputs --------
text_input = st.text_area("Texto del anuncio:")
url_input = st.text_input("URL del anuncio (opcional):")

uploaded_file = st.file_uploader(
    "O sube una imagen del anuncio",
    type=["jpg", "jpeg", "png", "tiff"]
)

# -------- Botón --------
if st.button("Analizar anuncio"):

    data = {
        "texto": text_input,
        "url": url_input,
        "idioma": idioma
    }

    files = {}

    if uploaded_file:
        files["foto"] = (
            uploaded_file.name,
            uploaded_file,
            uploaded_file.type
        )

    response = requests.post(API_URL, data=data, files=files)

    if response.status_code == 200:
        result = response.json()

        st.subheader(UI_TEXTS[lang_ui]["result"])

        if result["semaforo"] == "VERDE":
            st.success(UI_TEXTS[lang_ui]["low"])
        elif result["semaforo"] == "AMARILLO":
            st.warning(UI_TEXTS[lang_ui]["medium"])
        elif result["semaforo"] == "ROJO":
            st.error(UI_TEXTS[lang_ui]["high"])

        st.metric(UI_TEXTS[lang_ui]["score"], result["puntuacion"])

        st.subheader(UI_TEXTS[lang_ui]["message"])
        st.info(result["mensaje_usuario"])

        st.subheader(UI_TEXTS[lang_ui]["motives"])

    else:
        st.error("Error al conectar con la API")
        st.write(response.status_code)
        st.write(response.text)
        
#Ejecución:  streamlit run app.py