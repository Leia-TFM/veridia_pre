import json
import re
import unicodedata
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from smolagents import ToolCallingAgent, LiteLLMModel, Tool
from api.config import settings

import logging
logger = logging.getLogger(__name__)


# =============================================================================
# SECCIÓN 1 – CONSTANTES Y REGEX DE SEGURIDAD
# =============================================================================

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

    descripcion:   Optional[str] = Field(default=None, max_length=3000)
    url_oferta:    Optional[str]   = Field(default=None, max_length=300)

    # Captura cualquier campo extra que venga en el anuncio

    @field_validator("descripcion", mode="before")
    @classmethod
    def sanitize_descripcion(cls, v, info):
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
# SECCIÓN 7 – TOOL DE DETECCIÓN ML
# =============================================================================
def _generar_justificacion(label: int, proba: float, senales: list) -> str:
    pct = round(proba * 100)
    if label == 1:
        base = f"El modelo detecta un riesgo de fraude del {pct}%."
        if senales:
            senales_formateadas = [str(s) for s in senales[:4]]
            base += f" Señales de alerta identificadas: {', '.join(senales_formateadas)}."
    else:
        base = f"El modelo no detecta señales significativas de fraude (probabilidad estimada: {pct}%)."
    return base

class FraudDetectionTool(Tool):

    name = "fraud_detection"
    description = (
        "Detects fraud in job postings. "
        "Analyzes text signals, linguistic patterns, and ML predictions. "
        "Input can be a JSON string or object with job posting fields (descripcion, titulo, empresa, etc.). "
        "Returns JSON with verdict (FRAUDULENT/LEGITIMATE), probability, confidence, signals, and reasoning."
    )

    inputs = {
        "job_posting_json": {
            "type": "string",
            "description": "Job posting data as JSON string or object. Can include: descripcion, titulo, empresa, salario_min, salario_max, url_oferta, etc.",
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
            model = data["model"]
            model.set_params(device='cpu')
            self._pipeline = {
                "model"           : model,
                "threshold"       : data["threshold"],
                "sbert_model_name": data["sbert_model_name"],
                "encoder"         : None
            }
    def _get_encoder(self):
        if self._pipeline["encoder"] is None:
            from sentence_transformers import SentenceTransformer
            self._pipeline["encoder"] = SentenceTransformer(
                self._pipeline["sbert_model_name"],
                device="cpu")
        return self._pipeline["encoder"]

    def _get_confidence_level(self, probability: float) -> str:
        for threshold, level in self._CONFIDENCE_MAP:
            if probability >= threshold:
                return level
        return "low"
    

    async def forward(self, job_posting_json) -> str:

        # 1. Deserializar
        try:
            fields = json.loads(job_posting_json)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.error(f"Error al deserializar entrada: {exc}")
            return json.dumps({"error": f"Formato de entrada inválido: {exc}"}, ensure_ascii=False)

        # 2. Usar resultado ya procesado
        resultado_proc = fields.get("resultado_procesado")
        if not resultado_proc:
            return json.dumps({"error": "No se recibió resultado procesado."}, ensure_ascii=False)

        # 3. Predicción ML
        try:
            texto_para_modelo = resultado_proc.get("texto_normalizado", "")
            if not texto_para_modelo:
                return json.dumps({"error": "Texto inválido para procesamiento"}, ensure_ascii=False)

            self._load_pipeline()

            encoder = self._get_encoder()
            embedding = encoder.encode([texto_para_modelo])
            logger.debug(f"Embedding generado, shape: {embedding.shape}")

            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)

            predicciones = self._pipeline["model"].predict_proba(embedding)
            logger.debug(f"Predicciones recibidas, shape: {predicciones.shape}")

            proba_fraud = float(predicciones[0, 1])
            logger.debug(f"Probabilidad extraída: {proba_fraud}")

            label = 1 if proba_fraud >= self._pipeline["threshold"] else 0
            
            # Procesar señales de forma segura
            # Procesar señales de forma segura
            try:
                senales = resultado_proc.get("senales", {})
                if isinstance(senales, dict):
                    senales_sin_fuente = {k: v for k, v in senales.items() if k != "fuente"}
                    raw_list = list(senales_sin_fuente.values())
                else:
                    raw_list = senales if isinstance(senales, list) else []
                
                # Aplanamos y limpiamos: extraemos el string si es ['texto'] y quitamos vacíos
                senales_list = []
                for s in raw_list:
                    if isinstance(s, list) and len(s) > 0:
                        item = str(s[0]).strip()
                    else:
                        item = str(s).strip()
                    
                    if item and item not in ["[]", "None", ""]:
                        senales_list.append(item)
                        
            except Exception as e:
                logger.warning(f"Error procesando señales: {e}")
                senales_list = []

            return json.dumps({
                "verdict"         : "FRAUDULENT" if label == 1 else "LEGITIMATE",
                "probability"     : round(proba_fraud, 4),
                "confidence_level": self._get_confidence_level(proba_fraud),
                "fuente"          : resultado_proc.get("fuente", "desconocida"),
                "senales"         : senales_list,
                "caracteristicas" : resultado_proc.get("caracteristicas", {}),
                "estadisticas"    : resultado_proc.get("estadisticas", {}),
                "justificacion"   : _generar_justificacion(label, proba_fraud, senales_list)
            }, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error inesperado en forward(): {type(e).__name__}: {e}", exc_info=True)
            return json.dumps({
                "error": f"Error inesperado: {type(e).__name__}",
                "verdict": None,
                "probability": None,
                "confidence_level": None,
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
        self.model = LiteLLMModel(model_id="ollama/qwen2.5:3b")
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

    async def ejecutar_tarea(self, query: str) -> str:
        try:
            # 1. Preparar la entrada
            if isinstance(query, str):
                try:
                    query_data = json.loads(query)
                except json.JSONDecodeError:
                    query_data = {"descripcion": query}
            else:
                query_data = query
            
            job_posting_json = json.dumps(query_data, ensure_ascii=False)

            # 2. EJECUCIÓN TÉCNICA (Tool de confianza)
            # Obtenemos los datos duros que el frontend necesita para el semáforo y gráficas
            logger.info("Obteniendo datos técnicos de la Tool...")
            tool_result_str = await self.tools[0].forward(job_posting_json=job_posting_json)
            datos_finales = json.loads(tool_result_str)

            if "error" in datos_finales:
                return tool_result_str

            # 3. EJECUCIÓN NARRATIVA (Agente)
            # Le pedimos que genere SOLO el mensaje para el usuario
            tarea = (
                f"Analiza este anuncio siguiendo tus instrucciones de experto.\n"
                f"DATOS TÉCNICOS: {tool_result_str}\n"
                f"CONTENIDO DEL ANUNCIO: {job_posting_json}\n"
                "TAREA: Escribe una explicación breve (2-3 frases) para el usuario. "
                "Usa un tono directo y neutral. No devuelvas JSON, solo el texto."
            )

            logger.info("Iniciando razonamiento narrativo del agente...")
            # Aquí capturamos la respuesta del agente como un string simple
            import litellm
            respuesta = litellm.completion(
                model="ollama/qwen2.5:3b",
                messages=[{"role": "user", "content": tarea}]
            )
            mensaje_agente = respuesta.choices[0].message.content.strip()

            # 4. ENSAMBLAJE FINAL
            # Sustituimos la justificación genérica de la tool por la narrativa rica del agente
            if mensaje_agente and len(mensaje_agente) > 10:
                # Limpiamos posibles artefactos por si el agente escribe "Respuesta: ..."
                mensaje_limpio = re.sub(r'^(Respuesta|Justificación|Mensaje):\s*', '', mensaje_agente, flags=re.IGNORECASE)
                datos_finales["justificacion"] = mensaje_limpio

            # Devolvemos el JSON de la Tool enriquecido con el texto del Agente
            return json.dumps(datos_finales, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error crítico en ejecutar_tarea: {e}", exc_info=True)
            # Si todo falla, al menos devolvemos algo que el frontend entienda
            return json.dumps({
                "error": "Error en el análisis",
                "verdicto": "AMBIGUO",
                "justificacion": "No se pudo completar el análisis técnico."
            }, ensure_ascii=False)