# Generador de Anuncios Laborales Sintéticos

Script de generación de datos sintéticos para el entrenamiento de un clasificador automático de anuncios de empleo fraudulentos, en el contexto de detección de trata de personas.

---

## Descripción

Con este script hemos generado los anuncios sintéticos para entrenar el modelo híbrido de la aplicación web. La generación sintética se ha hecho en base a anuncios reales
etiquetados y en base a la guía de anotación.

El script produce dos archivos de salida:
- `dataset_sintetico.jsonl` — solo los anuncios generados
- `dataset_completo.jsonl` — anuncios reales anotados + sintéticos

---

## Arquitectura del pipeline

```
guia_anotacion.xlsx  ──►  cargar_guia()
                               │
dataset.jsonl  ────────►  analizar_dataset()   (cobertura de señales)
                               │
                          seleccionar_señales()  (por etiqueta)
                               │
                      prompt_fraude() / prompt_legitimo()
                               │
                          llamar_ollama()        (Mistral local)
                               │
                           validar()
                               │
                    dataset_sintetico.jsonl
                    dataset_completo.jsonl
```

---

## Etiquetas y objetivos de generación

| Etiqueta           | Anuncios objetivo |
|--------------------|:-----------------:|
| FRAUDE GRAVE       | 800               |
| FRAUDE             | 800               |
| FRAUDE PROBABLE    | 600               |
| REVISAR            | 300               |
| LEGÍTIMO           | 800               |
| LEGÍTIMO PROBABLE  | 700               |
| **Total**          | **4 000**         |

---

## Señales lingüísticas

Las señales se extraen de `guia_anotacion.xlsx` y se clasifican en dos tipos:

- **Presencia (P):** rasgo que debe aparecer en el texto (p.ej. promesa de salario muy alto, vaguedad en las tareas)
- **Ausencia (A):** información que deliberadamente se omite (p.ej. sin nombre de empresa, sin descripción de tareas)

Cada señal tiene un **peso numérico** que determina su relevancia para el cálculo de la puntuación bruta del anuncio. La selección de señales por anuncio prioriza las que están sin representación o poco representadas en el dataset real.

---

## Requisitos

### Software

- Python 3.9+
- [Ollama](https://ollama.com/download) instalado y en ejecución
- Modelo Mistral descargado

```bash
# En una terminal, arrancar el servidor de Ollama
ollama serve

# En otra terminal, descargar el modelo
ollama pull mistral
```

### Dependencias Python

```bash
pip install requests openpyxl
```

---

## Archivos necesarios

Todos deben estar en la misma carpeta que el script:

```
proyecto/
├── generar_sinteticos.py
├── dataset.jsonl           # Anuncios reales anotados
└── guia_anotacion.xlsx     # Guía de anotación con señales lingüísticas
```

### Estructura esperada de `dataset.jsonl`

Cada línea es un objeto JSON con al menos los campos:

```json
{
  "id": "real_00001",
  "texto": "Texto del anuncio...",
  "etiqueta": "FRAUDE",
  "señales": [
    {"codigo": "lex-1", "señal": "...", "tipo": "P", "peso": 2.0}
  ]
}
```

### Estructura esperada de `guia_anotacion.xlsx`

La hoja `Guía de Anotación` debe tener datos a partir de la fila 4, con las siguientes columnas relevantes:

| Col | Contenido |
|-----|-----------|
| A   | Nivel lingüístico (Léxico, Morfosintáctico, Pragmático-discursivo, Paralingüístico) |
| B   | Tipo (P = presencia / A = ausencia) |
| C   | Peso numérico |
| D   | Nombre de la señal |
| E   | Descripción / ejemplos |
| H   | Indicador de legitimidad (para anuncios legítimos) |

---

## Uso

```bash
python generar_sinteticos.py
```

El script comprueba la conexión con Ollama antes de comenzar y muestra el progreso por etiqueta.

---

## Parámetros de configuración

Editables al inicio del script:

```python
MODELO       = "mistral"          # Modelo Ollama a usar
TEMPERATURA  = 0.85               # Temperatura de generación
PAUSA        = 0                  # Segundos entre llamadas (0 = sin pausa)
OLLAMA_URL   = "http://localhost:11434/api/generate"
```

También se pueden modificar las listas `SECTORES` y `CIUDADES` para ajustar el dominio de los anuncios generados.

---

## Formato de salida

Cada línea del `.jsonl` de salida contiene:

```json
{
  "id": "sint_01000",
  "texto": "Texto del anuncio generado...",
  "etiqueta": "FRAUDE GRAVE",
  "puntuacion_bruta": 7.5,
  "señales_objetivo": [
    {"codigo": "lex-3", "señal": "...", "tipo": "P", "peso": 2.0}
  ],
  "sector": "hostelería",
  "ciudad": "Madrid",
  "sintetico": true,
  "modelo": "mistral"
}
```

---

## Notas técnicas

- La validación descarta anuncios de menos de 30 o más de 450 palabras, y duplicados por prefijo de 80 caracteres.
- Las llamadas a Ollama tienen hasta 3 reintentos automáticos ante fallos de conexión o errores de la API.
- Los parámetros `num_ctx: 2048` y `num_gpu: 33` están ajustados para GPUs con VRAM limitada (probado en RTX 2060); ajustar según hardware disponible.
- La función `interpretar()` permite convertir una puntuación bruta numérica en etiqueta categórica, útil para revisión posterior.