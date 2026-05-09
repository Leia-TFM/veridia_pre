from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from api.models.schemas import DistribucionSemaforo, EstadisticasGenerales
 
import matplotlib
matplotlib.use("Agg")  # Backend sin GUI, obligatorio en servidor
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import base64
 
router = APIRouter()
 
 
# ---------- HELPERS ----------
 
def _fig_to_base64(fig) -> str:
    """Convierte una figura matplotlib a string base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130, transparent=True)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded
 
 
def _grafico_semaforo(verde: int, amarillo: int, rojo: int) -> str:
    """Gráfico de tarta con los tres niveles de riesgo."""
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
 
    valores = [verde, amarillo, rojo]
    etiquetas = ["Bajo riesgo", "Riesgo medio", "Alto riesgo"]
    colores = ["#16a34a", "#ca8a04", "#dc2626"]
    explotar = (0.03, 0.03, 0.03)
 
    wedges, texts, autotexts = ax.pie(
        valores,
        labels=None,
        colors=colores,
        explode=explotar,
        autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
        startangle=90,
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
        textprops={"fontsize": 11},
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
 
    parches = [
        mpatches.Patch(color=c, label=f"{l} ({v})")
        for c, l, v in zip(colores, etiquetas, valores)
    ]
    ax.legend(handles=parches, loc="lower center", bbox_to_anchor=(0.5, -0.12),
              ncol=1, fontsize=10, frameon=False)
    ax.set_title("Distribución por nivel de riesgo", fontsize=13, fontweight="bold", pad=14)
 
    return _fig_to_base64(fig)
 
 
def _grafico_indicadores(indicadores: dict) -> str:
    """Gráfico de barras horizontal con los indicadores más frecuentes."""
    if not indicadores:
        return ""
 
    etiquetas = list(indicadores.keys())
    valores = list(indicadores.values())
 
    # Ordenar de mayor a menor
    pares = sorted(zip(valores, etiquetas), reverse=True)
    valores, etiquetas = zip(*pares)
 
    fig, ax = plt.subplots(figsize=(6, max(3, len(etiquetas) * 0.7)))
 
    colores_barras = ["#6f4a8e", "#9b5fcf", "#b68ede", "#d4b8f0", "#e8d8fa"]
    c = [colores_barras[i % len(colores_barras)] for i in range(len(etiquetas))]
 
    barras = ax.barh(etiquetas, valores, color=c, edgecolor="white", linewidth=0.8)
 
    for barra, val in zip(barras, valores):
        ax.text(
            barra.get_width() + 0.3, barra.get_y() + barra.get_height() / 2,
            str(val), va="center", ha="left", fontsize=10, fontweight="bold", color="#374151"
        )
 
    ax.set_xlabel("Frecuencia", fontsize=10)
    ax.set_title("Indicadores más frecuentes", fontsize=13, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, max(valores) * 1.2)
    ax.tick_params(axis="y", labelsize=10)
    fig.tight_layout()
 
    return _fig_to_base64(fig)
 
 
def _grafico_idiomas(idiomas: dict) -> str:
    """Gráfico de barras verticales con idiomas detectados."""
    if not idiomas:
        return ""
 
    etiquetas = list(idiomas.keys())
    valores = list(idiomas.values())
 
    fig, ax = plt.subplots(figsize=(5, 3.5))
 
    colores_barras = ["#b6c35d", "#8f9e25", "#6b7a1a", "#d4e07a", "#e8f0a0"]
    c = [colores_barras[i % len(colores_barras)] for i in range(len(etiquetas))]
 
    barras = ax.bar(etiquetas, valores, color=c, edgecolor="white", linewidth=0.8, width=0.5)
 
    for barra, val in zip(barras, valores):
        ax.text(
            barra.get_x() + barra.get_width() / 2, barra.get_height() + 0.5,
            str(val), ha="center", va="bottom", fontsize=10, fontweight="bold", color="#374151"
        )
 
    ax.set_ylabel("Anuncios analizados", fontsize=10)
    ax.set_title("Idiomas detectados", fontsize=13, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, max(valores) * 1.25)
    ax.tick_params(axis="x", labelsize=11)
    fig.tight_layout()
 
    return _fig_to_base64(fig)
 
 
# ---------- MODELO DE RESPUESTA CON GRÁFICOS ----------
 
class EstadisticasConGraficos(BaseModel):
    estadisticas: EstadisticasGenerales
    grafico_semaforo: str   # base64 PNG
    grafico_indicadores: str
    grafico_idiomas: str
 
 
# ---------- ENDPOINT ----------
 
@router.get("/estadisticas", response_model=EstadisticasConGraficos)
async def obtener_estadisticas():
    # Aquí se implementaría la lógica para calcular las estadísticas reales
    stats = EstadisticasGenerales(
        total_analizados=100,
        distribucion_semaforo=DistribucionSemaforo(
            verde=60,
            amarillo=25,
            rojo=15
        ),
        indicadores_frecuentes={
            "trabajo inmediato": 34,
            "sin experiencia": 28,
            "alojamiento incluido": 21
        },
        idiomas_frecuentes={
            "es": 75,
            "en": 20,
            "fr": 5
        }
    )
 
    dist = stats.distribucion_semaforo
 
    return EstadisticasConGraficos(
        estadisticas=stats,
        grafico_semaforo=_grafico_semaforo(dist.verde, dist.amarillo, dist.rojo),
        grafico_indicadores=_grafico_indicadores(stats.indicadores_frecuentes),
        grafico_idiomas=_grafico_idiomas(stats.idiomas_frecuentes),
    )