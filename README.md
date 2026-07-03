# Vigía

Bot de Telegram que vigila el mercado por ti: lee indicadores macro en
tiempo real desde la API de FRED, detecta el régimen de mercado vigente
por consenso de indicadores y entrega señales automáticamente cuando el
régimen cambia. Corre solo, desplegado en Google Cloud.

> Información educativa. **No es asesoría financiera.**

## Cómo funciona

```
        FRED API                      detector                Telegram
┌──────────────────────┐      ┌─────────────────────┐      ┌───────────┐
│ VIXCLS   (VIX)       │      │ cada indicador vota │      │ /estado   │
│ T10Y2Y   (curva)     │ ───► │ +1 / 0 / −1         │ ───► │ /senal    │
│ BAMLH0A0HYM2 (HY OAS)│      │ suma = régimen      │      │ avisos al │
│ SP500    (tendencia) │      │ consenso = confianza│      │ cambiar   │
└──────────────────────┘      └─────────────────────┘      └───────────┘
```

Cuatro indicadores votan riesgo con umbrales transparentes (sin caja negra):

| Indicador | Serie FRED | Vota risk-off cuando… | Vota risk-on cuando… |
|---|---|---|---|
| Volatilidad | `VIXCLS` | VIX ≥ 24 | VIX ≤ 16 |
| Curva de tipos | `T10Y2Y` | 10Y−2Y invertida (< 0) | pendiente ≥ 0.25% |
| Crédito high yield | `BAMLH0A0HYM2` | OAS ≥ 5% | OAS ≤ 4% |
| Tendencia S&P 500 | `SP500` | −2% bajo su media de 50 sesiones | +2% sobre ella |

Suma ≥ +2 → **RISK-ON** · suma ≤ −2 → **RISK-OFF** · resto → **NEUTRAL**.
La confianza sale del tamaño del consenso (3–4 votos alineados = alta).

Un job periódico (default: cada 30 min) reevalúa el régimen; si cambió,
envía la señal a todos los chats suscritos:

```
SEÑAL · RÉGIMEN RISK-OFF
ACTIVO     S&P 500 (SPX)
DIRECCIÓN  Corto / cobertura
GATILLO    VIX 27.3 > 24 (estrés)
           curva 10Y–2Y invertida (−0.31%)
CONFIANZA  Alta (consenso 3/4)
```

## Comandos del bot

| Comando | Qué hace |
|---|---|
| `/start` | Presentación y ayuda |
| `/estado` | Lectura actual de los cuatro indicadores |
| `/senal` | La señal vigente, ahora mismo |
| `/suscribir` | Recibir aviso automático en cada cambio de régimen |
| `/parar` | Dejar de recibir avisos |

## Correr en local

Requisitos: Python 3.12+, un token de bot (gratis con
[@BotFather](https://t.me/BotFather)) y una API key de FRED (gratis en
[fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)).

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows · en Linux/mac: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # y completa TELEGRAM_TOKEN y FRED_API_KEY
python -m vigia               # arranca el bot
```

Sin credenciales también puedes ver el motor funcionando:

```bash
python -m vigia --once --demo                      # escenario risk-off sintético
python -m vigia --once --demo --escenario risk-on
python -m vigia --once                             # datos reales (solo FRED_API_KEY)
```

Tests (sin red, sin credenciales):

```bash
python -m unittest discover -s tests -v
```

## Deploy en Google Cloud

El bot usa *long polling* (no necesita URL pública ni webhook). En Cloud
Run se despliega como servicio con una instancia siempre viva:

```bash
gcloud run deploy vigia \
  --source . \
  --region us-central1 \
  --no-cpu-throttling \
  --min-instances 1 --max-instances 1 \
  --no-allow-unauthenticated \
  --set-env-vars CHECK_INTERVAL_MIN=30,STATE_PATH=/tmp/estado.json \
  --set-secrets TELEGRAM_TOKEN=vigia-telegram-token:latest,FRED_API_KEY=vigia-fred-key:latest
```

Notas:

- Los tokens van en **Secret Manager** (`gcloud secrets create …`), nunca
  en la imagen ni en el repo.
- `max-instances 1` importa: dos instancias harían polling duplicado.
- El estado en `/tmp` no sobrevive un redeploy; la única consecuencia es
  que la primera evaluación tras arrancar registra la línea base sin
  avisar. Para persistencia real, monta un volumen de Cloud Storage y
  apunta `STATE_PATH` ahí.
- Alternativa más barata: una VM `e2-micro` (capa gratuita) con Docker y
  `--restart unless-stopped`.

## Estructura

```
vigia/
├── vigia/
│   ├── fred.py        # cliente de la API de FRED (4 series fijas)
│   ├── regime.py      # detector: votos por indicador + consenso
│   ├── signals.py     # señal y formato de mensajes
│   ├── bot.py         # comandos de Telegram + job de vigilancia
│   ├── demo.py        # series sintéticas para correr sin credenciales
│   ├── state.py       # último régimen y suscriptores (JSON en disco)
│   ├── config.py      # variables de entorno
│   └── __main__.py    # CLI: bot | --once | --demo
├── tests/
├── Dockerfile
└── requirements.txt
```

## Stack

Python 3.12 · python-telegram-bot · httpx · FRED API · Google Cloud Run
