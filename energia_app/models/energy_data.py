from datetime import datetime
import pandas as pd
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from energia_app.models.user import db, Building

class EnergyData(db.Model):
    """
    Modelo para almacenar datos de consumo energético
    
    Este modelo permite guardar registros individuales de consumo energético
    que pueden ser utilizados para entrenar el modelo predictivo o para 
    realizar análisis históricos.
    """
    __tablename__ = 'energy_data'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # Relación opcional con un edificio
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    building = relationship('Building', backref='energy_data')
    
    # Variables predictoras
    area_edificio = Column(Float, nullable=False)
    ocupacion = Column(Integer, nullable=False)
    dia_semana = Column(Integer, nullable=False)  # 0=Lunes, 6=Domingo
    hora_dia = Column(Integer, nullable=False)    # 0-23
    
    # Variable objetivo
    consumo_energetico = Column(Float, nullable=False)
    
    # Índices para mejorar rendimiento de consultas
    __table_args__ = (
        Index('idx_energy_fecha', 'timestamp'),
        Index('idx_energy_building', 'building_id'),
        Index('idx_energy_dia_hora', 'dia_semana', 'hora_dia'),
    )
    
    def __repr__(self):
        return f'<EnergyData {self.id}: {self.consumo_energetico} kWh @ {self.timestamp}>'
    
    @classmethod
    def get_recent_records(cls, limit=10):
        """Obtiene los registros más recientes"""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_records_count(cls):
        """Obtiene el número total de registros"""
        return cls.query.count()
    
    @classmethod
    def get_records_by_building(cls, building_id):
        """Obtiene los registros para un edificio específico"""
        return cls.query.filter_by(building_id=building_id).all()
    
    @classmethod
    def get_records_by_period(cls, start_date, end_date):
        """Obtiene los registros en un período específico"""
        return cls.query.filter(
            cls.timestamp >= start_date,
            cls.timestamp <= end_date
        ).all()
    
    @classmethod
    def get_avg_consumption_by_building(cls):
        """Obtiene el consumo promedio por edificio"""
        return db.session.query(
            cls.building_id,
            func.avg(cls.consumo_energetico).label('avg_consumption')
        ).group_by(cls.building_id).all()
    
    @classmethod
    def get_avg_consumption_by_day(cls):
        """Obtiene el consumo promedio por día de la semana"""
        return db.session.query(
            cls.dia_semana,
            func.avg(cls.consumo_energetico).label('avg_consumption')
        ).group_by(cls.dia_semana).order_by(cls.dia_semana).all()
    
    @classmethod
    def get_avg_consumption_by_hour(cls):
        """Obtiene el consumo promedio por hora del día"""
        return db.session.query(
            cls.hora_dia,
            func.avg(cls.consumo_energetico).label('avg_consumption')
        ).group_by(cls.hora_dia).order_by(cls.hora_dia).all()
    
    @classmethod
    def export_to_df(cls):
        """
        Exporta todos los registros a un DataFrame de pandas
        
        Returns:
            pandas.DataFrame: DataFrame con todos los registros
        """
        # Obtener todos los registros
        records = cls.query.all()
        
        # Convertir a diccionario
        data = []
        for record in records:
            data.append({
                'area_edificio': record.area_edificio,
                'ocupacion': record.ocupacion,
                'dia_semana': record.dia_semana,
                'hora_dia': record.hora_dia,
                'consumo_energetico': record.consumo_energetico,
                'building_id': record.building_id,
                'timestamp': record.timestamp
            })
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Seleccionar solo las columnas necesarias para el entrenamiento
        training_df = df[['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']]
        
        return training_df
    
    @classmethod
    def import_from_df(cls, df, convert_building_areas=True):
        """
        Importa registros desde un DataFrame de pandas
        
        Args:
            df (pandas.DataFrame): DataFrame con los registros a importar
            convert_building_areas (bool): Si es True, busca edificios con áreas similares
                                         y asigna el building_id correspondiente
        
        Returns:
            int: Número de registros importados
        """
        # Verificar columnas mínimas requeridas
        required_cols = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Faltan columnas requeridas: {', '.join(missing_cols)}")
        
        # Buscar edificios para asignar building_id si es necesario
        building_map = {}
        if convert_building_areas and 'building_id' not in df.columns:
            buildings = Building.query.all()
            for building in buildings:
                building_map[building.area] = building.id
        
        # Crear registros
        records = []
        for _, row in df.iterrows():
            # Asignar building_id si existe un edificio con área similar
            building_id = None
            if 'building_id' in row and pd.notna(row['building_id']):
                building_id = row['building_id']
            elif convert_building_areas:
                # Buscar el edificio con área más cercana (dentro de un margen del 5%)
                area = row['area_edificio']
                for building_area, bid in building_map.items():
                    if abs(building_area - area) / area <= 0.05:  # 5% de margen
                        building_id = bid
                        break
            
            # Crear nuevo registro
            record = cls(
                area_edificio=row['area_edificio'],
                ocupacion=row['ocupacion'],
                dia_semana=row['dia_semana'],
                hora_dia=row['hora_dia'],
                consumo_energetico=row['consumo_energetico'],
                building_id=building_id
            )
            
            records.append(record)
        
        # Guardar en la base de datos
        db.session.add_all(records)
        db.session.commit()
        
        return len(records)
    
    @classmethod
    def get_statistics(cls):
        """
        Obtiene estadísticas generales de los datos
        
        Returns:
            dict: Diccionario con estadísticas
        """
        stats = {}
        
        # Total de registros
        stats['total_records'] = cls.query.count()
        
        # Promedio de consumo total
        avg_consumption = db.session.query(func.avg(cls.consumo_energetico)).scalar()
        stats['avg_consumption'] = float(avg_consumption) if avg_consumption else 0
        
        # Mínimo y máximo de consumo
        min_consumption = db.session.query(func.min(cls.consumo_energetico)).scalar()
        max_consumption = db.session.query(func.max(cls.consumo_energetico)).scalar()
        stats['min_consumption'] = float(min_consumption) if min_consumption else 0
        stats['max_consumption'] = float(max_consumption) if max_consumption else 0
        
        # Registros por edificio
        building_counts = db.session.query(
            cls.building_id, 
            func.count(cls.id).label('count')
        ).group_by(cls.building_id).all()
        
        stats['records_by_building'] = {
            bid if bid is not None else 'sin_edificio': count 
            for bid, count in building_counts
        }
        
        return stats