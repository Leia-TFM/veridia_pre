import asyncio
import json
import re
import unicodedata
import httpx
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError
from smolagents import ToolCallingAgent, LiteLLMModel, Tool
from api.config import settings
from servicios.texto_service import process_text_input, process_url_input

import logging
logger = logging.getLogger(__name__)


# =============================================================================
# SECCIÓN 1 – CONSTANTES Y REGEX DE SEGURIDAD
# =============================================================================

MAX_BYTES_TITULO = 300
MAX_BYTES_DESCRIPCION = 8000

# Detecta intentos de manipular al LLM embebiendo instrucciones en los campos.
PROMPT_INJECTION_RE = re.compile(
    r"(ignore\s+(previous|all)\s+instructions?|"
    r"you\s+are\s+now\s+|act\s+as\s+|"
    r"jailbreak|DAN\s+mode|"
    r"system\s*:\s*|<\|im_start\|>|"
    r"\[INST\]|\[SYS\])",
    re.IGNORECASE,
)

# Evita scripts, SQL malicioso o atributos de evento HTML.
CODE_INJECTION_RE = re.compile(
    r"(<script[\s>]|</script>|javascript\s*:|"
    r"on\w+\s*=\s*[\"']|"
    r"vbscript\s*:|data\s*:\s*text/html|"
    r"'\s*;\s*DROP\s+TABLE|"
    r"--\s*$|1\s*=\s*1|'\s*OR\s*'1'\s*=\s*'1)",
    re.IGNORECASE,
)

# Bloquea caracteres de control y Unicode invisibles/bidi.
CONTROL_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|"
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064]"
)


# =============================================================================
# SECCIÓN 2 – FUNCIONES DE SANITIZACIÓN
# =============================================================================

def _normalize_unicode(value: str) -> str:
    """Normaliza a NFC para deshacer homoglyphs simples."""
    return unicodedata.normalize("NFC", value)


def _sanitize(value: str, field_name: str = "campo") -> str:
    """
    Pipeline de sanitización para campos de texto libre.
    Orden: strip → NFC → control chars → HTML/SQL → prompt injection.
    """
    value = value.strip()
    value = _normalize_unicode(value)

    if CONTROL_CHARS_RE.search(value):
        raise ValueError(f"'{field_name}' contiene caracteres de control no permitidos.")
    if CODE_INJECTION_RE.search(value):
        raise ValueError(f"'{field_name}' contiene código HTML/SQL malicioso.")
    if PROMPT_INJECTION_RE.search(value):
        raise ValueError(f"'{field_name}' contiene instrucciones de inyección de IA.")

    return value


def _check_byte_size(value: str, max_bytes: int, field_name: str) -> str:
    """Verifica que el campo no supere el límite de bytes en UTF-8."""
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"'{field_name}' supera el límite de {max_bytes} bytes.")
    return value


# =============================================================================
# SECCIÓN 3 – ESQUEMA PYDANTIC (JobAdInput)
# =============================================================================

class JobAdInput(BaseModel):
    """
    Esquema flexible para anuncios de estructura variable.
    Solo se valida seguridad (inyecciones, encoding) y tamaño máximo.
    Ningún campo es obligatorio — el pipeline ML trabaja con lo que haya.
    """

    titulo:        Optional[str] = Field(default=None, max_length=120)
    empresa:       Optional[str] = Field(default=None, max_length=100)
    descripcion:   Optional[str] = Field(default=None, max_length=3000)
    salario_min:   Optional[float] = Field(default=None, gt=0, lt=30_000)
    salario_max:   Optional[float] = Field(default=None, gt=0, lt=30_000)
    jornada_horas: Optional[int]   = Field(default=None, ge=1, le=60)
    ubicacion:     Optional[str]   = Field(default=None, max_length=100)
    contacto:      Optional[str]   = Field(default=None, max_length=100)
    tipo_contrato: Optional[str]   = Field(default=None, max_length=60)
    url_oferta:    Optional[str]   = Field(default=None, max_length=300)

    # Captura cualquier campo extra que venga en el anuncio
    model_config = {"extra": "allow"}

    @field_validator("titulo", "empresa", "descripcion",
                    "ubicacion", "tipo_contrato", "contacto", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v, info):
        if v is None:
            return v
        return _sanitize(str(v), field_name=info.field_name)

    @field_validator("descripcion", mode="after")
    @classmethod
    def descripcion_byte_limit(cls, v):
        if v is None:
            return v
        return _check_byte_size(v, MAX_BYTES_DESCRIPCION, "descripcion")

