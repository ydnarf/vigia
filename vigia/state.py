"""Estado persistente del bot: último régimen visto y suscriptores.

Un JSON en disco alcanza: el bot corre en una sola instancia y el estado
sobrevive reinicios. En Cloud Run conviene montar un volumen o aceptar
que un redeploy reenvíe la primera señal (documentado en el README).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Estado:
    ruta: Path
    ultimo_regimen: str | None = None
    suscriptores: set[int] = field(default_factory=set)

    @classmethod
    def cargar(cls, ruta: Path) -> "Estado":
        if not ruta.exists():
            return cls(ruta=ruta)
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return cls(
            ruta=ruta,
            ultimo_regimen=datos.get("ultimo_regimen"),
            suscriptores=set(datos.get("suscriptores", [])),
        )

    def guardar(self) -> None:
        datos = {
            "ultimo_regimen": self.ultimo_regimen,
            "suscriptores": sorted(self.suscriptores),
        }
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporal.replace(self.ruta)
