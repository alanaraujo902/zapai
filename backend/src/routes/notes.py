from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.note import Note, Insight, MediaFile
from src.models.category import Category
from src.routes.auth import token_required

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/', methods=['GET'])
@token_required
def get_notes(current_user):
    """Lista anotações do usuário com filtros opcionais"""
    try:
        # Parâmetros de query
        category = request.args.get('category')
        tags = request.args.getlist('tags')
        limit = min(int(request.args.get('limit', 20)), 100)  # Máximo 100
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search')
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')
        include_content = request.args.get('include_content', 'true').lower() == 'true'
        
        # Busca anotações
        notes = Note.get_by_user(
            user_id=current_user.id,
            category=category,
            tags=tags,
            limit=limit,
            offset=offset,
            search=search,
            sort=sort,
            order=order
        )
        
        # Conta total para paginação
        total_count = Note.count_by_user(
            user_id=current_user.id,
            category=category,
            tags=tags,
            search=search
        )
        
        return jsonify({
            'notes': [note.to_dict(include_content=include_content) for note in notes],
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/', methods=['POST'])
@token_required
def create_note(current_user):
    """Cria nova anotação"""
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'error': 'Conteúdo da anotação é obrigatório'}), 400
        
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Conteúdo não pode estar vazio'}), 400
        
        # Parâmetros opcionais
        source = data.get('source', 'app')
        category = data.get('category')
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        
        # Valida categoria se fornecida
        if category:
            cat_obj = Category.find_or_create_by_name(current_user.id, category)
            category = cat_obj.name
        
        # Cria anotação
        note = Note(
            user_id=current_user.id,
            content=content,
            source=source,
            category=category,
            tags=tags,
            metadata=metadata
        )
        
        db.session.add(note)
        db.session.commit()
        
        # TODO: Adicionar à fila de processamento IA
        
        return jsonify({
            'message': 'Anotação criada com sucesso',
            'note': note.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/<note_id>', methods=['GET'])
@token_required
def get_note(current_user, note_id):
    """Retorna anotação específica"""
    try:
        note = Note.query.filter_by(
            id=note_id,
            user_id=current_user.id
        ).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        include_insights = request.args.get('include_insights', 'false').lower() == 'true'
        
        return jsonify({
            'note': note.to_dict(include_insights=include_insights)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/<note_id>', methods=['PUT'])
@token_required
def update_note(current_user, note_id):
    """Atualiza anotação existente"""
    try:
        note = Note.query.filter_by(
            id=note_id,
            user_id=current_user.id
        ).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados são obrigatórios'}), 400
        
        # Atualiza campos se fornecidos
        if 'content' in data:
            content = data['content'].strip()
            if not content:
                return jsonify({'error': 'Conteúdo não pode estar vazio'}), 400
            note.content = content
        
        if 'category' in data:
            category = data['category']
            if category:
                cat_obj = Category.find_or_create_by_name(current_user.id, category)
                note.category = cat_obj.name
            else:
                note.category = None
        
        if 'tags' in data:
            note.set_tags(data['tags'])
        
        if 'metadata' in data:
            current_metadata = note.get_metadata()
            current_metadata.update(data['metadata'])
            note.set_metadata(current_metadata)
        
        note.updated_at = datetime.utcnow()
        db.session.commit()
        
        # TODO: Re-processar com IA se conteúdo mudou significativamente
        
        return jsonify({
            'message': 'Anotação atualizada com sucesso',
            'note': note.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/<note_id>', methods=['DELETE'])
@token_required
def delete_note(current_user, note_id):
    """Remove anotação"""
    try:
        note = Note.query.filter_by(
            id=note_id,
            user_id=current_user.id
        ).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        # Remove anotação e relacionamentos (cascade)
        db.session.delete(note)
        db.session.commit()
        
        return jsonify({'message': 'Anotação removida com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/<note_id>/insights', methods=['GET'])
@token_required
def get_note_insights(current_user, note_id):
    """Retorna insights da anotação"""
    try:
        note = Note.query.filter_by(
            id=note_id,
            user_id=current_user.id
        ).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        insights = Insight.query.filter_by(
            note_id=note_id,
            user_id=current_user.id
        ).order_by(Insight.created_at.desc()).all()
        
        return jsonify({
            'insights': [insight.to_dict() for insight in insights]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/<note_id>/insights', methods=['POST'])
@token_required
def create_insight(current_user, note_id):
    """Cria insight para anotação (usado pelo sistema de IA)"""
    try:
        note = Note.query.filter_by(
            id=note_id,
            user_id=current_user.id
        ).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        data = request.get_json()
        if not data or not data.get('insight_type') or not data.get('content'):
            return jsonify({'error': 'Tipo e conteúdo do insight são obrigatórios'}), 400
        
        insight = Insight(
            user_id=current_user.id,
            note_id=note_id,
            insight_type=data['insight_type'],
            content=data['content'],
            confidence_score=data.get('confidence_score', 0.0),
            metadata=data.get('metadata', {})
        )
        
        db.session.add(insight)
        db.session.commit()
        
        return jsonify({
            'message': 'Insight criado com sucesso',
            'insight': insight.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/insights/<insight_id>/dismiss', methods=['POST'])
@token_required
def dismiss_insight(current_user, insight_id):
    """Marca insight como dispensado"""
    try:
        insight = Insight.query.filter_by(
            id=insight_id,
            user_id=current_user.id
        ).first()
        
        if not insight:
            return jsonify({'error': 'Insight não encontrado'}), 404
        
        insight.dismiss()
        db.session.commit()
        
        return jsonify({'message': 'Insight dispensado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/search', methods=['GET'])
@token_required
def search_notes(current_user):
    """Busca avançada de anotações"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query de busca é obrigatória'}), 400
        
        category = request.args.get('category')
        tags = request.args.getlist('tags')
        limit = min(int(request.args.get('limit', 10)), 50)
        offset = int(request.args.get('offset', 0))
        
        # Busca básica por conteúdo (em produção, usar Elasticsearch)
        notes = Note.get_by_user(
            user_id=current_user.id,
            category=category,
            tags=tags,
            limit=limit,
            offset=offset,
            search=query
        )
        
        total_count = Note.count_by_user(
            user_id=current_user.id,
            category=category,
            tags=tags,
            search=query
        )
        
        return jsonify({
            'query': query,
            'results': [note.to_dict(include_content=False) for note in notes],
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/stats', methods=['GET'])
@token_required
def get_notes_stats(current_user):
    """Retorna estatísticas das anotações do usuário"""
    try:
        # Contagem total
        total_notes = Note.query.filter_by(user_id=current_user.id).count()
        
        # Contagem por categoria
        category_stats = db.session.query(
            Note.category,
            db.func.count(Note.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Note.category).all()
        
        # Contagem por fonte
        source_stats = db.session.query(
            Note.source,
            db.func.count(Note.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Note.source).all()
        
        # Contagem por status de processamento
        status_stats = db.session.query(
            Note.status,
            db.func.count(Note.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Note.status).all()
        
        # Anotações recentes (últimos 7 dias)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_notes = Note.query.filter(
            Note.user_id == current_user.id,
            Note.created_at >= week_ago
        ).count()
        
        return jsonify({
            'total_notes': total_notes,
            'recent_notes': recent_notes,
            'by_category': [{'category': cat or 'Sem categoria', 'count': count} for cat, count in category_stats],
            'by_source': [{'source': source, 'count': count} for source, count in source_stats],
            'by_status': [{'status': status, 'count': count} for status, count in status_stats]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/export', methods=['GET'])
@token_required
def export_notes(current_user):
    """Exporta anotações do usuário"""
    try:
        format_type = request.args.get('format', 'json').lower()
        category = request.args.get('category')
        
        # Busca todas as anotações (sem limite)
        notes = Note.get_by_user(
            user_id=current_user.id,
            category=category,
            limit=10000  # Limite alto para exportação
        )
        
        if format_type == 'json':
            export_data = {
                'user_id': current_user.id,
                'exported_at': datetime.utcnow().isoformat(),
                'total_notes': len(notes),
                'notes': [note.to_dict(include_insights=True) for note in notes]
            }
            
            return jsonify(export_data), 200
            
        elif format_type == 'markdown':
            # Gera markdown
            md_content = f"# Anotações - {current_user.name or current_user.email}\n\n"
            md_content += f"Exportado em: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}\n\n"
            
            current_category = None
            for note in notes:
                if note.category != current_category:
                    current_category = note.category
                    md_content += f"\n## {current_category or 'Sem categoria'}\n\n"
                
                md_content += f"### {note.get_title()}\n\n"
                md_content += f"**Criado em:** {note.created_at.strftime('%d/%m/%Y %H:%M')}\n"
                md_content += f"**Fonte:** {note.source}\n"
                
                if note.get_tags():
                    md_content += f"**Tags:** {', '.join(note.get_tags())}\n"
                
                md_content += f"\n{note.content}\n\n"
                
                if note.insights:
                    md_content += "**Insights:**\n"
                    for insight in note.insights:
                        md_content += f"- {insight.content}\n"
                    md_content += "\n"
                
                md_content += "---\n\n"
            
            return md_content, 200, {'Content-Type': 'text/markdown'}
            
        else:
            return jsonify({'error': 'Formato não suportado'}), 400
            
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@notes_bp.route('/bulk', methods=['POST'])
@token_required
def bulk_operations(current_user):
    """Operações em lote nas anotações"""
    try:
        data = request.get_json()
        if not data or not data.get('operation') or not data.get('note_ids'):
            return jsonify({'error': 'Operação e IDs das anotações são obrigatórios'}), 400
        
        operation = data['operation']
        note_ids = data['note_ids']
        
        # Verifica se todas as anotações pertencem ao usuário
        notes = Note.query.filter(
            Note.id.in_(note_ids),
            Note.user_id == current_user.id
        ).all()
        
        if len(notes) != len(note_ids):
            return jsonify({'error': 'Algumas anotações não foram encontradas'}), 404
        
        if operation == 'delete':
            for note in notes:
                db.session.delete(note)
            
        elif operation == 'update_category':
            new_category = data.get('category')
            if new_category:
                cat_obj = Category.find_or_create_by_name(current_user.id, new_category)
                new_category = cat_obj.name
            
            for note in notes:
                note.category = new_category
                note.updated_at = datetime.utcnow()
        
        elif operation == 'add_tags':
            new_tags = data.get('tags', [])
            for note in notes:
                current_tags = note.get_tags()
                for tag in new_tags:
                    if tag not in current_tags:
                        current_tags.append(tag)
                note.set_tags(current_tags)
                note.updated_at = datetime.utcnow()
        
        else:
            return jsonify({'error': 'Operação não suportada'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'Operação {operation} executada com sucesso',
            'affected_notes': len(notes)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

