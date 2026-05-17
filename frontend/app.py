# "El archivo app.py es el Frontend principal de la aplicación. Se encarga de construir
# la interfaz web con Streamlit, gestionar la navegación entre páginas, el sistema de idiomas,
# los inputs del usuario (texto, URL e imagen) y comunicarse con el Backend a través de las APIs
# siguiendo los criterios de los diferentes grupos del proyecto (estilo, colores, disposición, etc...)"

# "Librerías principales: streamlit para la interfaz, requests para las llamadas a la API,
# deep_translator para traducciones en tiempo real de textos estáticos de la UI"
import streamlit as st
from streamlit_modal import Modal
from streamlit_scroll_navigation import scroll_navbar  
import requests
import time
from deep_translator import GoogleTranslator

##### LAS FRASES EN MAYÚSCULA SON PARA COSAS QUE HAY QUE CAMBIAR

# "URLs de los tres endpoints del Backend con los que se comunica el Frontend"
API_DETECTAR_IDIOMA = "http://127.0.0.1:8000/api/detectar_idioma"
API_ANALIZAR = "http://127.0.0.1:8000/api/analizar"
API_ESTADISTICAS = "http://127.0.0.1:8000/api/estadisticas"

# "NAVEGACIÓN"
# "Inicialización del estado de navegación: si es la primera vez que carga la app,
# se establece la página de inicio y el idioma como None hasta que el usuario seleccione uno"
if "page" not in st.session_state:
    st.session_state.page = "home"

if "idioma" not in st.session_state:
    st.session_state.idioma = None

# "CONFIG"
# "Define el título de la página y su icono en la pestaña del navegador"
st.set_page_config(                  
    page_title="Proyecto Verid.IA",
    page_icon="✔",
    layout="wide"
)

# "CSS" 
# "Código encargado del diseño (colores, tipo de celda, botones, área de texto y modal de la detección/traducción) 
# de la web en ese orden, formato html, botón principal"
st.markdown("""     
<style>

.main {
    background-color: #ffffff;  #crema, si no gusta se puede cambiar a blanco
}

.block-container {
    padding-top: 2rem;
}

.stButton>button {
    background-color: #b6c35d; /* botón verde */
    color: #000000; 
    border-radius: 10px;
    padding: 16px 28px; /* más grande */
    font-weight: bold;
    font-size: 20px; /* aumenta tamaño del texto */
}

textarea {
    border-radius:10px !important;
}

.st-key-modal_resultado-close {
    display: none !important;
}
            
</style>
""", unsafe_allow_html=True)

# "FUNCIONES API"
# "Función genérica para hacer llamadas POST al Backend, admite datos de formulario y archivos opcionales.
# En caso de error de conexión muestra un mensaje en pantalla y devuelve None para manejarlo desde fuera"
def llamar_api(endpoint, data, files=None):
    try:
        response = requests.post(endpoint, data=data, files=files)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

# "Versión GET de la función anterior, usada principalmente para obtener las estadísticas globales"
def llamar_api_get(endpoint):
    try:
        response = requests.get(endpoint)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return None
    
