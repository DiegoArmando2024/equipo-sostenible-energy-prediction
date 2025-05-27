# energia_app/services/email_service.py
from flask import current_app, render_template
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
import os
from datetime import datetime, timedelta
from energia_app.models.user import User, Building, Prediction

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de correos electrónicos del sistema energético"""
    
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar el servicio con la aplicación Flask"""
        app.config.setdefault('MAIL_SERVER', 'smtp.gmail.com')
        app.config.setdefault('MAIL_PORT', 587)
        app.config.setdefault('MAIL_USE_TLS', True)
        app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME'))
        app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD'))
        app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))
        
        self.mail = Mail(app)
    
    def send_consumption_alert(self, user_email, building_name, consumption, threshold=100):
        """
        Envía alerta de consumo energético alto
        
        Args:
            user_email (str): Email del destinatario
            building_name (str): Nombre del edificio
            consumption (float): Consumo actual en kWh
            threshold (float): Umbral de alerta
        """
        try:
            subject = f'🚨 Alerta de Consumo Energético - {building_name}'
            
            # Crear mensaje
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=render_template('emails/consumption_alert.html',
                                   building_name=building_name,
                                   consumption=consumption,
                                   threshold=threshold,
                                   timestamp=datetime.now())
            )
            
            self.mail.send(msg)
            logger.info(f"Alerta de consumo enviada a {user_email} para {building_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar alerta de consumo: {str(e)}")
            return False
    
    def send_weekly_report(self, user_email, user_name):
        """
        Envía reporte semanal de consumo energético
        
        Args:
            user_email (str): Email del destinatario
            user_name (str): Nombre del usuario
        """
        try:
            # Calcular datos de la semana pasada
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Obtener datos de consumo
            predictions = Prediction.query.filter(
                Prediction.timestamp >= start_date,
                Prediction.timestamp <= end_date
            ).all()
            
            # Calcular estadísticas
            total_consumption = sum(p.consumo_predicho for p in predictions)
            avg_consumption = total_consumption / len(predictions) if predictions else 0
            buildings_count = len(set(p.building_id for p in predictions))
            
            # Obtener top edificios por consumo
            building_consumption = {}
            for prediction in predictions:
                building_id = prediction.building_id
                if building_id not in building_consumption:
                    building_consumption[building_id] = 0
                building_consumption[building_id] += prediction.consumo_predicho
            
            top_buildings = sorted(building_consumption.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
            
            # Obtener nombres de edificios
            top_buildings_data = []
            for building_id, consumption in top_buildings:
                building = Building.query.get(building_id)
                if building:
                    top_buildings_data.append({
                        'name': building.name,
                        'consumption': round(consumption, 2)
                    })
            
            subject = f'📊 Reporte Semanal de Consumo Energético - UDEC'
            
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=render_template('emails/weekly_report.html',
                                   user_name=user_name,
                                   total_consumption=round(total_consumption, 2),
                                   avg_consumption=round(avg_consumption, 2),
                                   buildings_count=buildings_count,
                                   top_buildings=top_buildings_data,
                                   start_date=start_date.strftime('%d/%m/%Y'),
                                   end_date=end_date.strftime('%d/%m/%Y'))
            )
            
            self.mail.send(msg)
            logger.info(f"Reporte semanal enviado a {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar reporte semanal: {str(e)}")
            return False
    
    def send_maintenance_reminder(self, user_email, building_name, equipment_type):
        """
        Envía recordatorio de mantenimiento preventivo
        
        Args:
            user_email (str): Email del destinatario
            building_name (str): Nombre del edificio
            equipment_type (str): Tipo de equipo
        """
        try:
            subject = f'🔧 Recordatorio de Mantenimiento - {building_name}'
            
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=render_template('emails/maintenance_reminder.html',
                                   building_name=building_name,
                                   equipment_type=equipment_type,
                                   timestamp=datetime.now())
            )
            
            self.mail.send(msg)
            logger.info(f"Recordatorio de mantenimiento enviado a {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar recordatorio de mantenimiento: {str(e)}")
            return False
    
    def send_user_welcome(self, user_email, user_name, temp_password=None):
        """
        Envía email de bienvenida a nuevo usuario
        
        Args:
            user_email (str): Email del nuevo usuario
            user_name (str): Nombre del usuario
            temp_password (str): Contraseña temporal (opcional)
        """
        try:
            subject = '🎉 Bienvenido al Sistema Predictivo de Consumo Energético - UDEC'
            
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=render_template('emails/user_welcome.html',
                                   user_name=user_name,
                                   temp_password=temp_password,
                                   login_url=current_app.config.get('BASE_URL', 'http://localhost:5000') + '/login')
            )
            
            self.mail.send(msg)
            logger.info(f"Email de bienvenida enviado a {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de bienvenida: {str(e)}")
            return False
    
    def send_system_notification(self, admin_emails, notification_type, message, data=None):
        """
        Envía notificación del sistema a administradores
        
        Args:
            admin_emails (list): Lista de emails de administradores
            notification_type (str): Tipo de notificación
            message (str): Mensaje de la notificación
            data (dict): Datos adicionales
        """
        try:
            subject = f'🔔 Notificación del Sistema - {notification_type}'
            
            for email in admin_emails:
                msg = Message(
                    subject=subject,
                    recipients=[email],
                    html=render_template('emails/system_notification.html',
                                       notification_type=notification_type,
                                       message=message,
                                       data=data,
                                       timestamp=datetime.now())
                )
                
                self.mail.send(msg)
                logger.info(f"Notificación del sistema enviada a {email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar notificación del sistema: {str(e)}")
            return False

