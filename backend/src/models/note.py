from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json
from src.models.user import db

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(20), nullable=False, default='app')  # 'whatsapp', 'app', 'web'
    category = db.Column(db.String(100), nullable=True, index=True)
    tags = db.Column(db.Text, default='[]', nullable=False)  # JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    ai_processed_at = db.Column(db.DateTime, nullable=True)
    deadline_suggested = db.Column(db.DateTime, nullable=True)
    related_notes = db.Column(db.Text, default='[]', nullable=False)  # JSON array of note IDs
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'processing', 'processed', 'failed'
    note_metadata = db.Column(db.Text, default='{}', nullable=False)  # JSON object
    
    # Relacionamentos
    insights = db.relationship('Insight', backref='note', lazy=True, cascade='all, delete-orphan')
    media_files = db.relationship('MediaFile', backref='note', lazy=True, cascade='all, delete-orphan')

    def __init__(self, user_id, content, source='app', category=None, tags=None, note_metadata=None):
        self.user_id = user_id
        self.content = content
        self.source = source
        self.category = category
        self.set_tags(tags or [])
        self.set_metadata(note_metadata or {})

    def get_tags(self):
        """Retorna tags como lista"""
        try:
            return json.loads(self.tags)
        except:
            return []

    def set_tags(self, tags_list):
        """Define tags a partir de lista"""
        self.tags = json.dumps(tags_list)

    def add_tag(self, tag):
        """Adiciona uma tag se não existir"""
        current_tags = self.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.set_tags(current_tags)

    def remove_tag(self, tag):
        """Remove uma tag se existir"""
        current_tags = self.get_tags()
        if tag in current_tags:
            current_tags.remove(tag)
            self.set_tags(current_tags)

    def get_related_notes(self):
        """Retorna IDs de notas relacionadas como lista"""
        try:
            return json.loads(self.related_notes)
        except:
            return []

    def set_related_notes(self, note_ids):
        """Define notas relacionadas a partir de lista de IDs"""
        self.related_notes = json.dumps(note_ids)

    def add_related_note(self, note_id):
        """Adiciona uma nota relacionada"""
        current_related = self.get_related_notes()
        if note_id not in current_related:
            current_related.append(note_id)
            self.set_related_notes(current_related)

    def get_metadata(self):
        """Retorna metadata como dicionário"""
        try:
            return json.loads(self.note_metadata)
        except:
            return {}

    def set_metadata(self, metadata_dict):
        """Define metadata a partir de dicionário"""
        self.note_metadata = json.dumps(metadata_dict)

    def update_metadata(self, key, value):
        """Atualiza um campo específico do metadata"""
        current_metadata = self.get_metadata()
        current_metadata[key] = value
        self.set_metadata(current_metadata)

    def is_processed(self):
        """Verifica se a nota foi processada pela IA"""
        return self.status == 'processed' and self.ai_processed_at is not None

    def mark_as_processed(self):
        """Marca a nota como processada pela IA"""
        self.status = 'processed'
        self.ai_processed_at = datetime.utcnow()

    def mark_as_processing(self):
        """Marca a nota como sendo processada"""
        self.status = 'processing'

    def mark_as_failed(self, error_message=None):
        """Marca a nota como falha no processamento"""
        self.status = 'failed'
        if error_message:
            self.update_metadata('error_message', error_message)

    def get_title(self, max_length=50):
        """Gera título a partir do conteúdo"""
        if not self.content:
            return "Nota sem conteúdo"
        
        # Remove quebras de linha e espaços extras
        clean_content = ' '.join(self.content.split())
        
        if len(clean_content) <= max_length:
            return clean_content
        
        # Trunca no último espaço antes do limite
        truncated = clean_content[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."

    def get_preview(self, max_length=150):
        """Gera preview do conteúdo"""
        if not self.content:
            return ""
        
        clean_content = ' '.join(self.content.split())
        
        if len(clean_content) <= max_length:
            return clean_content
        
        truncated = clean_content[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."

    @staticmethod
    def get_by_user(user_id, category=None, tags=None, limit=20, offset=0, search=None, sort='created_at', order='desc'):
        """Busca notas do usuário com filtros opcionais"""
        query = Note.query.filter(Note.user_id == user_id)
        
        if category:
            query = query.filter(Note.category == category)
        
        if tags:
            # Busca notas que contenham pelo menos uma das tags
            for tag in tags:
                query = query.filter(Note.tags.contains(f'"{tag}"'))
        
        if search:
            query = query.filter(Note.content.contains(search))
        
        # Ordenação
        if sort == 'created_at':
            order_by = Note.created_at.desc() if order == 'desc' else Note.created_at.asc()
        elif sort == 'updated_at':
            order_by = Note.updated_at.desc() if order == 'desc' else Note.updated_at.asc()
        else:
            order_by = Note.created_at.desc()
        
        query = query.order_by(order_by)
        
        return query.offset(offset).limit(limit).all()

    @staticmethod
    def count_by_user(user_id, category=None, tags=None, search=None):
        """Conta notas do usuário com filtros opcionais"""
        query = Note.query.filter(Note.user_id == user_id)
        
        if category:
            query = query.filter(Note.category == category)
        
        if tags:
            for tag in tags:
                query = query.filter(Note.tags.contains(f'"{tag}"'))
        
        if search:
            query = query.filter(Note.content.contains(search))
        
        return query.count()

    def to_dict(self, include_content=True, include_insights=False):
        """Converte nota para dicionário"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'source': self.source,
            'category': self.category,
            'tags': self.get_tags(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ai_processed_at': self.ai_processed_at.isoformat() if self.ai_processed_at else None,
            'deadline_suggested': self.deadline_suggested.isoformat() if self.deadline_suggested else None,
            'related_notes': self.get_related_notes(),
            'status': self.status,
            'metadata': self.get_metadata(),
            'title': self.get_title(),
            'preview': self.get_preview()
        }
        
        if include_content:
            data['content'] = self.content
        
        if include_insights:
            data['insights'] = [insight.to_dict() for insight in self.insights]
        
        return data

    def __repr__(self):
        return f'<Note {self.id} by User {self.user_id}>'


class Insight(db.Model):
    __tablename__ = 'insights'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    note_id = db.Column(db.String(36), db.ForeignKey('notes.id'), nullable=False, index=True)
    insight_type = db.Column(db.String(50), nullable=False)  # 'summary', 'advice', 'connection', 'task', 'deadline'
    content = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_dismissed = db.Column(db.Boolean, default=False, nullable=False)
    insight_metadata = db.Column(db.Text, default='{}', nullable=False)

    def __init__(self, user_id, note_id, insight_type, content, confidence_score=0.0, insight_metadata=None):
        self.user_id = user_id
        self.note_id = note_id
        self.insight_type = insight_type
        self.content = content
        self.confidence_score = confidence_score
        self.set_metadata(insight_metadata or {})

    def get_metadata(self):
        """Retorna metadata como dicionário"""
        try:
            return json.loads(self.insight_metadata)
        except:
            return {}

    def set_metadata(self, metadata_dict):
        """Define metadata a partir de dicionário"""
        self.insight_metadata = json.dumps(metadata_dict)

    def dismiss(self):
        """Marca insight como dispensado pelo usuário"""
        self.is_dismissed = True

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'note_id': self.note_id,
            'insight_type': self.insight_type,
            'content': self.content,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat(),
            'is_dismissed': self.is_dismissed,
            'metadata': self.get_metadata()
        }

    def __repr__(self):
        return f'<Insight {self.insight_type} for Note {self.note_id}>'


class MediaFile(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = db.Column(db.String(36), db.ForeignKey('notes.id'), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'image', 'document', 'audio', 'video'
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)  # Texto extraído via OCR ou parsing
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    file_metadata = db.Column(db.Text, default='{}', nullable=False)

    def __init__(self, note_id, file_name, file_type, file_path, file_size, mime_type, extracted_text=None, file_metadata=None):
        self.note_id = note_id
        self.file_name = file_name
        self.file_type = file_type
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.extracted_text = extracted_text
        self.set_metadata(file_metadata or {})

    def get_metadata(self):
        """Retorna metadata como dicionário"""
        try:
            return json.loads(self.file_metadata)
        except:
            return {}

    def set_metadata(self, metadata_dict):
        """Define metadata a partir de dicionário"""
        self.file_metadata = json.dumps(metadata_dict)

    def get_file_size_mb(self):
        """Retorna tamanho do arquivo em MB"""
        return round(self.file_size / (1024 * 1024), 2)

    def to_dict(self):
        return {
            'id': self.id,
            'note_id': self.note_id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'mime_type': self.mime_type,
            'extracted_text': self.extracted_text,
            'created_at': self.created_at.isoformat(),
            'metadata': self.get_metadata()
        }

    def __repr__(self):
        return f'<MediaFile {self.file_name} for Note {self.note_id}>'

