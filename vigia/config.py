"""Configuración por variables de entorno (con .env en desarrollo)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_token: str
    fred_api_key: str
    intervalo_min: int
    ruta_estado: Path
    demo: bool


def cargar() -> Config:
    load_dotenv()
    return Config(
        telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
        fred_api_key=os.getenv("FRED_API_KEY", ""),
        intervalo_min=int(os.getenv("CHECK_INTERVAL_MIN", "30")),
        ruta_estado=Path(os.getenv("STATE_PATH", "estado.json")),
        demo=os.getenv("VIGIA_DEMO", "") == "1",
    )