# =============================================================================
# SECCIÓN 5 – ORQUESTADOR DE VALIDACIÓN
# =============================================================================

async def validar_anuncio(data: dict) -> dict:
# Valida el anunció estructuralmente y de segurdad
    ad = JobAdInput(**data)
    return ad.model_dump()

# =============================================================================
# SECCIÓN 6 – HELPER DE TEXTO
# =============================================================================

# Campos en orden de relevancia semántica para el modelo ML.
# Campos conocidos con orden de relevancia
_CAMPOS_TEXTO = [
    "titulo", "empresa", "descripcion",
    "tipo_contrato", "ubicacion",
    "jornada_horas", "salario_min", "salario_max", "contacto",
]

def _campos_a_texto(fields: dict) -> str:
    partes = []
    
    # Primero los campos conocidos en orden
    for campo in _CAMPOS_TEXTO:
        valor = fields.get(campo)
        if valor is not None and str(valor).strip():
            partes.append(f"{campo}: {valor}")
    
    # Luego cualquier campo extra que haya llegado
    campos_extra = set(fields.keys()) - set(_CAMPOS_TEXTO) - {"url_oferta"}
    for campo in sorted(campos_extra):
        valor = fields.get(campo)
        if valor is not None and str(valor).strip():
            partes.append(f"{campo}: {valor}")
    
    return "\n".join(partes)

# =============================================================================
# SECCIÓN 7 – TOOL DE DETECCIÓN ML
# =============================================================================
def _generar_justificacion(label: int, proba: float, senales: list) -> str:
    pct = round(proba * 100)
    if label == 1:
        base = f"El modelo detecta un riesgo de fraude del {pct}%."
        if senales:
            base += f" Señales de alerta identificadas: {', '.join(senales[:4])}."
    else:
        base = f"El modelo no detecta señales significativas de fraude (probabilidad estimada: {pct}%)."
    return base

