"""Generación y formato de señales a partir del régimen detectado."""

from dataclasses import dataclass
from html import escape

from .regime import RISK_OFF, RISK_ON, Regimen

ACTIVO = "S&P 500 (SPX)"

_DIRECCION = {
    RISK_ON: "Largo",
    RISK_OFF: "Corto / cobertura",
}

DISCLAIMER = "Información educativa. No es asesoría financiera."


@dataclass(frozen=True)
class Senal:
    regimen: Regimen
    activo: str
    direccion: str
    gatillos: tuple[str, ...]


def generar(regimen: Regimen) -> Senal:
    gatillos = tuple(v.detalle for v in regimen.votos if v.voto != 0)
    if not gatillos:
        gatillos = ("Sin lecturas extremas: todos los indicadores en zona neutral",)
    return Senal(
        regimen=regimen,
        activo=ACTIVO,
        direccion=_DIRECCION.get(regimen.nombre, "Fuera del mercado"),
        gatillos=gatillos,
    )


def _fila(etiqueta: str, valor: str) -> str:
    return f"{etiqueta:<10} {valor}"


def formatear_senal(senal: Senal) -> str:
    """Texto HTML para Telegram, en el mismo tono sobrio del resto."""
    r = senal.regimen
    filas = [
        _fila("ACTIVO", senal.activo),
        _fila("DIRECCIÓN", senal.direccion),
        _fila("GATILLO", senal.gatillos[0]),
    ]
    filas.extend(_fila("", g) for g in senal.gatillos[1:])
    filas.append(_fila("CONFIANZA", f"{r.confianza.capitalize()} (consenso {r.consenso})"))
    filas.append(_fila("DATOS", f"FRED, cierre {r.fecha_datos}"))
    cuerpo = escape("\n".join(filas))
    return (
        f"<b>SEÑAL · RÉGIMEN {escape(r.nombre)}</b>\n"
        f"<pre>{cuerpo}</pre>\n"
        f"<i>{escape(DISCLAIMER)}</i>"
    )


def formatear_estado(regimen: Regimen) -> str:
    """Lectura completa de indicadores para el comando /estado."""
    marcas = {1: "+", 0: "·", -1: "−"}
    filas = [f"{marcas[v.voto]} {v.detalle}" for v in regimen.votos]
    cuerpo = escape("\n".join(filas))
    return (
        f"<b>RÉGIMEN {escape(regimen.nombre)}</b> "
        f"(puntaje {regimen.puntaje:+d}, confianza {escape(regimen.confianza)})\n"
        f"<pre>{cuerpo}</pre>\n"
        f"<i>Datos FRED al cierre {escape(regimen.fecha_datos)}. {escape(DISCLAIMER)}</i>"
    )
