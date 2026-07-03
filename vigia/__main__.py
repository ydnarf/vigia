"""Punto de entrada.

    python -m vigia                  # bot de Telegram (requiere tokens)
    python -m vigia --once           # evalúa una vez y sale (requiere FRED_API_KEY)
    python -m vigia --once --demo    # evalúa con datos sintéticos, sin credenciales
"""

import argparse
import asyncio
import dataclasses
import logging

from . import demo, fred, regime, signals
from .config import cargar


def _evaluar_una_vez(args: argparse.Namespace) -> None:
    config = cargar()
    if args.demo or config.demo:
        series = demo.series_demo(args.escenario)
    else:
        if not config.fred_api_key:
            raise SystemExit("Falta FRED_API_KEY (o usa --demo).")
        series = asyncio.run(fred.descargar(config.fred_api_key))

    regimen = regime.detectar(series)
    senal = signals.generar(regimen)

    print(f"RÉGIMEN   {regimen.nombre}  (puntaje {regimen.puntaje:+d}, "
          f"confianza {regimen.confianza})")
    print(f"ACTIVO    {senal.activo}")
    print(f"DIRECCIÓN {senal.direccion}")
    for i, gatillo in enumerate(senal.gatillos):
        print(f"{'GATILLO' if i == 0 else '':9} {gatillo}")
    print(f"DATOS     FRED, cierre {regimen.fecha_datos}")
    print(f"\n{signals.DISCLAIMER}")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    parser = argparse.ArgumentParser(prog="vigia", description=__doc__)
    parser.add_argument("--once", action="store_true",
                        help="evalúa el régimen una vez, imprime y sale")
    parser.add_argument("--demo", action="store_true",
                        help="usa series sintéticas en lugar de FRED")
    parser.add_argument("--escenario", default="risk-off",
                        choices=["risk-off", "risk-on", "neutral"],
                        help="escenario para el modo demo")
    args = parser.parse_args()

    if args.once:
        _evaluar_una_vez(args)
        return

    from .bot import run  # importa aquí para que --once no exija telegram

    config = cargar()
    if args.demo:
        config = dataclasses.replace(config, demo=True)
    run(config)


if __name__ == "__main__":
    main()
