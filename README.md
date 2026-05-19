# Proyecto Verid.IA

## Descripción

`Proyecto Verid.IA` es una aplicación de validación de anuncios laborales diseñada para detectar señales de fraude y posibles riesgos relacionados con trata de personas.

El sistema combina:
- Backend en FastAPI
- Interfaz en Streamlit
- OCR para imágenes
- Detección de idioma con FastText
- Traducción con GoogleTranslator
- Análisis de texto mediante reglas y agentes de IA
- Persistencia local de resultados en formato JSONL

## Características principales

- Analiza anuncios de empleo desde:
  - Texto directo
  - URL de páginas web
  - Imágenes con OCR
- Detecta el idioma y, si es necesario, traduce el contenido.
- Clasifica cada anuncio con un semáforo de seguridad:
  - `verde` (bajo riesgo)
  - `amarillo` (riesgo medio)
  - `rojo` (alto riesgo)
- Genera justificaciones basadas en señales detectadas.
- Proporciona estadísticas agregadas sobre los análisis almacenados.
- Monta páginas de política de privacidad desde `frontend/` en `/privacidad`.

## Estructura del proyecto

- `main.py` - arranque de la aplicación FastAPI.
- `api/` - configuración, rutas y esquemas de datos.
- `servicios/` - lógica de procesamiento de texto, IA, OCR, traducción y almacenamiento.
- `frontend/` - interfaz Streamlit y páginas estáticas.
- `data/analisis_dataset.jsonl` - historial local de análisis.
- `requirements.txt` - dependencias necesarias.

## Requisitos

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Descargar modelo de spaCy en español:
   ```bash
   python -m spacy download es_core_news_sm
   ```
3. Instalar Tesseract OCR en el sistema y añadirlo al PATH.
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki

## Ejecución

### Backend

Inicia el servidor FastAPI con:
```bash
uvicorn main:app --reload
```

### Frontend

Inicia la interfaz Streamlit con:
```bash
streamlit run frontend/app.py
```

## Endpoints disponibles

- `GET /` - comprobación de estado.
- `POST /api/analizar` - analiza un anuncio laboral.
- `POST /api/detectar_idioma` - detecta el idioma y traduce el contenido.
- `GET /api/estadisticas` - devuelve estadísticas agregadas de los análisis.

## Uso de la API

### `/api/analizar`

Parámetros de formulario:
- `tipo` - `TEXTO`, `ENLACE` o `IMAGEN`
- `idioma_destino` - `es`, `en`, `fr`, `de`, `pt`, `it`, `nl`, `ca`, `ru`, `pl`, `uk`, `ar`
- `texto` - texto del anuncio (opcional si se usa URL o imagen)
- `url` - enlace del anuncio (opcional si se usa texto o imagen)
- `file` - archivo de imagen para OCR (solo si `tipo=IMAGEN`)

### `/api/detectar_idioma`

Parámetros de formulario:
- `texto` - texto para detectar idioma
- `url` - URL para extraer y detectar idioma
- `file` - archivo de imagen con texto
- `idioma_destino` - idioma objetivo para la traducción

### `/api/estadisticas`

Devuelve un resumen con:
- total de anuncios analizados
- distribución del semáforo
- indicadores frecuentes
- idiomas más detectados

## Ejemplos de uso con curl

### Analizar texto directo

```bash
curl -X POST http://127.0.0.1:8000/api/analizar \
  -F "tipo=TEXTO" \
  -F "idioma_destino=es" \
  -F "texto=Oferta de empleo urgente: se busca persona para trabajo desde casa sin experiencia, comisión alta."
```

### Analizar URL

```bash
curl -X POST http://127.0.0.1:8000/api/analizar \
  -F "tipo=ENLACE" \
  -F "idioma_destino=es" \
  -F "url=https://ejemplo.com/oferta-trabajo"
```

### Analizar imagen

```bash
curl -X POST http://127.0.0.1:8000/api/analizar \
  -F "tipo=IMAGEN" \
  -F "idioma_destino=es" \
  -F "file=@ruta/a/imagen.jpg"
```

### Detectar idioma y traducir contenido

```bash
curl -X POST http://127.0.0.1:8000/api/detectar_idioma \
  -F "idioma_destino=es" \
  -F "texto=This is a suspicious job posting, no resume needed, pay in advance."
```

### Obtener estadísticas

```bash
curl http://127.0.0.1:8000/api/estadisticas
```

## Datos y persistencia

Los análisis se guardan localmente en `data/analisis_dataset.jsonl`.
Cada registro incluye metadatos de entrada, idioma detectado, texto original, traducción y resultado del análisis.

## Notas

- El sistema está preparado para funcionar en español y detecta varios idiomas de entrada.
- Si no se encuentra el pipeline ML local, el proyecto aplica análisis por reglas como fallback.
- Se recomienda usar el frontend Streamlit para probar las funcionalidades de forma interactiva.
