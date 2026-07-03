"""Bot de Telegram: comandos y vigilancia periódica del régimen."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from . import demo, fred, regime, signals
from .config import Config
from .state import Estado

log = logging.getLogger(__name__)

BIENVENIDA = (
    "<b>Vigía</b> — vigila el mercado por ti.\n\n"
    "Leo indicadores macro de FRED (VIX, curva 10Y–2Y, crédito HY y "
    "tendencia del S&amp;P 500), detecto el régimen vigente y aviso cuando "
    "cambia.\n\n"
    "/estado — lectura actual de los indicadores\n"
    "/senal — señal vigente ahora mismo\n"
    "/suscribir — recibir aviso en cada cambio de régimen\n"
    "/parar — dejar de recibir avisos\n\n"
    f"<i>{signals.DISCLAIMER}</i>"
)


async def _evaluar(config: Config) -> regime.Regimen:
    if config.demo:
        series = demo.series_demo()
    else:
        series = await fred.descargar(config.fred_api_key)
    return regime.detectar(series)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(BIENVENIDA)


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regimen = await _evaluar(context.bot_data["config"])
    await update.message.reply_html(signals.formatear_estado(regimen))


async def cmd_senal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regimen = await _evaluar(context.bot_data["config"])
    senal = signals.generar(regimen)
    await update.message.reply_html(signals.formatear_senal(senal))


async def cmd_suscribir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    estado: Estado = context.bot_data["estado"]
    estado.suscriptores.add(update.effective_chat.id)
    estado.guardar()
    await update.message.reply_html(
        "Suscrito. Te aviso cuando el régimen de mercado cambie."
    )


async def cmd_parar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    estado: Estado = context.bot_data["estado"]
    estado.suscriptores.discard(update.effective_chat.id)
    estado.guardar()
    await update.message.reply_html("Listo, no recibirás más avisos.")


async def vigilar(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job periódico: evalúa el régimen y avisa a los suscriptores si cambió."""
    config: Config = context.bot_data["config"]
    estado: Estado = context.bot_data["estado"]
    try:
        regimen = await _evaluar(config)
    except Exception:
        log.exception("Fallo evaluando el régimen; se reintenta en el próximo ciclo")
        return

    if estado.ultimo_regimen is None:
        # Primer arranque: registra la línea base sin avisar a nadie.
        estado.ultimo_regimen = regimen.nombre
        estado.guardar()
        log.info("Línea base registrada: %s", regimen.nombre)
        return

    if regimen.nombre == estado.ultimo_regimen:
        log.info("Sin cambios: %s (puntaje %+d)", regimen.nombre, regimen.puntaje)
        return

    log.info("Cambio de régimen: %s → %s", estado.ultimo_regimen, regimen.nombre)
    mensaje = signals.formatear_senal(signals.generar(regimen))
    for chat_id in sorted(estado.suscriptores):
        try:
            await context.bot.send_message(
                chat_id, mensaje, parse_mode=ParseMode.HTML
            )
        except Exception:
            log.exception("No se pudo avisar al chat %s", chat_id)
    estado.ultimo_regimen = regimen.nombre
    estado.guardar()


async def _error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Error atendiendo una actualización", exc_info=context.error)


def run(config: Config) -> None:
    if not config.telegram_token:
        raise SystemExit("Falta TELEGRAM_TOKEN (crea el bot con @BotFather).")
    if not config.demo and not config.fred_api_key:
        raise SystemExit("Falta FRED_API_KEY (gratis en fred.stlouisfed.org).")

    application = Application.builder().token(config.telegram_token).build()
    application.bot_data["config"] = config
    application.bot_data["estado"] = Estado.cargar(config.ruta_estado)

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("estado", cmd_estado))
    application.add_handler(CommandHandler("senal", cmd_senal))
    application.add_handler(CommandHandler("suscribir", cmd_suscribir))
    application.add_handler(CommandHandler("parar", cmd_parar))
    application.add_error_handler(_error)

    application.job_queue.run_repeating(
        vigilar, interval=config.intervalo_min * 60, first=10
    )

    log.info(
        "Vigía en marcha (cada %d min, demo=%s)", config.intervalo_min, config.demo
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)