class FraudDetectionTool(Tool):

    name = "fraud_detection"
    description = (
        "Analyzes a pre-validated job posting and predicts whether it is FRAUDULENT or LEGITIMATE. "
        "Input is a JSON string with already sanitized fields: "
        "All fields are optional. Send whatever fields are available in the job posting. "
        "Also accepts any additional fields not listed above. " 
        "and optionally 'jornada_horas', 'ubicacion', 'tipo_contrato', 'url_oferta'. "
        "If 'url_oferta' is present, content is extracted directly from the URL. "
        "Returns JSON with 'verdict' (FRAUDULENT/LEGITIMATE), 'probability' (0-1), "
        "'confidence_level' (high/medium/low), 'senales', 'caracteristicas', 'estadisticas'."
    )

    inputs = {
        "job_posting_json": {
            "type": "string",
            "description": "JSON string with pre-validated job posting fields.",
        }
    }
    output_type = "string"

    _CONFIDENCE_MAP = [
        (0.75, "high"),
        (0.55, "medium"),
        (0.0,  "low"),
    ]

    def __init__(self, pipeline_path: str, **kwargs):
        super().__init__(**kwargs)
        self._pipeline_path = pipeline_path
        self._pipeline = None  # lazy loading

    def _load_pipeline(self):
        if self._pipeline is None:
            import joblib
            data = joblib.load(self._pipeline_path)
            self._pipeline = {
                "model" : data["model"],
                "threshold" : data["threshold"],
                "sbert_model_name": data["sbert_model_name"],
                "encoder": None
            }
    def _get_encoder(self):
        if self._pipeline["encoder"] is None:
            from sentence_transformers import SentenceTransformer
            self._pipeline["encoder"] = SentenceTransformer(self._pipeline["sbert_model_name"])
        return self._pipeline["encoder"]

    def _get_confidence_level(self, probability: float) -> str:
        for threshold, level in self._CONFIDENCE_MAP:
            if probability >= threshold:
                return level
        return "low"
    

    def forward(self, job_posting_json: str) -> str:

        # 1. Deserializar (el dato ya viene validado desde la ruta)
        try:
            fields = json.loads(job_posting_json)
        except json.JSONDecodeError as exc:
            return json.dumps({"error": f"JSON inválido: {exc}"}, ensure_ascii=False)

        # 2. Procesamiento de texto
        # Si hay URL, trafilatura extrae el contenido real de la página.
        # Si no, concatenamos los campos del anuncio.
        url_oferta = fields.get("url_oferta")
        resultado_proc = (
            process_url_input(str(url_oferta))
            if url_oferta
            else process_text_input(_campos_a_texto(fields))
        )

        if not resultado_proc["exito"]:
            return json.dumps({
                "error": resultado_proc.get("metadatos", {}).get("mensaje", "Procesamiento fallido."),
                "verdict": None,
                "probability": None,
                "confidence_level": None,
            }, ensure_ascii=False)

        # 3. Predicción ML
        texto_para_modelo = resultado_proc["texto_normalizado"]
        self._load_pipeline()

        # Encodear texto con Sentence-BERT
        encoder = self._get_encoder()
        embedding = encoder.encode([texto_para_modelo])  # shape (1, 384)

        # Predecir con XGBoost
        model = self._pipeline["model"]
        threshold = self._pipeline["threshold"]
        proba_fraud = float(model.predict_proba(embedding)[0][1])
        label = 1 if proba_fraud >= threshold else 0

        return json.dumps({
            "verdict"         : "FRAUDULENT" if label == 1 else "LEGITIMATE",
            "probability"     : round(proba_fraud, 4),
            "confidence_level": self._get_confidence_level(proba_fraud),
            "fuente"          : resultado_proc["fuente"],
            "senales"         : resultado_proc["senales"],
            "caracteristicas" : resultado_proc["caracteristicas"],
            "estadisticas"    : resultado_proc["estadisticas"],
            "justificacion"   : _generar_justificacion(label, proba_fraud, resultado_proc["senales"])
        }, ensure_ascii=False)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_pipeline"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


# =============================================================================
# SECCIÓN 8 – AGENTE ORQUESTADOR
# =============================================================================

class OrquestadorAgente:
    def __init__(
        self,
        pipeline_path: str,
        model_id: str = settings.MODELO,
        max_steps: int = 6,
        validator=None
    ):
        self.model = LiteLLMModel(model_id="ollama/qwen2.5:7b")
        self.tools = [FraudDetectionTool(pipeline_path=pipeline_path)]
        self.validator = validator

        self.agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
            max_steps=max_steps,
        )
        self.agent.prompt_templates["system_prompt"] = (
            settings.PROMPT +
            "\n\nIMPORTANT: Always call the fraud_detection tool before providing any answer. "
            "Never respond directly with a JSON result without first calling the tool."
        )

    def ejecutar_tarea(self, query: str) -> str:
        # 1. Datos estructurados de la tool
        try:
            tool_data = json.loads(self.tools[0].forward(job_posting_json=query))
        except Exception as e:
            logger.error(f"Tool falló: {e}")
            return json.dumps({"error": str(e)})

        # 2. Razonamiento del agente como justificación
        tarea = (
            "Analyze this job posting for fraud risk. "
            "Call the fraud_detection tool to get the ML prediction, "
            "then explain in Spanish your reasoning about why this posting "
            "may or may not be fraudulent, highlighting the most suspicious elements.\n\n"
            f"Job posting data: {query}"
        )
        try:
            tool_data["justificacion"] = str(self.agent.run(tarea)).strip()
        except Exception as e:
            logger.warning(f"Agente falló al razonar: {e}")

        return json.dumps(tool_data, ensure_ascii=False)