# "IDIOMAS"
# "Los idiomas seleccionables en el desplegable"
languages = {       
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

# "Diccionario con la traducción de todos los elementos visibles por pantalla a los demás idiomas"
languages_input = {     
    "Español": {
        "text_label": "Texto del anuncio",
        "url_label": "URL del anuncio",
        "imagen_label": "Imagen del anuncio",
        "anuncio_label": "Analizar anuncio",
        "file_label": "📷Sube una imagen del anuncio. Para mejores resultados, recorta la foto encuadrando el anuncio de forma nítida.",
        "func_label": "Introduce un anuncio para detectar posibles fraudes.",
        "info_label": "Detecta anuncios de trabajo potencialmente fraudulentos. Puede elegir una de las siguientes tres opciones (Copiar Texto / Copiar URL / Subir una imagen) para comprobarlo.",
        "info_anuncio_label": "Información del anuncio",
        "copiar_label": "Copia aquí tu anuncio (Texto/URL/Imagen)",
        "previa_label": "Vista previa",
        "info_imagen_label": "Sube una imagen para verla aquí.",
        "borrar_texto_label": "Borrar texto",
        "borrar_url_label": "Borrar URL",
        "borrar_imagen_label": "Borrar imagen",
        "spinner_label": "Analizando anuncio...",
        "mode_label": "Seleccione un modo de uso",
        "mode_label_one": "Analizar anuncio",
        "mode_label_two": "Mostrar estadísticas",
        "idioma_label": "Cambiar idioma",
        "seccion_label": "Ir a sección"

    },
    "English": {
        "text_label": "Advertisement's text",
        "url_label": "Advertisement URL",
        "imagen_label": "Advertisement image",
        "anuncio_label": "Analyse advertisement",
        "file_label": "📷Upload an image of the advertisement. For best results, crop the photo so that the ad is clearly framed.",
        "func_label": "Insert an advertisement to detect potential fraud.",
        "info_label": "Detects potentially fraudulent job postings. You may select one of the following three options (Copy Text / Copy URL / Upload an image) to verify this.",
        "info_anuncio_label": "Advertisement´s information",
        "copiar_label": "Paste your advertisement here (Text/URL/Image)",
        "previa_label": "Preview",
        "info_imagen_label": "Upload an image to view it here.",
        "borrar_texto_label": "Erase text",
        "borrar_url_label": "Erase URL",
        "borrar_imagen_label": "Erase image",
        "spinner_label": "Analysing advertisement...",
        "mode_label": "Select a usage mode",
        "mode_label_one": "Analyse advertisement",
        "mode_label_two": "Show statistics",
        "idioma_label": "Change language",
        "seccion_label": "Go to section"

    },
    "Français": {
        "text_label": "Texte de l'annonce",
        "url_label": "URL de l'annonce",
        "imagen_label": "Image de l'annonce",
        "anuncio_label": "Analyser l'annonce",
        "file_label": "📷Téléchargez une image de l’annonce. Pour de meilleurs résultats, recadrez la photo afin que l’annonce soit clairement cadrée.",
        "func_label": "Insérer un annonce pour détecter les fraudes potentielles.",
        "info_label": "Détecte les offres d'emploi potentiellement frauduleuses. Vous pouvez choisir l'une des trois options suivantes (Copier le texte / Copier l'URL / Télécharger une image) pour le vérifier.",
        "info_anuncio_label": "Information de l'annonce",
        "copiar_label": "Copiez ici votre annonce (Texte/URL/Image)",
        "previa_label": "Aperçu",
        "info_imagen_label": "Téléchargez une image pour la voir ici.",
        "borrar_texto_label": "Effacer texte",
        "borrar_url_label": "Effacer URL",
        "borrar_imagen_label": "Effacer image",
        "spinner_label": "Analyse de l'annonce...",
        "mode_label": "Sélectionnez un mode d'utilisation",
        "mode_label_one": "Analyser l'annonce",
        "mode_label_two": "Afficher les statistiques",
        "idioma_label": "Changer de langue",
        "seccion_label": "Accéder à la section"
    },
    "Deutsch": {
        "text_label": "Text des Stellenangebots",
        "url_label": "URL des Stellenangebots",
        "imagen_label": "Bild des Stellenangebots",
        "anuncio_label": "Stellenangebot analysieren",
        "file_label": "📷Laden Sie ein Bild der Anzeige hoch. Für beste Ergebnisse, schneiden Sie das Foto so zu, dass die Anzeige klar eingerahmt ist.",
        "func_label": "Ein Stellenangebot einfügen, um potenzielle Betrugsfälle zu erkennen",
        "info_label": "Erkennt potenziell betrügerische Stellenangebote. Sie können eine der folgenden drei Optionen auswählen (Text kopieren / URL kopieren / Bild hochladen), um dies zu überprüfen",
        "info_anuncio_label": "Informationen zum Stellenangebot",
        "copiar_label": "Füge hier deine Anzeige ein (Text, URL, Bild)",
        "previa_label": "Vorschau",
        "info_imagen_label": "Laden Sie ein Bild hoch, um es hier zu sehen.",
        "borrar_texto_label": "Text löschen",
        "borrar_url_label": "URL löschen",
        "borrar_imagen_label": "Bild löschen",
        "spinner_label": "Das Stellenangebot wird analysiert...",
        "mode_label": "Wählen Sie einen Verwendungsmodus",
        "mode_label_one": "Stellenangebot analysieren",
        "mode_label_two": "Statistiken anzeigen",
        "idioma_label": "Sprache ändern",
        "seccion_label": "Zum Abschnitt gehen"
    },
    "Italiano": {
        "text_label": "Testo dell'offerta di lavoro",
        "url_label": "URL dell'offerta di lavoro",
        "imagen_label": "Immagine dell'offerta di lavoro",
        "anuncio_label": "Analizza offerta di lavoro",
        "file_label": "📷Carica un'immagine dell'annuncio. Per ottenere risultati migliori, ritaglia la foto in modo che l'annuncio sia chiaramente inquadrato.",
        "func_label": "Inserisci un'offerta di lavoro per rilevare potenziali frodi",
        "info_label": "Rileva potenziali offerte di lavoro fraudolente. Puoi selezionare una delle seguenti tre opzioni (Copia testo / Copia URL / Carica un'immagine) per verificarla",
        "info_anuncio_label": "Informazioni sull'offerta di lavoro",
        "copiar_label": "Inserisci qui il tuo annuncio (Testo, URL, Immagine)",
        "previa_label": "Anteprima",
        "info_imagen_label": "Carica un'immagine per vederla qui.",
        "borrar_texto_label": "Elimina il testo",
        "borrar_url_label": "Elimina l'URL",
        "borrar_imagen_label": "Elimina l'immagine",
        "spinner_label": "Analisi dell'offerta di lavoro in corso...",
        "mode_label": "Seleziona una modalità di utilizzo",
        "mode_label_one": "Analizza annuncio",
        "mode_label_two": "Mostra statistiche",
        "idioma_label": "Cambia lingua",
        "seccion_label": "Vai alla sezione"
    },
    "Português": {
        "text_label": "Texto da oferta de emprego",
        "url_label": "URL da oferta de emprego",
        "imagen_label": "Imagem da oferta de emprego",
        "anuncio_label": "Analisar a oferta de emprego",
        "file_label": "📷Envie uma imagem do anúncio. Para melhores resultados, recorte a foto para que o anúncio fique claramente enquadrado.",
        "func_label": "Inserir uma oferta de emprego para detectar possíveis fraudes",
        "info_label": "Deteta potenciais ofertas de emprego fraudulentas. Pode selecionar uma das três opções seguintes (Copiar texto / Copiar URL / Carregar imagem) para verificá-la",
        "info_anuncio_label": "Informações sobre a oferta de emprego",
        "copiar_label": "Coloque aqui o seu anúncio (Texto, URL, Imagem)",
        "previa_label": "Pré-visualização",
        "info_imagen_label": "Carregar uma imagem para visualizá-la aqui.",
        "borrar_texto_label": "Apagar o texto",
        "borrar_url_label": "Apagar a URL",
        "borrar_imagen_label": "Apagar imagem",
        "spinner_label": "A analisar a oferta de emprego...",
        "mode_label": "Selecione um modo de uso",
        "mode_label_one": "Analisar anúncio",
        "mode_label_two": "Mostrar estatísticas",
        "idioma_label": "Mudar idioma",
        "seccion_label": "Ir para a secção"
    },
    "Русский": {
        "text_label": "Текст объявления о вакансии",
        "url_label": "URL объявления о вакансии",
        "imagen_label": "изображение объявления о вакансии",
        "anuncio_label": "Проанализировать объявление о вакансии",
        "file_label": "📷Загрузите изображение объявления. Для наилучших результатов, обрежьте фото так, чтобы объявление было чётко в кадре.",
        "func_label": "Вставить объявление о вакансии, чтобы обнаружить возможное мошенничество",
        "info_label": "Обнаруживает потенциально мошеннические объявления о вакансиях. Вы можете выбрать один из следующих трех вариантов («Копировать текст» / «Копировать URL» / «Загрузить изображение») для проверки",
        "info_anuncio_label": "Информация о вакансии",
        "copiar_label": "Вставьте сюда текст своего объявления (текст, URL, изображение)",
        "previa_label": "Предварительный просмотр",
        "info_imagen_label": "Загрузите изображение, чтобы увидеть его здесь.",
        "borrar_texto_label": "Удалить текст",
        "borrar_url_label": "Удалить URL",
        "borrar_imagen_label": "удалить изображение",
        "spinner_label": "Анализ вакансии...",
        "mode_label": "Выберите режим использования",
        "mode_label_one": "Анализировать объявление",
        "mode_label_two": "Показать статистику",
        "idioma_label": "Сменить язык",
        "seccion_label": "Перейти к разделу"
    },
    "العربية": {
        "text_label": "نص عرض العمل",
        "url_label": "رابط عرض العمل",
        "imagen_label": "صورة عرض العمل",
        "anuncio_label": "تحليل عرض العمل",
        "file_label": "📷قم بتحميل صورة للإعلان. للحصول على أفضل النتائج، قم بقص الصورة بحيث يظهر الإعلان بوضوح داخل الإطار",
        "func_label": "أدخل عرض العمل لاكتشاف الاحتيال المحتمل",
        "info_label": "عروض العمل الاحتيالية المحتملة. يمكنك اختيار أحد الخيارات الثلاثة التالية (نسخ النص / نسخ الرابط / تحميل صورة) للتحقق من ذلك",
        "info_anuncio_label": "معلومات عرض العمل",
        "copiar_label": "انسخ إعلانك هنا (نص، رابط، صورة)",
        "previa_label": "معاينة",
        "info_imagen_label": "قم بتحميل صورة لعرضها هنا",
        "borrar_texto_label": "مسح النص",
        "borrar_url_label": "مسح الرابط",
        "borrar_imagen_label": "حذف الصورة",
        "spinner_label": "تحليل عرض العمل...",
        "mode_label": "اختر وضع الاستخدام",
        "mode_label_one": "تحليل الإعلان",
        "mode_label_two": "عرض الإحصائيات",
        "idioma_label": "تغيير اللغة",
        "seccion_label": "الذهاب إلى القسم"
    },
    "Română": {
        "text_label": "Textul ofertei de angajare",
        "url_label": "URL-ul ofertei de angajare",
        "imagen_label": "Imaginea ofertei de angajare",
        "anuncio_label": "Analizați oferta de angajare",
        "file_label": "📷Încarcă o imagine a anunțului. Pentru rezultate mai bune și pentru, decupează fotografia astfel încât anunțul să fie clar încadrat.",
        "func_label": "Introduceți o ofertă de angajare pentru a depista eventualele fraude",
        "info_label": "Detectează ofertele de angajare potențial frauduloase. Puteți selecta una dintre următoarele trei opțiuni (Copiați textul / Copiați URL-ul / Încărcați o imagine) pentru a verifica acest lucru",
        "info_anuncio_label": "Detalii despre oferta de angajare",
        "copiar_label": "Copiază aici anunțul tău (Text, URL, Imagine)",
        "previa_label": "Previzualizare",
        "info_imagen_label": "Încărcați o imagine pentru a o vedea aici.",
        "borrar_texto_label": "Ștergeți textul",
        "borrar_url_label": "Ștergeți URL-ul",
        "borrar_imagen_label": "Șterge imaginea",
        "spinner_label": "Analizând oferta de angajare...",
        "mode_label": "Selectați un mod de utilizare",
        "mode_label_one": "Analizați anunțul",
        "mode_label_two": "Afișează statistici",
        "idioma_label": "Schimbă limba",
        "seccion_label": "Mergi la secțiune"
    },
    "Neerlandés": {
        "text_label": "Tekst van de advertentie",
        "url_label": "URL van de advertentie",
        "imagen_label": "Afbeelding van de advertentie",
        "anuncio_label": "Advertentie analyseren",
        "file_label": "📷Upload een afbeelding van de advertentie. Voor de beste resultaten, snijd de foto bij zodat de advertentie duidelijk in beeld is.",
        "func_label": "Voer een advertentie in om mogelijke fraude te detecteren.",
        "info_label": "Detecteert mogelijk frauduleuze vacatures. U kunt een van de volgende drie opties kiezen (Tekst kopiëren / URL kopiëren / Afbeelding uploaden) om dit te controleren.",
        "info_anuncio_label": "Advertentie-informatie",
        "copiar_label": "Plak hier je advertentie (Tekst, URL, Afbeelding)",
        "previa_label": "Voorvertoning",
        "info_imagen_label": "Upload een afbeelding om deze hier te zien.",
        "borrar_texto_label": "Tekst wissen",
        "borrar_url_label": "URL wissen",
        "borrar_imagen_label": "Afbeelding verwijderen",
        "spinner_label": "Advertentie analyseren...",
        "mode_label": "Selecteer een gebruiksmodus",
        "mode_label_one": "Advertentie analyseren",
        "mode_label_two": "Statistieken tonen",
        "idioma_label": "Taal wijzigen",
        "seccion_label": "Ga naar sectie"
    },
    "Catalán": {
        "text_label": "Text de l'oferta de treball",
        "url_label": "URL de l'oferta de treball",
        "imagen_label": "Imatge de l'oferta de treball",
        "anuncio_label": "Analitzar oferta de treball",
        "file_label": "📷Puja una imatge de l’anunci. Per obtenir millors resultats, retalla la foto de manera que l’anunci quedi clarament enquadrat.",
        "func_label": "Introdueix una oferta de treball per detectar possibles fraus",
        "info_label": "Detecta ofertes de treball potencialment fraudulentes. Pot escollir una de les següents tres opcions (Copiar text / Copiar URL / Puja una imatge) per comprovar-ho", #normalmente se gasta más triar (aunque creo que es más con cosas físicas que con decisiones) pero creo que escollir es más correcto (es más similar a seleccionar, lo que no se gasta 100% son seleccionar o elegir porque son castellanismos o en el caso de elegir es SOLO en contexto post elecciones), va en función de zonas y costumbres.
        "info_anuncio_label": "Informació de l'oferta de treball",
        "copiar_label": "Pega aquí el teu anunci (Text, URL, Imatge)",
        "previa_label": "Vista prèvia",
        "info_imagen_label": "Puja una imatge per veure-la aquí.",
        "borrar_texto_label": "Esborra text",
        "borrar_url_label": "Esborra URL",
        "borrar_imagen_label": "Esborra imatge",
        "spinner_label": "Analitzant oferta de treball...",
        "mode_label": "Seleccioneu un mode d'ús",
        "mode_label_one": "Analitzar anunci",
        "mode_label_two": "Mostra estadístiques",
        "idioma_label": "Canviar idioma",
        "seccion_label": "Anar a la secció"
    },
    "Polaco": {
        "text_label": "Treść ogłoszenia",
        "url_label": "URL ogłoszenia",
        "imagen_label": "Obraz ogłoszenia",
        "anuncio_label": "Analizuj ogłoszenie",
        "file_label": "📷Prześlij obraz reklamy. Aby uzyskać najlepsze wyniki, przytnij zdjęcie tak, aby reklama była wyraźnie w kadrze.",
        "func_label": "Wprowadź ogłoszenie, aby wykryć możliwe oszustwa.",
        "info_label": "Wykrywa potencjalnie fałszywe oferty pracy. Możesz wybrać jedną z trzech opcji (Skopiuj tekst / Skopiuj URL / Prześlij obraz), aby to sprawdzić.",
        "info_anuncio_label": "Informacje o ogłoszeniu",
        "copiar_label": "Wklej tutaj swoją reklamę (Tekst, adres URL, Obraz)",
        "previa_label": "Podgląd",
        "info_imagen_label": "Prześlij obraz, aby zobaczyć go tutaj.",
        "borrar_texto_label": "Usuń tekst",
        "borrar_url_label": "Usuń URL",
        "borrar_imagen_label": "Usuń obraz",
        "spinner_label": "Analizowanie ogłoszenia...",
        "mode_label": "Wybierz tryb użytkowania",
        "mode_label_one": "Analizuj ogłoszenie",
        "mode_label_two": "Pokaż statystyki",
        "idioma_label": "Zmień język",
        "seccion_label": "Przejdź do sekcji"
    },
    "Ucraniano": {
        "text_label": "Текст оголошення",
        "url_label": "URL оголошення",
        "imagen_label": "Зображення оголошення",
        "anuncio_label": "Аналізувати оголошення",
        "file_label": "📷Завантажте зображення оголошення. Для найкращих результатів, обріжте фото так, щоб оголошення було чітко в кадрі.",
        "func_label": "Введіть оголошення для виявлення можливого шахрайства.",
        "info_label": "Виявляє потенційно шахрайські вакансії. Ви можете вибрати один із трьох варіантів (Скопіювати текст / Скопіювати URL / Завантажити зображення) для перевірки.",
        "info_anuncio_label": "Інформація про оголошення",
        "copiar_label": "Вставте тут своє оголошення (текст, URL-адресу, зображення)",
        "previa_label": "Попередній перегляд",
        "info_imagen_label": "Завантажте зображення, щоб побачити його тут.",
        "borrar_texto_label": "Видалити текст",
        "borrar_url_label": "Видалити URL",
        "borrar_imagen_label": "видалити зображення",
        "spinner_label": "Аналіз оголошення...",
        "mode_label": "Виберіть режим використання",
        "mode_label_one": "Аналізувати оголошення",
        "mode_label_two": "Показати статистику",
        "idioma_label": "Змінити мову",
        "seccion_label": "Перейти до розділу"
    }
}

# "TEXTOS RESULTADO"
# "Diccionario con todos los textos que aparecen en los resultados del análisis traducidos a cada idioma soportado.
# Se accede a él siempre mediante el código de idioma de dos letras (ej: 'es', 'en', 'fr'...)"
UI_TEXTS = {    
    "es":{
        "result":" ✔ Resultado del análisis",
        "spanish_only_error": "Solo se permiten anuncios en español. Inténtalo de nuevo.",
        "data": "Introduce texto, url o sube una imagen", 
        "data_add": "Solo puedes introducir una opción: texto, URL o imagen", 
        "mode": "Detectar Idioma / Traducción",
        "lang_phrase": "Idioma detectado",
        "valid_phrase": "Texto válido para análisis",
        "original_phrase": "Texto original",
        "translated_phrase": "Texto traducido",
        "message": "Mensaje",
        "veredict": "Veredicto",
        "indicator": "Indicadores detectados",
        "trust": "Confianza",
        "green": "Riesgo bajo",
        "yellow": "Riesgo medio",
        "red": "Riesgo alto",
        "close": "Entendido", #EXTRA
        "detect": "Mostrar Detección/Traducción",  #EXTRA
        "config_title": "Configuración",
        "select_language_title": "Selecciona idioma",
        "continue_phrase": "Continuar",
        "about_us": "¿Quiénes somos?",
        "social_media": "Nuestras Redes Sociales"
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
        "veredict": "Verdict",
        "indicator": "Indicators detected",
        "trust": "Trust",
        "green": "Low risk",
        "yellow": "Medium risk",
        "red": "High risk",
        "close": "Understood",
        "detect": "Check Detection/Translation",
        "config_title": "Configuration",
        "select_language_title": "Choose Language", 
        "continue_phrase": "Continue",
        "about_us": "About us",
        "social_media": "Our Social Media" 
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
        "veredict": "Verdict",
        "indicator": "Indicateurs détectés",
        "trust": "Confiance",
        "green": "Risque faible",
        "yellow": "Risque moyen",
        "red": "Risque élevé ",
        "close": "Compris",
        "detect": "Vérifier Détection/Traduction",
        "config_title": "Configuration",
        "select_language_title": "Choisir la langue", 
        "continue_phrase": "Continuer",
        "about_us": "Qui sommes-nous?",
        "social_media": "Nos Réseaux Sociaux" 
    },
    "de": {
        "result": " ✔ Analyseergebnis",
        "spanish_only_error": "Nur Anzeigen auf Spanisch sind erlaubt. Versuche es erneut.",
        "data": "Gib Text oder eine URL ein oder lade ein Bild hoch",
        "data_add": "Du kannst nur eine Option eingeben: Text, URL oder Bilde", 
        "mode": "Sprache erkennen / Übersetzen",
        "lang_phrase": "Erkannte Sprache",
        "valid_phrase": "Text geeignet für die Analyse",
        "original_phrase": "Originaltext",
        "translated_phrase": "Übersetzter Text",
        "message": "Nachricht",
        "veredict": "Urteil",
        "indicator": "Erkannte Indikatoren",
        "trust": "Vertrauen",
        "green": "Geringes Risiko",
        "yellow": "Mittleres Risiko",
        "red": "Hohes Risiko",
        "close": "Verstanden",
        "detect": "Erkennung/Übersetzung anzeigen",
        "config_title": "Konfiguration",
        "select_language_title": "Sprache auswählen", 
        "continue_phrase": "Weiter",
        "about_us": "Über uns",
        "social_media": "Unsere Sozialen Medien" 
    },
    "it": {
        "result": " ✔ Risultato dell'analisi",
        "spanish_only_error": "Sono consentiti solo annunci in spagnolo. Riprova.",
        "data": "Inserisci testo, URL o carica un'immagine",
        "data_add": "È possibile inserire solo un'opzione tra testo, URL e immagine", 
        "mode": "Rileva lingua / Traduzione",
        "lang_phrase": "Lingua rilevata",
        "valid_phrase": "Testo idoneo all'analisi",
        "original_phrase": "Testo originale",
        "translated_phrase": "Testo tradotto",
        "message": "Messaggio",
        "veredict": "Verdetto",
        "indicator": "Indicatori rilevati",
        "trust": "Affidabilità",
        "green": "Rischio basso",
        "yellow": "Rischio medio",
        "red": "Rischio alto",
        "close": "Capito",
        "detect": "Mostra rilevamento/traduzione",
        "config_title": "Configurazione",
        "select_language_title": "Seleziona lingua", 
        "continue_phrase": "Continua",
        "about_us": "Chi siamo?",
        "social_media": "I nostri Social Media" 
    },
    "pt": {
        "result": " ✔ Resultado da análise",
        "spanish_only_error": "Apenas anúncios em espanhol são permitidos. Tente novamente.",
        "data": "Introduza texto, URL ou carregue uma imagem",
        "data_add": "Só pode introduzir uma opção: texto, URL ou imagem", 
        "mode": "Detectar idioma / Tradução",
        "lang_phrase": "Idioma detectado",
        "valid_phrase": "Texto válido para análise",
        "original_phrase": "Texto original",
        "translated_phrase": "Texto traduzido",
        "message": "Mensagem",
        "veredict": "Veredito",
        "indicator": "Indicadores detectados",
        "trust": "Confiança",
        "green": "Risco baixo",
        "yellow": "Risco médio",
        "red": "Risco alto",
        "close": "Entendido",
        "detect": "Mostrar deteção/tradução",
        "config_title": "Configuração",
        "select_language_title": "Selecionar idioma", 
        "continue_phrase": "Continuar",
        "about_us": "Quem somos?",
        "social_media": "As nossas Redes Sociais" 
    },
    "ru": {
        "result": " ✔ Результат анализа",
        "spanish_only_error": "Разрешены только объявления на испанском языке. Попробуйте снова.",
        "data": "Введите текст, URL или загрузите изображение",
        "data_add": "Вы можете ввести только один вариант: текст, URL или изображение", 
        "mode": "Определить язык / Перевод",
        "lang_phrase": "Определённый язык",
        "valid_phrase": "Текст пригоден для анализа",
        "original_phrase": "Оригинальный текст",
        "translated_phrase": "Переведённый текст",
        "message": "Сообщение",
        "veredict": "Вердикт",
        "indicator": "Обнаруженные индикаторы",
        "trust": "Доверие",
        "green": "Низкий риск",
        "yellow": "Средний риск",
        "red": "Высокий риск",
        "close": "Понятно",
        "detect": "Показать распознавание/перевод",
        "config_title": "Настройки",
        "select_language_title": "Выберите язык", 
        "continue_phrase": "Продолжить",
        "about_us": "Кто мы?",
        "social_media": "Наши социальные сети" 
    },
    "ar": {
        "result": " ✔ نتيجة التحليل",
        "spanish_only_error": "يُسمح فقط بالإعلانات باللغة الإسبانية. حاول مرة أخرى.",
        "data": "أدخل نصًا أو رابطًا أو قم بتحميل صورة",
        "data_add": "يمكنك إدخال خيار واحد فقط من النص أو الرابط أو الصورة", 
        "mode": "اكتشاف اللغة / الترجمة",
        "lang_phrase": "اللغة المكتشفة",
        "valid_phrase": "النص صالح للتحليل",
        "original_phrase": "النص الأصلي",
        "translated_phrase": "النص المترجم",
        "message": "رسالة",
        "veredict": "الحكم",
        "indicator": "المؤشرات المكتشفة",
        "trust": "الثقة",
        "green": "خطر منخفض",
        "yellow": "خطر متوسط",
        "red": "خطر مرتفع",
        "close": "مفهوم",
        "detect": "إظهار الكشف/الترجمة",
        "config_title": "الإعدادات",
        "select_language_title": "اختر اللغة", 
        "continue_phrase": "متابعة",
        "about_us": "من نحن؟",
        "social_media": "حساباتنا على مواقع التواصل الاجتماعي"
    },
    "ro": {
        "result": " ✔ Rezultatul analizei",
        "spanish_only_error": "Sunt permise doar anunțuri în spaniolă. Încercați din nou.",
        "data": "Introdu text, URL sau încarcă o imagine",
        "data_add": "Poți introduce doar o singură opțiune: text, URL sau imagine",
        "mode": "Detectați limba / Traducere",
        "lang_phrase": "Limbă detectată",
        "valid_phrase": "Text valid pentru analiză",
        "original_phrase": "Text original",
        "translated_phrase": "Text tradus",
        "message": "Mesaj",
        "veredict": "Verdict",
        "indicator": "Indicatori detectați",
        "trust": "Încredere",
        "green": "Risc scăzut",
        "yellow": "Risc mediu",
        "red": "Risc ridicat",
        "close": "Am înțeles",
        "detect": "Afișează detectarea/traducerea",
        "config_title": "Configurare",
        "select_language_title": "Selectați limba", 
        "continue_phrase": "Continuați",
        "about_us": "Cine suntem?",
        "social_media": "Rețelele noastre sociale" 
    },
    "nl": {
        "result": " ✔ Analyseresultaat",
        "spanish_only_error": "Alleen advertenties in het Spaans zijn toegestaan. Probeer opnieuw.",
        "data": "Voer tekst of een URL in, of upload een afbeelding",
        "data_add": "Je kunt slechts één tekst, URL of afbeelding invoeren",
        "mode": "Taal detecteren / Vertaling",
        "lang_phrase": "Gedetecteerde taal",
        "valid_phrase": "Tekst geschikt voor analyse",
        "original_phrase": "Originele tekst",
        "translated_phrase": "Vertaalde tekst",
        "message": "Bericht",
        "veredict": "Vonnis",
        "indicator": "Gedetecteerde indicatoren",
        "trust": "Vertrouwen",
        "green": "Laag risico",
        "yellow": "Gemiddeld risico",
        "red": "Hoog risico",
        "close": "Begrepen",
        "detect": "Detectie/vertaling weergeven",
        "config_title": "Instellingen",
        "select_language_title": "Taal kiezen", 
        "continue_phrase": "Doorgaan",
        "about_us": "Wie zijn wij?",
        "social_media": "Onze Sociale Media"
    },
    "ca": {
        "result": " ✔ Resultat de l'anàlisi",
        "spanish_only_error": "Només es permeten anuncis en espanyol. Torneu-ho a intentar.",
        "data": "Introduïu text, una URL o pugeu una imatge",
        "data_add": "Només podeu introduir un text, una URL o una imatge",
        "mode": "Detectar idioma / Traducció",
        "lang_phrase": "Idioma detectat",
        "valid_phrase": "Text vàlid per a l'anàlisi",
        "original_phrase": "Text original",
        "translated_phrase": "Text traduït",
        "message": "Missatge",
        "veredict": "Veredicte",
        "indicator": "Indicadors detectats", 
        "trust": "Confiança",
        "green": "Risc baix",
        "yellow": "Risc mitjà",
        "red": "Risc alt",
        "close": "Entengut",
        "detect": "Mostra la detecció/traducció",
        "config_title": "Configuració",
        "select_language_title": "Selecciona l'idioma", 
        "continue_phrase": "Continuar",
        "about_us": "Qui som?",
        "social_media": "Les nostres Xarxes Socials"
    },
    "pl": {
        "result": " ✔ Wynik analizy",
        "spanish_only_error": "Dozwolone są tylko ogłoszenia w języku hiszpańskim. Spróbuj ponownie.",
        "data": "Wprowadź tekst, adres URL lub prześlij obraz",
        "data_add": "Możesz wprowadzić tylko jedną opcję: tekst, adres URL lub obraz",
        "mode": "Wykryj język / Tłumaczenie",
        "lang_phrase": "Wykryty język",
        "valid_phrase": "Tekst nadaje się do analizy",
        "original_phrase": "Tekst oryginalny",
        "translated_phrase": "Tekst przetłumaczony",
        "message": "Wiadomość",
        "veredict": "Werdykt",
        "indicator": "Wykryte wskaźniki",
        "trust": "Zaufanie",
        "green": "Niskie ryzyko",
        "yellow": "Średnie ryzyko",
        "red": "Wysokie ryzyko",
        "close": "Rozumiem",
        "detect": "Pokaż wykrycie/tłumaczenie",
        "config_title": "Ustawienia",
        "select_language_title": "Wybierz język", 
        "continue_phrase": "Kontynuuj",
        "about_us": "Kim jesteśmy?",
        "social_media": "Nasze Media Społecznościowe"
    },
    "uk": {
        "result": " ✔ Результат аналізу",
        "spanish_only_error": "Дозволені лише оголошення іспанською мовою. Спробуйте ще раз.",
        "data": "Введіть текст, URL-адресу або завантажте зображення",
        "data_add": "Ви можете ввести лише один елемент: текст, URL-адресу або зображення",
        "mode": "Визначити мову / Переклад",
        "lang_phrase": "Визначена мова",
        "valid_phrase": "Текст придатний для аналізу",
        "original_phrase": "Оригінальний текст",
        "translated_phrase": "Перекладений текст",
        "message": "Повідомлення",
        "veredict": "Вердикт",
        "indicator": "Виявлені індикатори",
        "trust": "Довіра",
        "green": "Низький ризик",
        "yellow": "Середній ризик",
        "red": "Високий ризик",
        "close": "Зрозуміло",
        "detect": "Показати розпізнавання/переклад",
        "config_title": "Налаштування",
        "select_language_title": "Оберіть мову", 
        "continue_phrase": "Продовжити",
        "about_us": "Хто ми?",
        "social_media": "Наші соціальні мережі"
    },
}

# "Diccionario para traducir el mensaje desde el backend a cada uno de los idiomas posibles."
translations = {  
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
    },
    "de": {
        "valid": "Der Text ist auf Spanisch ({idioma}) und kann analysiert werden.",
        "invalid": "Nicht unterstützte Sprache. Die erkannte Sprache ist ({idioma}). Nur Spanisch (es) ist zulässig."
    },
    "it": {
        "valid": "Il testo è in spagnolo ({idioma}) e può essere analizzato.",
        "invalid": "Lingua non supportata. La lingua rilevata è ({idioma}). È consentito solo lo spagnolo (es)."
    },
    "pt": {
        "valid": "O texto está em espanhol ({idioma}) e pode ser analisado.",
        "invalid": "Idioma não suportado. O idioma detetado é ({idioma}). Apenas o espanhol (es) é permitido."
    },
    "ru": {
        "valid": "Текст на испанском языке ({idioma}) и может быть проанализирован.",
        "invalid": "Неподдерживаемый язык. Обнаруженный язык: ({idioma}). Разрешён только испанский (es)."
    },
    "ar": {
        "valid": "النص باللغة الإسبانية ({idioma}) ويمكن تحليله.",
        "invalid": "لغة غير مدعومة. اللغة المكتشفة هي ({idioma}). يُسمح فقط بالإسبانية (es)."
    },
    "ro": {
        "valid": "Textul este în spaniolă ({idioma}) și poate fi analizat.",
        "invalid": "Limbă nesuportată. Limba detectată este ({idioma}). Este permisă doar spaniola (es)."
    },
    "nl": {
        "valid": "De tekst is in het Spaans ({idioma}) en kan worden geanalyseerd.",
        "invalid": "Niet-ondersteunde taal. De gedetecteerde taal is ({idioma}). Alleen Spaans (es) is toegestaan."
    },
    "ca": {
        "valid": "El text és en espanyol ({idioma}) i es pot analitzar.",
        "invalid": "Idioma no compatible. L'idioma detectat és ({idioma}). Només s'admet l'espanyol (es)."
    },
    "pl": {
        "valid": "Tekst jest w języku hiszpańskim ({idioma}) i można go analizować.",
        "invalid": "Nieobsługiwany język. Wykryty język to ({idioma}). Dozwolony jest tylko hiszpański (es)."
    },
    "uk": {
        "valid": "Текст іспанською мовою ({idioma}) і може бути проаналізований.",
        "invalid": "Непідтримувана мова. Виявлена мова: ({idioma}). Дозволено лише іспанську (es)."
    }
}