# Funciones de utilidad para tareas programadas
def check_consumption_alerts():
    """Verifica si hay consumos que requieren alertas"""
    try:
        # Obtener predicciones de las últimas 24 horas
        yesterday = datetime.now() - timedelta(days=1)
        recent_predictions = Prediction.query.filter(
            Prediction.timestamp >= yesterday
        ).all()
        
        email_service = EmailService()
        email_service.init_app(current_app)
        
        # Definir umbrales de alerta por área del edificio
        def get_threshold(building_area):
            if building_area < 1000:
                return 50  # kWh
            elif building_area < 3000:
                return 100  # kWh
            else:
                return 150  # kWh
        
        # Verificar cada predicción
        for prediction in recent_predictions:
            building = Building.query.get(prediction.building_id)
            if building:
                threshold = get_threshold(building.area)
                
                if prediction.consumo_predicho > threshold:
                    # Obtener usuarios administradores del edificio
                    admin_users = User.query.filter_by(role='admin').all()
                    
                    for admin in admin_users:
                        email_service.send_consumption_alert(
                            admin.email,
                            building.name,
                            prediction.consumo_predicho,
                            threshold
                        )
        
        logger.info("Verificación de alertas de consumo completada")
        
    except Exception as e:
        logger.error(f"Error en verificación de alertas: {str(e)}")

def send_weekly_reports():
    """Envía reportes semanales a todos los usuarios activos"""
    try:
        email_service = EmailService()
        email_service.init_app(current_app)
        
        # Obtener todos los usuarios activos
        users = User.query.all()
        
        for user in users:
            email_service.send_weekly_report(user.email, user.username)
        
        logger.info("Reportes semanales enviados")
        
    except Exception as e:
        logger.error(f"Error al enviar reportes semanales: {str(e)}")

# Configuración para tareas programadas (usando APScheduler)
def setup_scheduled_emails(app):
    """Configura las tareas programadas de email"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        import atexit
        
        scheduler = BackgroundScheduler()
        
        # Verificar alertas cada hora
        scheduler.add_job(
            func=check_consumption_alerts,
            trigger="interval",
            hours=1,
            id='consumption_alerts'
        )
        
        # Enviar reportes semanales los lunes a las 8:00 AM
        scheduler.add_job(
            func=send_weekly_reports,
            trigger="cron",
            day_of_week="mon",
            hour=8,
            id='weekly_reports'
        )
        
        scheduler.start()
        
        # Cerrar scheduler al terminar la aplicación
        atexit.register(lambda: scheduler.shutdown())
        
        logger.info("Tareas programadas de email configuradas")
    except ImportError:
        logger.warning("APScheduler no instalado. Tareas programadas deshabilitadas.")
    
