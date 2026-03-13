from fastapi import APIRouter, HTTPException
from api.models.schemas import  AnuncioEntrada, TipoEntrada, ResultadoAnalisis, NivelSeguridad


router = APIRouter()

@router.post("/analizar", response_model=ResultadoAnalisis)
async def analizar_anuncio(anuncio: AnuncioEntrada):

    # Aquí se implementaría la lógica de análisis del anuncio
    # Por ahora, se devuelve un resultado simulado

    if anuncio.idioma != "es":
        raise HTTPException(
            status_code=400,
            detail=f"Idioma no soportado: {anuncio.idioma}. Solo se admite español (es)."
        )
    # Simulación de preprocesado segun tipo de entrada
    if anuncio.tipo == TipoEntrada.IMAGEN:
        texto_limpio = "Texto extraído de la imagen (simulado)"
    elif anuncio.tipo == TipoEntrada.ENLACE:
        texto_limpio = "Texto extraído del enlace (simulado)"
    else:
        texto_limpio = "Texto limpio del anuncio (simulado)"


        # Aquí se podría agregar lógica específica para analizar texto
        # Futuro: resultado = ia_service.analizar_texto(texto_limpio)
    resultado = ResultadoAnalisis(
        tipo_entrada=anuncio.tipo,
        nivel_seguridad=NivelSeguridad.AMARILLO,
        confianza_seguridad=0.75,
        mensaje="El anuncio requiere atención debido a posibles riesgos.",
        indicadores=["Uso de lenguaje ambiguo", "Falta de información clara"],
        idioma_detectado=anuncio.idioma
    )
    return resultado