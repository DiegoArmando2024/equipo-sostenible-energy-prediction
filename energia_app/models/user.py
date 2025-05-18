from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' o 'admin'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Building(db.Model):
    __tablename__ = 'buildings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    area = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    
    # Relación con predicciones
    predictions = db.relationship('Prediction', backref='building', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Building {self.name}>'

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ocupacion = db.Column(db.Integer, nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)
    hora_dia = db.Column(db.Integer, nullable=False)
    consumo_predicho = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<Prediction {self.id} for Building {self.building_id}>'