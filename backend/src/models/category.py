from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json
from src.models.user import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    parent_category_id = db.Column(db.String(36), db.ForeignKey('categories.id'), nullable=True)
    color = db.Column(db.String(7), default='#6366f1', nullable=False)  # Hex color
    icon = db.Column(db.String(50), default='📝', nullable=False)  # Emoji or icon name
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_system_generated = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def __init__(self, user_id, name, parent_category_id=None, color='#6366f1', icon='📝', is_system_generated=False, description=None):
        self.user_id = user_id
        self.name = name
        self.parent_category_id = parent_category_id
        self.color = color
        self.icon = icon
        self.is_system_generated = is_system_generated
        self.description = description

    @staticmethod
    def create_default_categories(user_id):
        """Cria categorias padrão para um novo usuário"""
        default_categories = [
            {'name': 'Trabalho', 'icon': '💼', 'color': '#3b82f6', 'description': 'Anotações relacionadas ao trabalho e carreira'},
            {'name': 'Pessoal', 'icon': '👤', 'color': '#10b981', 'description': 'Anotações pessoais e vida privada'},
            {'name': 'Saúde', 'icon': '🏥', 'color': '#ef4444', 'description': 'Informações sobre saúde e bem-estar'},
            {'name': 'Finanças', 'icon': '💰', 'color': '#f59e0b', 'description': 'Controle financeiro e investimentos'},
            {'name': 'Estudos', 'icon': '📚', 'color': '#8b5cf6', 'description': 'Aprendizado e desenvolvimento pessoal'},
            {'name': 'Projetos', 'icon': '🚀', 'color': '#06b6d4', 'description': 'Projetos pessoais e profissionais'},
            {'name': 'Ideias', 'icon': '💡', 'color': '#eab308', 'description': 'Insights e ideias criativas'},
            {'name': 'Lembretes', 'icon': '⏰', 'color': '#f97316', 'description': 'Tarefas e compromissos importantes'}
        ]
        
        categories = []
        for i, cat_data in enumerate(default_categories):
            category = Category(
                user_id=user_id,
                name=cat_data['name'],
                icon=cat_data['icon'],
                color=cat_data['color'],
                description=cat_data['description'],
                is_system_generated=True,
                sort_order=i
            )
            categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        return categories

    def get_full_path(self):
        """Retorna o caminho completo da categoria (incluindo pais)"""
        if self.parent_category_id:
            parent = Category.query.get(self.parent_category_id)
            if parent:
                return f"{parent.get_full_path()} > {self.name}"
        return self.name

    def get_depth(self):
        """Retorna a profundidade da categoria na hierarquia"""
        if self.parent_category_id:
            parent = Category.query.get(self.parent_category_id)
            if parent:
                return parent.get_depth() + 1
        return 0

    def get_all_subcategories(self):
        """Retorna todas as subcategorias (recursivamente)"""
        subcats = []
        for subcat in self.subcategories:
            subcats.append(subcat)
            subcats.extend(subcat.get_all_subcategories())
        return subcats

    def can_be_parent_of(self, potential_child):
        """Verifica se esta categoria pode ser pai da categoria fornecida (evita loops)"""
        if potential_child.id == self.id:
            return False
        
        # Verifica se a categoria atual não é descendente da potencial filha
        current = self
        while current.parent_category_id:
            if current.parent_category_id == potential_child.id:
                return False
            current = Category.query.get(current.parent_category_id)
            if not current:
                break
        
        return True

    def count_notes(self, include_subcategories=True):
        """Conta o número de anotações nesta categoria"""
        from src.models.note import Note
        
        if include_subcategories:
            # Conta notas desta categoria e de todas as subcategorias
            category_names = [self.name]
            for subcat in self.get_all_subcategories():
                category_names.append(subcat.name)
            
            count = 0
            for name in category_names:
                count += Note.query.filter(
                    Note.user_id == self.user_id,
                    Note.category == name
                ).count()
            return count
        else:
            # Conta apenas notas desta categoria específica
            return Note.query.filter(
                Note.user_id == self.user_id,
                Note.category == self.name
            ).count()

    @staticmethod
    def get_by_user(user_id, include_counts=False):
        """Retorna todas as categorias do usuário organizadas hierarquicamente"""
        categories = Category.query.filter(
            Category.user_id == user_id
        ).order_by(Category.sort_order, Category.name).all()
        
        if include_counts:
            for category in categories:
                category._note_count = category.count_notes(include_subcategories=False)
        
        return categories

    @staticmethod
    def get_hierarchy(user_id):
        """Retorna categorias organizadas em estrutura hierárquica"""
        all_categories = Category.get_by_user(user_id)
        
        # Separa categorias raiz das subcategorias
        root_categories = [cat for cat in all_categories if cat.parent_category_id is None]
        
        def build_tree(parent_categories):
            tree = []
            for parent in parent_categories:
                node = {
                    'category': parent,
                    'children': build_tree([cat for cat in all_categories if cat.parent_category_id == parent.id])
                }
                tree.append(node)
            return tree
        
        return build_tree(root_categories)

    @staticmethod
    def find_or_create_by_name(user_id, name, auto_create=True):
        """Encontra categoria por nome ou cria se não existir"""
        category = Category.query.filter(
            Category.user_id == user_id,
            Category.name == name
        ).first()
        
        if not category and auto_create:
            # Cria nova categoria com configurações padrão
            category = Category(
                user_id=user_id,
                name=name,
                is_system_generated=True  # Marcada como gerada pelo sistema (IA)
            )
            db.session.add(category)
            db.session.commit()
        
        return category

    def update_sort_order(self, new_order):
        """Atualiza ordem de classificação da categoria"""
        self.sort_order = new_order
        db.session.commit()

    def move_to_parent(self, new_parent_id):
        """Move categoria para novo pai (ou raiz se None)"""
        if new_parent_id:
            new_parent = Category.query.get(new_parent_id)
            if not new_parent or not new_parent.can_be_parent_of(self):
                raise ValueError("Categoria pai inválida ou criaria loop na hierarquia")
        
        self.parent_category_id = new_parent_id
        db.session.commit()

    def to_dict(self, include_children=False, include_note_count=False):
        """Converte categoria para dicionário"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'parent_category_id': self.parent_category_id,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'is_system_generated': self.is_system_generated,
            'sort_order': self.sort_order,
            'description': self.description,
            'full_path': self.get_full_path(),
            'depth': self.get_depth()
        }
        
        if include_children:
            data['subcategories'] = [subcat.to_dict() for subcat in self.subcategories]
        
        if include_note_count:
            data['note_count'] = self.count_notes(include_subcategories=False)
            data['total_note_count'] = self.count_notes(include_subcategories=True)
        
        return data

    def __repr__(self):
        return f'<Category {self.name} for User {self.user_id}>'

