"""Cliente mínimo de la API de FRED (Federal Reserve Economic Data).

Solo usa el endpoint de observaciones. Las cuatro series que alimentan el
detector están fijadas aquí; agregar un indicador nuevo es sumar una
entrada a SERIES y una función de voto en regime.py.
"""

from datetime import date, timedelta

import httpx

from .regime import Serie

BASE = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "vix": "VIXCLS",  # CBOE Volatility Index
    "curva": "T10Y2Y",  # spread 10 años - 2 años del Tesoro
    "credito": "BAMLH0A0HYM2",  # ICE BofA US High Yield OAS
    "sp500": "SP500",  # S&P 500 (cierre)
}


class FredError(RuntimeError):
    """La API de FRED respondió con error o sin datos útiles."""


def _parsear(payload: dict, serie_id: str) -> Serie:
    observaciones = payload.get("observations", [])
    datos: Serie = []
    for obs in observaciones:
        valor = obs.get("value", ".")
        if valor == ".":  # FRED marca así los días sin dato
            continue
        datos.append((obs["date"], float(valor)))
    if not datos:
        raise FredError(f"FRED no devolvió observaciones válidas para {serie_id}")
    return datos


async def descargar(api_key: str, dias: int = 180) -> dict[str, Serie]:
    """Descarga las cuatro series de los últimos `dias` días naturales."""
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    series: dict[str, Serie] = {}
    async with httpx.AsyncClient(timeout=20) as cliente:
        for clave, serie_id in SERIES.items():
            respuesta = await cliente.get(
                BASE,
                params={
                    "series_id": serie_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": inicio,
                    "sort_order": "asc",
                },
            )
            if respuesta.status_code != 200:
                raise FredError(
                    f"FRED respondió {respuesta.status_code} para {serie_id}: "
                    f"{respuesta.text[:200]}"
                )
            series[clave] = _parsear(respuesta.json(), serie_id)
    return series