# "Función que selecciona el mensaje correcto del diccionario de traducciones según el idioma de la UI
# y si el texto es analizable o no, reemplazando el marcador {idioma} por el código real detectado"
def traducir_mensaje(lang, idioma_detectado, es_analizable):
    key = "valid" if es_analizable else "invalid"
    
    texto = translations.get(lang, translations["en"])[key]
    return texto.format(idioma=idioma_detectado)

# "Diccionario para traducir el mensaje de validez del idioma desde el backend a cada uno de los idiomas posibles."
translations_analisis = {  
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
    },
    "de": {
        "valid": "Diese Anzeige erfordert aufgrund möglicher Risiken besondere Aufmerksamkeit.",
        "invalid": "Nicht unterstützte Sprache. Die erkannte Sprache ist ({idioma}). Nur Spanisch (es) ist zulässig."
    },
    "it": {
        "valid": "Questo annuncio richiede attenzione a causa di potenziali rischi.",
        "invalid": "Lingua non supportata. La lingua rilevata è ({idioma}). È consentito solo lo spagnolo (es)."
    },
    "pt": {
        "valid": "Este anúncio requer atenção devido a potenciais riscos.",
        "invalid": "Idioma não suportado. O idioma detetado é ({idioma}). Apenas o espanhol (es) é permitido."
    },
    "ru": {
        "valid": "Это объявление требует внимания из-за возможных рисков.",
        "invalid": "Неподдерживаемый язык. Обнаруженный язык: ({idioma}). Разрешён только испанский (es)."
    },
    "ar": {
        "valid": "يتطلب هذا الإعلان الانتباه بسبب وجود مخاطر محتملة.",
        "invalid": "لغة غير مدعومة. اللغة المكتشفة هي ({idioma}). يُسمح فقط بالإسبانية (es)."
    },
    "ro": {
        "valid": "Acest anunț necesită atenție din cauza riscurilor potențiale.",
        "invalid": "Limbă nesuportată. Limba detectată este ({idioma}). Este permisă doar spaniola (es)."
    },
    "nl": {
        "valid": "Deze advertentie vereist aandacht vanwege mogelijke risico's.",
        "invalid": "Niet-ondersteunde taal. De gedetecteerde taal is ({idioma}). Alleen Spaans (es) is toegestaan."
    },
    "ca": {
        "valid": "Aquest anunci requereix atenció a causa de possibles riscos.",
        "invalid": "Idioma no compatible. L'idioma detectat és ({idioma}). Només s'admet l'espanyol (es)."
    },
    "pl": {
        "valid": "To ogłoszenie wymaga uwagi ze względu na możliwe zagrożenia.",
        "invalid": "Nieobsługiwany język. Wykryty język to ({idioma}). Dozwolony jest tylko hiszpański (es)."
    },
    "uk": {
        "valid": "Це оголошення потребує уваги через можливі ризики.",
        "invalid": "Непідтримувана мова. Виявлена мова: ({idioma}). Дозволено лише іспанську (es)."
    }
}

