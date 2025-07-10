from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.category import Category
from src.routes.auth import token_required

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
@token_required
def get_categories(current_user):
    """Lista categorias do usuário"""
    try:
        include_counts = request.args.get('include_counts', 'false').lower() == 'true'
        hierarchy = request.args.get('hierarchy', 'false').lower() == 'true'
        
        if hierarchy:
            # Retorna estrutura hierárquica
            category_tree = Category.get_hierarchy(current_user.id)
            
            def serialize_tree(tree_nodes):
                result = []
                for node in tree_nodes:
                    category_data = node['category'].to_dict(
                        include_children=False,
                        include_note_count=include_counts
                    )
                    category_data['children'] = serialize_tree(node['children'])
                    result.append(category_data)
                return result
            
            return jsonify({
                'categories': serialize_tree(category_tree)
            }), 200
        else:
            # Retorna lista plana
            categories = Category.get_by_user(current_user.id, include_counts=include_counts)
            
            return jsonify({
                'categories': [cat.to_dict(include_note_count=include_counts) for cat in categories]
            }), 200
            
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/', methods=['POST'])
@token_required
def create_category(current_user):
    """Cria nova categoria"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Nome da categoria é obrigatório'}), 400
        
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Nome não pode estar vazio'}), 400
        
        # Verifica se categoria já existe
        existing = Category.query.filter_by(
            user_id=current_user.id,
            name=name
        ).first()
        
        if existing:
            return jsonify({'error': 'Categoria já existe'}), 409
        
        # Parâmetros opcionais
        parent_category_id = data.get('parent_category_id')
        color = data.get('color', '#6366f1')
        icon = data.get('icon', '📝')
        description = data.get('description')
        
        # Valida categoria pai se fornecida
        if parent_category_id:
            parent = Category.query.filter_by(
                id=parent_category_id,
                user_id=current_user.id
            ).first()
            
            if not parent:
                return jsonify({'error': 'Categoria pai não encontrada'}), 404
        
        # Cria categoria
        category = Category(
            user_id=current_user.id,
            name=name,
            parent_category_id=parent_category_id,
            color=color,
            icon=icon,
            description=description
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Categoria criada com sucesso',
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/<category_id>', methods=['GET'])
@token_required
def get_category(current_user, category_id):
    """Retorna categoria específica"""
    try:
        category = Category.query.filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        
        if not category:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        include_children = request.args.get('include_children', 'false').lower() == 'true'
        include_note_count = request.args.get('include_note_count', 'false').lower() == 'true'
        
        return jsonify({
            'category': category.to_dict(
                include_children=include_children,
                include_note_count=include_note_count
            )
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/<category_id>', methods=['PUT'])
@token_required
def update_category(current_user, category_id):
    """Atualiza categoria existente"""
    try:
        category = Category.query.filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        
        if not category:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados são obrigatórios'}), 400
        
        # Atualiza campos se fornecidos
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({'error': 'Nome não pode estar vazio'}), 400
            
            # Verifica se novo nome já existe (exceto para a própria categoria)
            existing = Category.query.filter(
                Category.user_id == current_user.id,
                Category.name == name,
                Category.id != category_id
            ).first()
            
            if existing:
                return jsonify({'error': 'Nome já existe em outra categoria'}), 409
            
            category.name = name
        
        if 'color' in data:
            category.color = data['color']
        
        if 'icon' in data:
            category.icon = data['icon']
        
        if 'description' in data:
            category.description = data['description']
        
        if 'parent_category_id' in data:
            new_parent_id = data['parent_category_id']
            
            if new_parent_id:
                # Valida nova categoria pai
                new_parent = Category.query.filter_by(
                    id=new_parent_id,
                    user_id=current_user.id
                ).first()
                
                if not new_parent:
                    return jsonify({'error': 'Categoria pai não encontrada'}), 404
                
                if not new_parent.can_be_parent_of(category):
                    return jsonify({'error': 'Movimentação criaria loop na hierarquia'}), 400
            
            category.parent_category_id = new_parent_id
        
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Categoria atualizada com sucesso',
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/<category_id>', methods=['DELETE'])
@token_required
def delete_category(current_user, category_id):
    """Remove categoria"""
    try:
        category = Category.query.filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        
        if not category:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        # Verifica se categoria tem subcategorias
        if category.subcategories:
            return jsonify({
                'error': 'Categoria possui subcategorias. Remova-as primeiro ou mova para outra categoria.'
            }), 400
        
        # Verifica se categoria tem anotações
        note_count = category.count_notes(include_subcategories=False)
        if note_count > 0:
            # Opção de forçar remoção movendo anotações para "Sem categoria"
            force = request.args.get('force', 'false').lower() == 'true'
            
            if not force:
                return jsonify({
                    'error': f'Categoria possui {note_count} anotações. Use force=true para mover para "Sem categoria".'
                }), 400
            
            # Move anotações para sem categoria
            from src.models.note import Note
            Note.query.filter_by(
                user_id=current_user.id,
                category=category.name
            ).update({'category': None})
        
        # Remove categoria
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'message': 'Categoria removida com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/<category_id>/move', methods=['POST'])
@token_required
def move_category(current_user, category_id):
    """Move categoria para nova posição na hierarquia"""
    try:
        category = Category.query.filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        
        if not category:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados são obrigatórios'}), 400
        
        new_parent_id = data.get('parent_category_id')
        new_sort_order = data.get('sort_order')
        
        # Move para novo pai se especificado
        if 'parent_category_id' in data:
            if new_parent_id:
                new_parent = Category.query.filter_by(
                    id=new_parent_id,
                    user_id=current_user.id
                ).first()
                
                if not new_parent:
                    return jsonify({'error': 'Categoria pai não encontrada'}), 404
                
                if not new_parent.can_be_parent_of(category):
                    return jsonify({'error': 'Movimentação criaria loop na hierarquia'}), 400
            
            category.parent_category_id = new_parent_id
        
        # Atualiza ordem se especificada
        if new_sort_order is not None:
            category.sort_order = new_sort_order
        
        db.session.commit()
        
        return jsonify({
            'message': 'Categoria movida com sucesso',
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/reorder', methods=['POST'])
@token_required
def reorder_categories(current_user):
    """Reordena múltiplas categorias"""
    try:
        data = request.get_json()
        if not data or not data.get('categories'):
            return jsonify({'error': 'Lista de categorias é obrigatória'}), 400
        
        category_orders = data['categories']  # [{'id': 'uuid', 'sort_order': 1}, ...]
        
        # Valida e atualiza cada categoria
        for item in category_orders:
            category_id = item.get('id')
            sort_order = item.get('sort_order')
            
            if not category_id or sort_order is None:
                continue
            
            category = Category.query.filter_by(
                id=category_id,
                user_id=current_user.id
            ).first()
            
            if category:
                category.sort_order = sort_order
        
        db.session.commit()
        
        return jsonify({'message': 'Categorias reordenadas com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/stats', methods=['GET'])
@token_required
def get_category_stats(current_user):
    """Retorna estatísticas das categorias"""
    try:
        categories = Category.get_by_user(current_user.id)
        
        stats = []
        total_notes = 0
        
        for category in categories:
            note_count = category.count_notes(include_subcategories=True)
            total_notes += note_count
            
            stats.append({
                'category': category.to_dict(),
                'note_count': note_count,
                'subcategory_count': len(category.subcategories)
            })
        
        # Ordena por número de anotações
        stats.sort(key=lambda x: x['note_count'], reverse=True)
        
        return jsonify({
            'total_categories': len(categories),
            'total_notes': total_notes,
            'category_stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/suggestions', methods=['GET'])
@token_required
def get_category_suggestions(current_user):
    """Retorna sugestões de categorias baseadas no conteúdo das anotações"""
    try:
        # Em uma implementação completa, isso usaria IA para analisar
        # o conteúdo das anotações sem categoria e sugerir categorias
        
        from src.models.note import Note
        
        # Busca anotações sem categoria
        uncategorized_notes = Note.query.filter_by(
            user_id=current_user.id,
            category=None
        ).limit(10).all()
        
        # Análise simples baseada em palavras-chave
        suggestions = []
        
        keyword_categories = {
            'trabalho': ['trabalho', 'reunião', 'projeto', 'cliente', 'empresa', 'escritório'],
            'saúde': ['médico', 'consulta', 'remédio', 'exercício', 'dieta', 'saúde'],
            'finanças': ['dinheiro', 'conta', 'pagamento', 'investimento', 'banco', 'cartão'],
            'estudos': ['curso', 'livro', 'aprender', 'estudo', 'prova', 'universidade'],
            'pessoal': ['família', 'amigo', 'casa', 'pessoal', 'relacionamento'],
            'ideias': ['ideia', 'insight', 'criativo', 'inovação', 'brainstorm']
        }
        
        for note in uncategorized_notes:
            content_lower = note.content.lower()
            
            for category, keywords in keyword_categories.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        suggestions.append({
                            'note_id': note.id,
                            'note_title': note.get_title(),
                            'suggested_category': category,
                            'confidence': 0.7,  # Score simples
                            'reason': f'Contém palavra-chave: {keyword}'
                        })
                        break
        
        return jsonify({
            'suggestions': suggestions[:20]  # Limita a 20 sugestões
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@categories_bp.route('/apply-suggestions', methods=['POST'])
@token_required
def apply_category_suggestions(current_user):
    """Aplica sugestões de categorização"""
    try:
        data = request.get_json()
        if not data or not data.get('suggestions'):
            return jsonify({'error': 'Lista de sugestões é obrigatória'}), 400
        
        suggestions = data['suggestions']  # [{'note_id': 'uuid', 'category': 'trabalho'}, ...]
        applied_count = 0
        
        for suggestion in suggestions:
            note_id = suggestion.get('note_id')
            category_name = suggestion.get('category')
            
            if not note_id or not category_name:
                continue
            
            # Busca anotação
            from src.models.note import Note
            note = Note.query.filter_by(
                id=note_id,
                user_id=current_user.id
            ).first()
            
            if not note:
                continue
            
            # Encontra ou cria categoria
            category = Category.find_or_create_by_name(current_user.id, category_name)
            
            # Aplica categoria
            note.category = category.name
            applied_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{applied_count} sugestões aplicadas com sucesso',
            'applied_count': applied_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

