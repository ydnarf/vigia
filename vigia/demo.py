"""Series sintéticas para correr Vigía sin credenciales (VIGIA_DEMO=1).

Deterministas a propósito: cada escenario produce siempre el mismo
régimen, lo que las hace útiles también en los tests.
"""

from datetime import date, timedelta

from .regime import Serie


def _serie(valores: list[float]) -> Serie:
    hoy = date.today()
    n = len(valores)
    return [
        ((hoy - timedelta(days=n - 1 - i)).isoformat(), v)
        for i, v in enumerate(valores)
    ]


def _rampa(desde: float, hasta: float, pasos: int = 60) -> list[float]:
    paso = (hasta - desde) / (pasos - 1)
    return [desde + paso * i for i in range(pasos)]


def series_demo(escenario: str = "risk-off") -> dict[str, Serie]:
    if escenario == "risk-off":
        return {
            "vix": _serie(_rampa(18.0, 27.3)),
            "curva": _serie(_rampa(0.10, -0.31)),
            "credito": _serie(_rampa(4.2, 5.4)),
            "sp500": _serie(_rampa(5200.0, 4880.0)),
        }
    if escenario == "risk-on":
        return {
            "vix": _serie(_rampa(19.0, 13.2)),
            "curva": _serie(_rampa(0.30, 0.62)),
            "credito": _serie(_rampa(4.4, 3.1)),
            "sp500": _serie(_rampa(5100.0, 5480.0)),
        }
    if escenario == "neutral":
        return {
            "vix": _serie([18.5] * 60),
            "curva": _serie([0.12] * 60),
            "credito": _serie([4.5] * 60),
            "sp500": _serie([5200.0] * 60),
        }
    raise ValueError(f"Escenario demo desconocido: {escenario}")