# "Variante de traducir_mensaje para el resultado del análisis de seguridad.
# Si el idioma detectado no es español directamente devuelve el mensaje de idioma no soportado"
def traducir_mensaje_analisis(lang, idioma_detectado):  
    key = "invalid" if idioma_detectado != "es" else "valid"
    
    texto = translations_analisis.get(lang, translations_analisis["en"])[key]
    return texto.format(idioma=idioma_detectado)

# "Función de animación visual del semáforo: recibe el color activo y un placeholder de Streamlit
# donde renderiza los tres círculos (rojo, ámbar, verde) con el seleccionado encendido"
def animacion(color, luz):
    luces = {
        "rojo":  "🔴 ⚫ ⚫",
        "ambar": "⚫ 🟡 ⚫",
        "verde": "⚫ ⚫ 🟢"
    }
    luz.markdown(
        f"<div style='font-size:24px'>{luces[color]}</div>",
        unsafe_allow_html=True
    )

# "Función que renderiza el modal de 'Quiénes Somos' con los textos del equipo y la política de privacidad.
# Si el idioma de la UI no es español, traduce todo el bloque de golpe usando GoogleTranslator
# y lo cachea en session_state para no repetir la llamada en cada rerender"
def render_modal_quienes_somos(idioma_destino: str = "es"):
    textos = [   # MODIFICAR EL TEXTO SEGÚN COMUNICACIÓN
        "¿Quiénes somos?",
        "Somos un equipo comprometido con la lucha contra el fraude laboral. Proyecto Verid.IA nace para ayudar a las personas a identificar ofertas de trabajo falsas mediante inteligencia artificial.",
        "¿Qué hacemos?",
        "Analizamos anuncios de trabajo (texto, URL o imagen) y evaluamos el riesgo de que sean fraudulentos, protegiendo a los usuarios de posibles estafas.",
        "Política de privacidad"
    ]

    if idioma_destino != "es":
        cache_key = f"modal_{idioma_destino}"
        if cache_key not in st.session_state:
            texto_completo = "\n---\n".join(textos)
            traducido = GoogleTranslator(source="es", target=idioma_destino).translate(texto_completo)
            partes = traducido.split("\n---\n")
            partes[-1] = partes[-1].capitalize()  
            st.session_state[cache_key] = partes
        textos = st.session_state[cache_key]

    t = textos   # HAY QUE CAMBIAR EL LINK PARA LA POLÍTICA DE PRIVACIDAD
    st.markdown(f"""
        <div style="background-color:#f9fbf2; border:2px solid #ddb6fc; border-radius:16px 16px 0 0;
            padding:32px; max-width:700px; margin:20px auto 0 auto;
            box-shadow:0 5px 20px rgba(192,132,252,0.15);">
            <h2 style="color:#9b5fcf; text-align:center;">👥 {t[0]}</h2>
            <p style="font-size:17px; color:#333; text-align:center;">{t[1]}</p>
            <h3 style="color:#9b5fcf; text-align:center;">🎯 {t[2]}</h3>
            <p style="font-size:16px; color:#555; text-align:center;">{t[3]}</p>
            <hr style="border-color:#ddb6fc; margin:20px 0;">
            <h3 style="color:#9b5fcf; text-align:center;">📖 {t[4]}</h3>
            <div style="text-align:center; font-size:18px;">
                <a href="https://twitter.com/TU_USUARIO" target="_blank" style="margin:0 12px; color:#1da1f2; text-decoration:none;">📄 PDF</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# "Función que construye la página de inicio: muestra el título del proyecto, el selector de idioma,
# el botón de 'Sobre Nosotros' con su modal desplegable y los enlaces a redes sociales.
# Cuando el usuario elige idioma y pulsa 'Continuar' se redirige a la página del analizador"
def pagina_inicio():
    st.markdown("<h1 style='text-align:center; color:#8f9e25; font-size:100px;'>✔erid.IA</h1>", unsafe_allow_html=True)
    st.divider()

    # "Idioma actual para traducir la UI"
    idioma_actual = languages.get(st.session_state.get("idioma", "🇪🇸 Español"), "es")

    st.title("🌍 " + UI_TEXTS[idioma_actual]["select_language_title"])

    st.markdown("""
    <style>
    div[data-baseweb="select"] > div {
        font-size: 26px !important;
        padding: 20px 20px !important;
        min-height: 80px !important;
        border-radius: 12px !important;
        align-items: center !important;
        display: flex !important;
    }
    div[data-baseweb="select"] span {
        font-size: 26px !important;
        line-height: 80px !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    ul[role="listbox"] {
        max-height: 600px !important;
        overflow-y: auto !important;
    }
    div[data-baseweb="popover"] li {
        font-size: 22px !important;
        padding: 14px 20px !important;
        line-height: 1.5 !important;
    }
    div[data-testid="stSelectbox"] label {
        font-size: 22px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # "Función que actualiza el idioma si se cambia en el selector, gracias a los session_state"
    def actualizar_idioma():
        st.session_state.idioma = st.session_state.selector_idioma

    idioma_guardado = st.session_state.get("idioma") or "🇪🇸 Español"

    selected_name = st.selectbox(
        UI_TEXTS[idioma_actual]["select_language_title"],
        list(languages.keys()),
        index=list(languages.keys()).index(idioma_guardado if idioma_guardado in languages else "🇪🇸 Español"),
        key="selector_idioma",
        on_change=actualizar_idioma
)

    if st.button(UI_TEXTS[idioma_actual]["continue_phrase"]):
        st.session_state.idioma = selected_name
        st.session_state.page = "analizador"
        st.rerun()
    
    # "CSS BOTÓN VIOLETA SUAVE"
    st.markdown("""
    <style>
    .st-key-btn_sobre_nosotros button,
    .st-key-btn_sobre_nosotros button p {
        background-color: #ddb6fc !important;
        color: #2d0060 !important;
        font-size: 20px !important;
    }
    .st-key-cerrar_sobre_nosotros button {
        background-color: #ddb6fc !important;
        color: #2d0060 !important;
        margin-top: 5px !important;
        margin-bottom: 4px !important;
        padding: 4px 8px !important;
        font-size: 14px !important;
        height: 32px !important;
    }

    /* Contenedor del botón cerrar: menos espacio */
    div.stKeyText_cerrar_sobre_nosotros,
    div[class*="st-key-cerrar_sobre_nosotros"] {
        margin-top: 8px !important;
        margin-bottom: 0 !important;
        padding-top: 4px !important;
        position: relative !important;
        z-index: 10 !important;
    }

    /* Ancho del contenedor */
    div.st-key-cerrar_sobre_nosotros {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # "BOTÓN "SOBRE NOSOTROS""
    col_left, col_center, col_right = st.columns([2, 1, 2])
    with col_center:
        if st.button(f"ℹ️ {UI_TEXTS[idioma_actual]['about_us']}", key="btn_sobre_nosotros", use_container_width=True):
            st.session_state["mostrar_sobre_nosotros"] = True
    
    # CAMBIAR EL LINK DE LAS REDES SOCIALES
    st.markdown(f"""
    <div style="text-align:center; margin-top:10px;">
        <h3 style="color:#9b5fcf;">🌐 {UI_TEXTS[idioma_actual]['social_media']}</h3>
        <div style="font-size:18px;">
            <a href="https://instagram.com/TU_USUARIO" target="_blank" style="margin:0 12px; color:#e1306c; text-decoration:none;">📸 Instagram</a>
            <a href="https://www.linkedin.com/in/proyecto-verid-ia-9390653b8/" target="_blank" style="margin:0 12px; color:#0077b5; text-decoration:none;">💼 LinkedIn</a>   
        </div>
    </div>
    """, unsafe_allow_html=True)

    # "MODAL SOBRE NOSOTROS"
    if st.session_state.get("mostrar_sobre_nosotros", False):
        render_modal_quienes_somos(idioma_destino=idioma_actual)

        st.markdown("""
        <style>
        div.st-key-cerrar_sobre_nosotros {
            margin-top: -20px !important;
        }
        div.st-key-cerrar_sobre_nosotros button {
            width: 160px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 2])
        with col3:
            if st.button(f"✕ {UI_TEXTS[idioma_actual]['close']}", key="cerrar_sobre_nosotros"):
                st.session_state["mostrar_sobre_nosotros"] = False
                st.rerun()

# "Función que muestra dentro del modal los resultados de detección de idioma y traducción del anuncio.
# Presenta el idioma detectado, si el texto es analizable, el texto original y el texto traducido en columnas paralelas"
def mostrar_resultado_traduccion(res_seg, res_det, lang_ui):  
    
    # "Contenedor principal con borde"
    with st.container(border=True):

        # "Cabecera/Idioma detectado"
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

        # "Mensaje dinámico"
        mensaje = traducir_mensaje(
            lang_ui,
            res_det["idioma_detectado"],
            res_det["es_analizable"]
        )

        # "Validación del resultado de la traducción"
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

        # "Comparador original/traducido"
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
            
# Traduce el texto del mensaje y las señales al idioma seleccionado            
# "Si el idioma destino es español no hace nada (ya viene en español del backend).
# Para el resto de idiomas usa GoogleTranslator y devuelve el original si la traducción falla"           
def traducir_texto(texto, lang_ui, source="es"):
    if not texto:
        return texto
    if lang_ui == "es":
        return texto
    try:
        return GoogleTranslator(source=source, target=lang_ui).translate(texto)
    except Exception:
        return texto

# "Función principal de visualización del resultado del análisis de seguridad.
# Muestra el semáforo visual (rojo/ámbar/verde), el porcentaje de confianza, el mensaje
# explicativo del Backend y la lista de señales de fraude detectadas si las hay"     
def mostrar_resultados(res_seg, res_det, lang_ui):
    st.subheader(UI_TEXTS[lang_ui]["result"])

    nivel = res_seg.get("nivel_seguridad")
    confianza = res_seg.get("confianza_seguridad", 0)
    confianza_pct = int(confianza * 100)

    nivel_config = {
        "verde": {"color": "#16a34a", "bg": "#f0fdf4", "border": "#86efac", "icon": "✓", "label": UI_TEXTS[lang_ui]['green']},
        "amarillo": {"color": "#ca8a04", "bg": "#fefce8", "border": "#fde047", "icon": "⚠", "label": UI_TEXTS[lang_ui]['yellow']},
        "rojo": {"color": "#dc2626", "bg": "#fff1f2", "border": "#fca5a5", "icon": "✕", "label": UI_TEXTS[lang_ui]['red']},
    }
    cfg = nivel_config.get(nivel, nivel_config["amarillo"])
    c, bg, bd, icon, lbl = cfg['color'], cfg['bg'], cfg['border'], cfg['icon'], cfg['label']
    semaforo_nivel = nivel if nivel in ("rojo", "verde") else "amarillo"

    col_semaforo, col_resultado = st.columns([1, 4])

    # "Donde se ve el semáforo"
    with col_semaforo:
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding-right:8px;">
            <div style="display:flex;flex-direction:column;align-items:center;
                width:70px;padding:12px 8px;background:#111;
                border-radius:14px;box-shadow:0 5px 20px rgba(0,0,0,0.5);">
                <div style="width:38px;height:38px;border-radius:50%;margin:6px 0;
                    background:{'red' if semaforo_nivel=='rojo' else '#2b2b2b'};
                    box-shadow:{'0 0 25px red' if semaforo_nivel=='rojo' else 'none'};"></div>
                <div style="width:38px;height:38px;border-radius:50%;margin:6px 0;
                    background:{'yellow' if semaforo_nivel=='amarillo' else '#2b2b2b'};
                    box-shadow:{'0 0 25px yellow' if semaforo_nivel=='amarillo' else 'none'};"></div>
                <div style="width:38px;height:38px;border-radius:50%;margin:6px 0;
                    background:{'limegreen' if semaforo_nivel=='verde' else '#2b2b2b'};
                    box-shadow:{'0 0 25px limegreen' if semaforo_nivel=='verde' else 'none'};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # "Donde se ven los resultados internos del análisis"
    with col_resultado:

        st.markdown(f"""
        <div style="background:{bg};border:2px solid {bd};border-radius:14px;padding:22px 26px;margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;">
                <div style="width:54px;height:54px;border-radius:50%;background:white;
                            border:2px solid {c};display:flex;align-items:center;
                            justify-content:center;font-size:26px;color:{c};
                            font-weight:700;flex-shrink:0;">
                    {icon}
                </div>
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                    <div style="font-size:28px;font-weight:700;color:{c};">{lbl}</div>
                </div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:7px;">
                <span style="font-size:16px;font-weight:600;color:#6b7280;
                            text-transform:uppercase;letter-spacing:1px;">
                    {UI_TEXTS[lang_ui]['trust']}
                </span>
                <span style="font-size:22px;font-weight:700;color:{c};">{confianza_pct}%</span>
            </div>
            <div style="height:10px;background:#e5e7eb;border-radius:99px;overflow:hidden;">
                <div style="height:100%;width:{confianza_pct}%;background:{c};border-radius:99px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # "Mensaje que devuelve el agente"
    mensaje = (res_seg.get("mensaje") or res_seg.get("justificacion") or "").strip()
    if not mensaje:
        mensaje = traducir_mensaje_analisis(lang_ui, res_det.get("idioma_detectado", "es"))
    else:
        mensaje = traducir_texto(mensaje, lang_ui, source=res_det.get("idioma_detectado", "es"))

    aviso_color = "#fde68a" if nivel != "verde" else "#d1fae5"
    border_color = "#f59e0b" if nivel != "verde" else "#10b981"

    st.markdown(f"""
    <div style="border-left:4px solid {border_color};background:{aviso_color};padding:16px 20px;
                border-radius:0 10px 10px 0;margin-bottom:14px;">
        <div style="font-size:13px;font-weight:600;letter-spacing:2px;
                    text-transform:uppercase;color:#111827;margin-bottom:8px;">
            {UI_TEXTS[lang_ui]['message']}
        </div>
        <div style="font-size:17px;color:#374151;line-height:1.7;">{mensaje}</div>
    </div>
    """, unsafe_allow_html=True)

    # "Señales detectadas por la tool"
    senales = res_seg.get("senales") or []
    if senales:
        senales_traducidas = [traducir_texto(s, lang_ui, source=res_det.get("idioma_detectado", "es")) for s in senales]

        items_senales = "".join(
            f"<div style='padding:8px 0;border-bottom:1px solid #f3f4f6;"
            f"display:flex;gap:10px;align-items:flex-start;'>"
            f"<span style='color:#e89a40;font-weight:700;font-size:18px;'>⚑</span>"
            f"<span style='font-size:16px;color:#374151;line-height:1.6;'>{s}</span></div>"
            for s in senales_traducidas
        )

        st.markdown(f"""
        <div style="background:#fffbf2;border:1.5px solid #fde68a;
                    border-left:4px solid #e89a40;border-radius:12px;
                    padding:6px 20px 10px;margin-bottom:14px;">
            <div style="font-size:13px;font-weight:600;letter-spacing:2px;
                        text-transform:uppercase;color:#92400e;padding:12px 0 8px;">
                🔎 {UI_TEXTS[lang_ui]['indicator']}
            </div>
            {items_senales}
        </div>
        """, unsafe_allow_html=True)

    # "Aviso de generación por IA"
    aviso_ia_es = "Los resultados de este análisis han sido generados por un agente de inteligencia artificial y pueden contener errores. No sustituyen el criterio de un profesional."

    if lang_ui != "es":
        cache_key = f"aviso_ia_{lang_ui}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = GoogleTranslator(source="es", target=lang_ui).translate(aviso_ia_es)
        aviso_ia = st.session_state[cache_key]
    else:
        aviso_ia = aviso_ia_es

    st.markdown(f"""
    <div style="margin-top:18px;padding:12px 18px;border-radius:10px;
                background:#f1f5f9;border:1px solid #cbd5e1;
                display:flex;align-items:flex-start;gap:10px;">
        <span style="font-size:20px;">🤖</span>
        <span style="font-size:17px;color:#111827;line-height:1.6;">{aviso_ia}</span>
    </div>
    """, unsafe_allow_html=True)

    
        
# "ESTADÍSTICAS"
# "Función que consulta la API de estadísticas y pinta en pantalla un resumen global con métricas,
# una barra de distribución por nivel de riesgo y dos columnas con idiomas detectados y señales más frecuentes.
# Traduce todos los textos estáticos al idioma seleccionado cacheando el resultado en session_state"
def mostrar_estadisticas(lang_ui):
    response = llamar_api_get(API_ESTADISTICAS)

    if not response or response.status_code != 200:
        st.error("❌ Error")
        return

    stats = response.json()

    # "Leer estructura real de la API"
    total      = stats.get("total_analizados", 0)
    dist       = stats.get("distribucion_semaforo", {})
    legitimate = dist.get("verde", 0)
    amarillo   = dist.get("amarillo", 0)
    fraudulent = dist.get("rojo", 0)
    idiomas_dict = stats.get("idiomas_frecuentes", {})
    senales_dict = stats.get("indicadores_frecuentes", {})

    # "Traducción de textos estáticos de este modo"
    textos_es = [
        "Estadísticas globales",
        "Total analizados",
        "Legítimos",
        "Con alertas",
        "Fraudulentos",
        "Distribución por nivel de riesgo",
        "Legítimos",
        "Con alertas",
        "Fraudulentos",
        "Sin datos suficientes para mostrar la distribución.",
        "Idiomas detectados",
        "Sin datos de idioma.",
        "Señales más frecuentes",
        "Sin señales registradas.",
    ]

    if lang_ui != "es":
        cache_key = f"estadisticas_{lang_ui}"
        if cache_key not in st.session_state:
            texto_completo = "\n---\n".join(textos_es)
            traducido = GoogleTranslator(source="es", target=lang_ui).translate(texto_completo)
            partes = traducido.split("\n---\n")
            st.session_state[cache_key] = partes
        t = st.session_state[cache_key]
    else:
        t = textos_es

    while len(t) < len(textos_es):
        t.append(textos_es[len(t)])

    (
        txt_titulo, txt_total, txt_legitimos, txt_alertas, txt_fraudulentos,
        txt_distribucion, txt_leg_barra, txt_alert_barra, txt_fraud_barra,
        txt_sin_datos, txt_idiomas, txt_sin_idiomas,
        txt_senales, txt_sin_senales
    ) = t[:14]

    # "Título"
    st.markdown(
        f"<h2 style='text-align:center;color:#8f9e25;'>📊 {txt_titulo}</h2>",
        unsafe_allow_html=True,
    )
    st.divider()

    # "Resumen de métricas"
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"🔢 {txt_total}", total)
    col2.metric(f"✅ {txt_legitimos}", legitimate)
    col3.metric(f"⚠️ {txt_alertas}", amarillo)
    col4.metric(f"🚨 {txt_fraudulentos}", fraudulent)

    st.divider()

    # "Distribución del semáforo"
    st.markdown(f"#### 🚦 {txt_distribucion}")

    if total > 0:
        pct_verde    = legitimate / total * 100
        pct_amarillo = amarillo   / total * 100
        pct_rojo     = fraudulent / total * 100

        barra_html = f"""
        <div style="border-radius:10px;overflow:hidden;height:28px;display:flex;margin-bottom:8px;">
            <div style="width:{pct_verde:.1f}%;background:#16a34a;" title="{txt_leg_barra} {pct_verde:.1f}%"></div>
            <div style="width:{pct_amarillo:.1f}%;background:#ca8a04;" title="{txt_alert_barra} {pct_amarillo:.1f}%"></div>
            <div style="width:{pct_rojo:.1f}%;background:#dc2626;" title="{txt_fraud_barra} {pct_rojo:.1f}%"></div>
        </div>
        <div style="display:flex;gap:20px;font-size:14px;">
            <span>🟢 {txt_leg_barra} &nbsp;<strong>{pct_verde:.1f}%</strong></span>
            <span>🟡 {txt_alert_barra} &nbsp;<strong>{pct_amarillo:.1f}%</strong></span>
            <span>🔴 {txt_fraud_barra} &nbsp;<strong>{pct_rojo:.1f}%</strong></span>
        </div>
        """
        st.markdown(barra_html, unsafe_allow_html=True)
    else:
        st.info(txt_sin_datos)

    st.divider()

    # "Idiomas y señales más comunes"
    col_idiomas, col_senales = st.columns(2)

    with col_idiomas:
        st.markdown(f"#### 🌍 {txt_idiomas}")
        if idiomas_dict:
            for idioma, count in list(idiomas_dict.items())[:8]:
                pct = count / total * 100 if total else 0
                st.markdown(
                    f"""
                    <div style="margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;font-size:14px;">
                            <span><strong>{idioma.upper()}</strong></span>
                            <span>{count} ({pct:.1f}%)</span>
                        </div>
                        <div style="background:#e5e7eb;border-radius:99px;height:8px;overflow:hidden;">
                            <div style="width:{pct:.1f}%;background:#b6c35d;height:100%;border-radius:99px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info(txt_sin_idiomas)

    with col_senales:
        st.markdown(f"#### 🔎 {txt_senales}")
        if senales_dict:
            max_val = max(senales_dict.values(), default=1)
            for senal, count in list(senales_dict.items())[:10]:
                pct = count / max_val * 100
                st.markdown(
                    f"""
                    <div style="margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;font-size:13px;">
                            <span style="color:#374151;">{senal}</span>
                            <span style="font-weight:700;color:#e89a40;">{count}</span>
                        </div>
                        <div style="background:#e5e7eb;border-radius:99px;height:8px;overflow:hidden;">
                            <div style="width:{pct:.1f}%;background:#e89a40;height:100%;border-radius:99px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info(txt_sin_senales)

# "SIDEBAR"
# "Función que construye la página principal del analizador. Contiene el sidebar con la configuración,
# el selector de modo (analizar / estadísticas), el formulario de entrada del anuncio y la lógica
# completa de llamada a las APIs de detección e análisis con la animación del semáforo incluida"
def pagina_analizador():

    # "Aquí es donde se ven los elementos en el lateral izquierdo"
    with st.sidebar:    

        st.header("⚙️ " + UI_TEXTS[languages[st.session_state.idioma]]["config_title"])       

        selected_name = st.session_state.idioma

        # "Variable que guarda el idioma seleccionado de todos los posibles"
        idioma_select = languages[selected_name]   
        lang_ui = idioma_select  

        # "Variable que guarda según el idioma seleccionado los elementos visibles por pantalla"                   
        idioma_input = languages_input[selected_name.split(" ")[1]]     
        lang_ui_input = idioma_input        
        
        st.divider()      

        if st.button(f"↩️{lang_ui_input['idioma_label']}"):
            st.session_state.page = "home"
            st.rerun()
        
        # "Markdown con color violeta"
        st.markdown(        
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

        # "Menú de navegación para saltar a cada sección del formulario.
        # El usuario puede pulsar los botones para ir directamente a Texto, URL o Imagen"
        st.markdown("---")
        st.markdown(f"#### 🧭 {lang_ui_input['seccion_label']}")
        scroll_navbar(
            anchor_ids=["seccion-texto", "seccion-url", "seccion-imagen", "seccion-analisis"],
            anchor_labels=[f"📝 {lang_ui_input['text_label']}", f"🔗 {lang_ui_input['url_label']}", f"🖼️ {lang_ui_input['imagen_label']}", f"🔍 {lang_ui_input['anuncio_label']}"],
            key="nav"
        )

    # "HEADER"
    with st.container():
        #"Este markdown hace de st.title()"
        st.markdown("<h1 style='text-align:center; color:#8f9e25; font-size:60px;'>✔ Proyecto Verid.IA</h1>",unsafe_allow_html=True) 
        st.caption(lang_ui_input["info_label"])     

    # "MODO"
    with st.container():
        st.markdown(f"<h3 style='color:#6f4a8e;'>{lang_ui_input["mode_label"]}:</h3>", unsafe_allow_html=True)
        modo = st.radio("Selecciona un modo", [f"{lang_ui_input["mode_label_one"]}", f"{lang_ui_input["mode_label_two"]}"], horizontal=True, label_visibility="hidden", key=f"modo_seleccionado_{lang_ui}")

    st.divider()    
    # "MODO ESTADÍSTICAS"
    if modo == lang_ui_input["mode_label_two"]:
        mostrar_estadisticas(lang_ui)
        # "No renderizar el resto del formulario de análisis"
        return  
    
    # "CSS para botón pequeño"
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

    # "LAYOUT"

    st.subheader(f"📄 {lang_ui_input["info_anuncio_label"]}")   

    # "Inicializar session_state si no existe"
    if "texto" not in st.session_state:
        st.session_state["texto"] = ""
    if "url" not in st.session_state:
        st.session_state["url"] = ""
    if "res_seg" not in st.session_state:       
        st.session_state["res_seg"] = None
    if "res_det" not in st.session_state:
        st.session_state["res_det"] = None
    if "lang_ui_resultado" not in st.session_state:
        st.session_state["lang_ui_resultado"] = None
    if "expanded_ad_info" not in st.session_state:
        st.session_state["expanded_ad_info"] = True  


    with st.expander(f"📋 {lang_ui_input['copiar_label']}", expanded=st.session_state["expanded_ad_info"]):
        
        # "TEXTO DEL ANUNCIO"
        # "Ancla para navegación"
        st.markdown('<div id="seccion-texto"></div>', unsafe_allow_html=True)  
        col_text_label, col_text_btn = st.columns([9, 1])
        
        with col_text_label:
            st.markdown(f"*{lang_ui_input['text_label']}*")
        with col_text_btn:
            if st.button("🧹", key="clear_text", help=lang_ui_input["borrar_texto_label"]):
                st.session_state["texto"] = ""
        
        # "Input"
        text_input = st.text_area(
            "Text",
            key="texto",
            height=150
        )
        
        # "URL DEL ANUNCIO"
        # "Ancla para navegación"
        st.markdown('<div id="seccion-url"></div>', unsafe_allow_html=True)  
        col_url_label, col_url_btn = st.columns([9, 1])
        
        with col_url_label:
            st.markdown(f"*{lang_ui_input['url_label']}*")
        with col_url_btn:
            if st.button("🧹", key="clear_url", help=lang_ui_input["borrar_url_label"]):
                st.session_state["url"] = ""
        
        # "Input"
        url_input = st.text_input(
            "URL",
            key="url"
        )
        
        # "IMAGEN DEL ANUNCIO"
        # "Ancla para navegación"
        st.markdown('<div id="seccion-imagen"></div>', unsafe_allow_html=True)  
        col_img_label, col_img_btn = st.columns([9, 1])

        with col_img_label:
            st.markdown(f"*{lang_ui_input['imagen_label']}*")

        with col_img_btn:
            if st.button("🧹", key="clear_image", help=lang_ui_input["borrar_imagen_label"]):
                st.session_state["imagen"] = None
                st.rerun()

        # "Uploader de la imagen"
        uploaded_file = st.file_uploader(
            label=f"{lang_ui_input['info_imagen_label']}",
            key="imagen_uploader",
            type=["jpg", "jpeg", "png", "tiff"]
        )

        # "Guardar en session_state"
        if uploaded_file is not None:
            st.session_state["imagen"] = uploaded_file

        # "Mostrar imagen si existe"
        if st.session_state.get("imagen") is not None:
            st.image(st.session_state["imagen"], use_container_width=True)
        else:
            st.markdown(
                f"""
                <div style="
                    background-color: #D6C2F0;
                    color: #000000;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 16px; 
                    font-weight: 500;
                    z-index: 9999;
                    pointer-events: none;
                ">
                    {lang_ui_input['file_label']}
                </div>
                """,
                unsafe_allow_html=True
            )

    # "Botón de analizar"
    st.divider()
    st.markdown("<div id='seccion-analisis'></div>", unsafe_allow_html=True)
    
    # "Texto informativo para contexto previo del análisis"
    info_texto_es = """
    ℹ️ Información:
    El sistema analizará el anuncio para detectar posibles señales de fraude laboral mediante IA. Devuelve el nivel
    de riesgo detectado, con un nivel de confianza (0-100) siendo 0 confianza mínima y 100 confianza máxima. Después, 
    devuelve un mensaje definitivo y las señales detectadas para determinar el veredicto.
    """

    # "Traducción automática según idioma de la UI"
    if lang_ui != "es":
        cache_key = f"info_analisis_{lang_ui}"

        if cache_key not in st.session_state:
            st.session_state[cache_key] = GoogleTranslator(
                source="es",
                target=lang_ui
            ).translate(info_texto_es)

        info_texto = st.session_state[cache_key]

    else:
        info_texto = info_texto_es

    # "Caja visual informativa"
    st.markdown(f"""
    <div style="
        background-color:#f9fbf2;
        padding:15px;
        border-radius:10px;
        border-left:5px solid #b6c35d;
        margin-bottom:20px;
        font-size:18px;
        line-height:1.7;
        color:#333333;
    ">
        {info_texto.replace(chr(10), "<br>")}
    </div>
    """, unsafe_allow_html=True)
    analyze = st.button(f"🔎 {lang_ui_input['anuncio_label']}")

    # "ANÁLISIS"
    if analyze:
        # "Validar que hay datos"
        inputs_filled = sum([          
            bool(text_input.strip()),
            bool(url_input.strip()),
            bool(uploaded_file)
        ])

        # "Mensajes de error, solo se escoge una opción (Texto o URL o Imagen)"
        if inputs_filled == 0:      
            st.warning(f"⚠️ {UI_TEXTS[lang_ui]['data']}")
            st.stop()

        if inputs_filled > 1:       
            st.warning(f"⚠️ {UI_TEXTS[lang_ui]['data_add']}")
            st.stop()
        
        # "Cerrar el expander"
        st.session_state["expanded_ad_info"] = False
        
        # "Definir tipo de entrada"
        if uploaded_file:
            tipo = "IMAGEN"
        elif url_input:
            tipo = "ENLACE"
        else:
            tipo = "TEXTO"
        
        # "Preparar datos"
        data = {"idioma_destino": idioma_select, "tipo": tipo}

        if text_input and not uploaded_file and not url_input:
            data["texto"] = text_input

        if url_input and not uploaded_file and not text_input:
            data["url"] = url_input

        files = None
        if uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        # "Condición para el análisis del anuncio (Modo 1)"
        if modo == f"{lang_ui_input['mode_label_one']}":  
            # "Mostrar spinner mientras se analiza"
            with st.status(f"{idioma_input['spinner_label']}", expanded=True) as status:
                luz = st.empty()

                animacion("rojo", luz)
                time.sleep(5)
                animacion("ambar", luz)
                time.sleep(5)
                animacion("verde", luz)

                response_idioma = llamar_api(API_DETECTAR_IDIOMA, data, files)
                time.sleep(5)

                status.update(label="🟢🟢🟢", state="complete", expanded=False)
            
            # "Procesar respuesta"
            if response_idioma and response_idioma.status_code == 200:
                res_det = response_idioma.json()
                
                # "Paso 1: Verificar si es analizable primero"
                if res_det.get("es_analizable"):
                    # "Paso 2: Analizar seguridad (sin mostrar nada todavía)"
                    files = None
                    if uploaded_file:
                        uploaded_file.seek(0)
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

                    response_seguridad = llamar_api(API_ANALIZAR, data, files)
                    
                    if response_seguridad and response_seguridad.status_code == 200:
                        res_seg = response_seguridad.json()
                        
                        # "Mostrar resultados del análisis"
                        st.divider()
                        mostrar_resultados(res_seg, res_det, lang_ui)
                        
                        # "Mostrar información de la detección/traducción (si el usuario quiere)"
                        st.divider()

                        # "Guardamos resultados en session_state para que sobrevivan al rerender"
                        st.session_state["res_seg"] = res_seg
                        st.session_state["res_det"] = res_det
                        st.session_state["lang_ui_resultado"] = lang_ui
                        st.session_state["_ultimo_lang_ui"] = lang_ui
                        st.session_state["_ultimo_texto"] = text_input
                        st.session_state["_ultima_url"] = url_input
                        st.session_state["_ultima_imagen"] = uploaded_file.name if uploaded_file else None  
                        
                    else:
                        st.error("❌ Error al conectar con la API de Análisis")
                        if response_seguridad:
                            st.write(f"Código de estado: {response_seguridad.status_code}")
                
                else:
                    # "Idioma no analizable - mostrar warning en popup"
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
                    
                    # "Botón de cierre"
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

# "Enrutamiento principal: según el valor de session_state.page se renderiza una función u otra"
if st.session_state.page == "home":
    pagina_inicio()

elif st.session_state.page == "analizador":
    pagina_analizador() 

# "Bloque de detección de cambios: si el usuario cambia el idioma o modifica el input después de analizar,
# se limpian los resultados guardados en session_state para evitar mostrar datos obsoletos"
_lang_actual = st.session_state.get("_ultimo_lang_ui")
_texto_actual = st.session_state.get("_ultimo_texto")
_url_actual = st.session_state.get("_ultima_url")
_imagen_actual = st.session_state.get("_ultima_imagen")
_lang_sesion = languages.get(st.session_state.get("idioma", "🇪🇸 Español"), "es")
_texto_sesion = st.session_state.get("texto", "")
_url_sesion = st.session_state.get("url", "")
_imagen_sesion = st.session_state.get("imagen").name if st.session_state.get("imagen") else None

if st.session_state.get("res_seg") is not None:
    if (_lang_actual != _lang_sesion or
        _texto_actual != _texto_sesion or
        _url_actual != _url_sesion or
        _imagen_actual != _imagen_sesion):
        st.session_state["res_seg"] = None
        st.session_state["res_det"] = None
        st.session_state["open_modal"] = False

# "MODAL TRADUCCIÓN"
# "Este bloque vive fuera del if analyze: para sobrevivir al rerender"
# "Gestiona el modal de detección/traducción: se crea una sola vez y se abre o cierra
# controlando st.session_state.open_modal en lugar de depender del estado interno del widget"
if st.session_state.get("res_seg") is not None:
    _lang = st.session_state.get("lang_ui_resultado", "es")

    modal = Modal(
        f"{UI_TEXTS[_lang]['result']}",
        key="modal_resultado",
        max_width=700
    )

    # "Estado único de apertura (no del widget)"
    if "open_modal" not in st.session_state:
        st.session_state.open_modal = False
    
    # "Botón de apertura del Modal"
    st.markdown("""
    <style>
    .st-key-abrir_modal_btn button {
        background-color: #FFA94D !important;
        color: #000000 !important;
        white-space: nowrap !important;
        font-size: 11px !important;
        padding: 4px 10px !important;
        min-width: 200px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns([1, 4])

    with col_btn1:
        if st.button(
            f"🔎 {UI_TEXTS[_lang]['detect']}",
            key="abrir_modal_btn"
        ):
            st.session_state.open_modal = True

        # "Reset automático cuando cambia el texto/idioma"
    if "prev_res_seg" not in st.session_state:
        st.session_state.prev_res_seg = None

    current = st.session_state.get("res_seg")

    if current != st.session_state.prev_res_seg:
        st.session_state.prev_res_seg = current
        st.session_state.open_modal = False

    # "Render controlado (sin is_open)"
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

#Ejecución del streamlit: streamlit run frontend/app.py
