# energia_app/utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import logging
from energia_app.services import get_service

logger = logging.getLogger(__name__)

def setup_scheduled_tasks(app):
    """Configura las tareas programadas para la aplicación"""
    if app.config.get('TESTING'):
        return None

    scheduler = BackgroundScheduler()
    email_service = get_service('email')

    # Ejemplo: Tarea programada para enviar reportes diarios a las 8:00 AM
    @scheduler.scheduled_job(
        CronTrigger(hour=8, minute=0),
        name='send_daily_reports'
    )
    def daily_reports():
        try:
            with app.app_context():
                logger.info("Ejecutando tarea programada: enviar reportes diarios")
                # Aquí iría la lógica para enviar reportes
                # email_service.send_daily_reports()
        except Exception as e:
            logger.error(f"Error en tarea programada: {str(e)}")

    # Ejemplo: Tarea programada para respaldo semanal los domingos a las 23:00
    @scheduler.scheduled_job(
        CronTrigger(day_of_week='sun', hour=23, minute=0),
        name='weekly_backup'
    )
    def weekly_backup():
        try:
            with app.app_context():
                logger.info("Ejecutando tarea programada: respaldo semanal")
                # Aquí iría la lógica para el respaldo
        except Exception as e:
            logger.error(f"Error en tarea programada: {str(e)}")

    # Iniciar el scheduler
    scheduler.start()
    return scheduler