from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    name = db.Column(db.String(100), nullable=True)
    subscription_status = db.Column(db.String(20), default='free', nullable=False)
    preferences = db.Column(db.Text, default='{}', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    trial_used = db.Column(db.Boolean, default=False, nullable=False)
    whatsapp_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relacionamentos
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')
    usage_logs = db.relationship('UsageLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, email, password, name=None, phone_number=None):
        self.email = email
        self.set_password(password)
        self.name = name
        self.phone_number = phone_number

    def set_password(self, password):
        """Hash e armazena a senha do usuário"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida está correta"""
        return check_password_hash(self.password_hash, password)

    def get_preferences(self):
        """Retorna preferências como dicionário"""
        try:
            return json.loads(self.preferences)
        except:
            return {}

    def set_preferences(self, prefs_dict):
        """Define preferências a partir de dicionário"""
        self.preferences = json.dumps(prefs_dict)

    def is_premium(self):
        """Verifica se usuário tem assinatura premium ativa"""
        return self.subscription_status in ['premium', 'premium_trial']

    def can_use_ai_features(self):
        """Verifica se usuário pode usar features de IA"""
        if self.is_premium():
            return True
        
        # Usuários gratuitos têm limite diário
        from src.models.usage_log import UsageLog
        today_usage = UsageLog.get_daily_usage(self.id)
        return today_usage < 5  # Limite de 5 processamentos IA por dia

    def to_dict(self, include_sensitive=False):
        """Converte usuário para dicionário"""
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone_number': self.phone_number,
            'subscription_status': self.subscription_status,
            'preferences': self.get_preferences(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'trial_used': self.trial_used,
            'whatsapp_opt_in': self.whatsapp_opt_in,
            'is_active': self.is_active,
            'email_verified': self.email_verified
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data

    def __repr__(self):
        return f'<User {self.email}>'


class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    device_info = db.Column(db.Text, default='{}', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def get_device_info(self):
        """Retorna informações do dispositivo como dicionário"""
        try:
            return json.loads(self.device_info)
        except:
            return {}

    def set_device_info(self, device_dict):
        """Define informações do dispositivo"""
        self.device_info = json.dumps(device_dict)

    def is_expired(self):
        """Verifica se a sessão expirou"""
        return datetime.utcnow() > self.expires_at

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'device_info': self.get_device_info(),
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Session {self.id} for User {self.user_id}>'


class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    api_type = db.Column(db.String(50), nullable=False)  # 'chatgpt', 'perplexity', etc.
    endpoint = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    request_metadata = db.Column(db.Text, default='{}', nullable=False)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)
    cost = db.Column(db.Float, default=0.0, nullable=False)

    @staticmethod
    def get_daily_usage(user_id, api_type=None):
        """Retorna contagem de uso diário do usuário"""
        from datetime import date
        today = date.today()
        
        query = UsageLog.query.filter(
            UsageLog.user_id == user_id,
            db.func.date(UsageLog.created_at) == today
        )
        
        if api_type:
            query = query.filter(UsageLog.api_type == api_type)
            
        return query.count()

    @staticmethod
    def log_usage(user_id, api_type, endpoint=None, tokens_used=0, cost=0.0, metadata=None):
        """Registra uso de API"""
        log = UsageLog(
            user_id=user_id,
            api_type=api_type,
            endpoint=endpoint,
            tokens_used=tokens_used,
            cost=cost,
            request_metadata=json.dumps(metadata or {})
        )
        db.session.add(log)
        db.session.commit()
        return log

    def get_metadata(self):
        """Retorna metadata como dicionário"""
        try:
            return json.loads(self.request_metadata)
        except:
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'api_type': self.api_type,
            'endpoint': self.endpoint,
            'created_at': self.created_at.isoformat(),
            'tokens_used': self.tokens_used,
            'cost': self.cost,
            'metadata': self.get_metadata()
        }

    def __repr__(self):
        return f'<UsageLog {self.api_type} for User {self.user_id}>'

