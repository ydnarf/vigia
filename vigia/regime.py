"""Detector de regímenes de mercado.

Cuatro indicadores macro votan riesgo: +1 (risk-on), 0 (neutral) o
-1 (risk-off). La suma decide el régimen y el tamaño del consenso decide
la confianza. Este módulo no habla con ninguna API: recibe las series ya
descargadas, así se prueba offline.
"""

from dataclasses import dataclass

# Una serie es una lista de (fecha ISO, valor) en orden ascendente.
Serie = list[tuple[str, float]]

# Umbrales de cada indicador. Valores redondos y documentados a propósito:
# el detector es transparente, no una caja negra optimizada.
UMBRAL_VIX_CALMA = 16.0  # VIX por debajo: complacencia / risk-on
UMBRAL_VIX_ESTRES = 24.0  # VIX por encima: estrés / risk-off
UMBRAL_CURVA_PLANA = 0.25  # 10Y-2Y en puntos %: debajo es plana, <0 invertida
UMBRAL_CREDITO_CALMA = 4.0  # OAS high yield en %: debajo, crédito tranquilo
UMBRAL_CREDITO_ESTRES = 5.0  # por encima, el crédito descuenta problemas
VENTANA_TENDENCIA = 50  # sesiones para la media del S&P 500
UMBRAL_TENDENCIA = 0.02  # ±2% sobre la media marca tendencia

RISK_ON = "RISK-ON"
NEUTRAL = "NEUTRAL"
RISK_OFF = "RISK-OFF"


@dataclass(frozen=True)
class Voto:
    indicador: str
    valor: float
    fecha: str
    voto: int  # +1 risk-on · 0 neutral · -1 risk-off
    detalle: str


@dataclass(frozen=True)
class Regimen:
    nombre: str
    puntaje: int
    confianza: str  # 'alta' · 'media' · 'baja'
    votos: tuple[Voto, ...]

    @property
    def consenso(self) -> str:
        return f"{sum(1 for v in self.votos if v.voto != 0)}/{len(self.votos)}"

    @property
    def fecha_datos(self) -> str:
        return max(v.fecha for v in self.votos)


def _ultimo(serie: Serie, nombre: str) -> tuple[str, float]:
    if not serie:
        raise ValueError(f"La serie '{nombre}' llegó vacía")
    return serie[-1]


def votar_vix(serie: Serie) -> Voto:
    fecha, valor = _ultimo(serie, "vix")
    if valor >= UMBRAL_VIX_ESTRES:
        voto, detalle = -1, f"VIX {valor:.1f} > {UMBRAL_VIX_ESTRES:.0f} (estrés)"
    elif valor <= UMBRAL_VIX_CALMA:
        voto, detalle = 1, f"VIX {valor:.1f} < {UMBRAL_VIX_CALMA:.0f} (calma)"
    else:
        voto, detalle = 0, f"VIX {valor:.1f} en zona neutral"
    return Voto("VIX", valor, fecha, voto, detalle)


def votar_curva(serie: Serie) -> Voto:
    fecha, valor = _ultimo(serie, "curva")
    if valor < 0:
        voto, detalle = -1, f"curva 10Y–2Y invertida ({valor:+.2f}%)"
    elif valor < UMBRAL_CURVA_PLANA:
        voto, detalle = 0, f"curva 10Y–2Y plana ({valor:+.2f}%)"
    else:
        voto, detalle = 1, f"curva 10Y–2Y con pendiente ({valor:+.2f}%)"
    return Voto("Curva 10Y–2Y", valor, fecha, voto, detalle)


def votar_credito(serie: Serie) -> Voto:
    fecha, valor = _ultimo(serie, "credito")
    if valor >= UMBRAL_CREDITO_ESTRES:
        voto, detalle = -1, f"spread HY {valor:.2f}% > {UMBRAL_CREDITO_ESTRES:.0f}%"
    elif valor <= UMBRAL_CREDITO_CALMA:
        voto, detalle = 1, f"spread HY {valor:.2f}% contenido"
    else:
        voto, detalle = 0, f"spread HY {valor:.2f}% en zona neutral"
    return Voto("Crédito HY", valor, fecha, voto, detalle)


def votar_tendencia(serie: Serie) -> Voto:
    fecha, valor = _ultimo(serie, "sp500")
    ventana = [v for _, v in serie[-VENTANA_TENDENCIA:]]
    if len(ventana) < 10:
        raise ValueError("La serie del S&P 500 necesita al menos 10 sesiones")
    media = sum(ventana) / len(ventana)
    desvio = (valor - media) / media
    if desvio >= UMBRAL_TENDENCIA:
        voto = 1
        detalle = f"S&P 500 {desvio:+.1%} sobre su media de {len(ventana)} sesiones"
    elif desvio <= -UMBRAL_TENDENCIA:
        voto = -1
        detalle = f"S&P 500 {desvio:+.1%} bajo su media de {len(ventana)} sesiones"
    else:
        voto = 0
        detalle = f"S&P 500 pegado a su media ({desvio:+.1%})"
    return Voto("Tendencia S&P 500", valor, fecha, voto, detalle)


def detectar(series: dict[str, Serie]) -> Regimen:
    """Evalúa las cuatro series y devuelve el régimen vigente.

    `series` debe traer las claves 'vix', 'curva', 'credito' y 'sp500'.
    """
    votos = (
        votar_vix(series["vix"]),
        votar_curva(series["curva"]),
        votar_credito(series["credito"]),
        votar_tendencia(series["sp500"]),
    )
    puntaje = sum(v.voto for v in votos)
    if puntaje >= 2:
        nombre = RISK_ON
    elif puntaje <= -2:
        nombre = RISK_OFF
    else:
        nombre = NEUTRAL
    magnitud = abs(puntaje)
    confianza = "alta" if magnitud >= 3 else "media" if magnitud == 2 else "baja"
    return Regimen(nombre, puntaje, confianza, votos)
