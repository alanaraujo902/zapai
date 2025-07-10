from flask import Blueprint, request, jsonify
from src.services.ai_processor import AIProcessor
from src.services.chatgpt_service import ChatGPTService
from src.services.perplexity_service import PerplexityService
from src.routes.auth import token_required

ai_bp = Blueprint('ai', __name__)
ai_processor = AIProcessor()
chatgpt_service = ChatGPTService()
perplexity_service = PerplexityService()

@ai_bp.route('/process-note/<note_id>', methods=['POST'])
@token_required
def process_note(current_user, note_id):
    """Processa uma anotação específica com IA"""
    try:
        # Verifica se a anotação pertence ao usuário
        from src.models.note import Note
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        # Obtém preferências do usuário
        user_preferences = current_user.get_preferences()
        
        # Processa com IA
        result = ai_processor.process_note(note_id, user_preferences)
        
        if result['success']:
            return jsonify({
                'message': 'Anotação processada com sucesso',
                'results': result['results']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/process-daily', methods=['POST'])
@token_required
def process_daily_notes(current_user):
    """Processa anotações do dia e gera resumo"""
    try:
        data = request.get_json() or {}
        date = data.get('date')  # Formato YYYY-MM-DD, opcional
        
        result = ai_processor.process_daily_notes(current_user.id, date)
        
        if result['success']:
            return jsonify({
                'message': 'Processamento diário concluído',
                'summary': result.get('summary'),
                'notes_processed': result.get('notes_processed', 0)
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/categorize-notes', methods=['POST'])
@token_required
def categorize_notes(current_user):
    """Categoriza anotações sem categoria"""
    try:
        data = request.get_json() or {}
        limit = min(data.get('limit', 10), 50)  # Máximo 50 por vez
        
        result = ai_processor.categorize_uncategorized_notes(current_user.id, limit)
        
        if result['success']:
            return jsonify({
                'message': 'Categorização concluída',
                'notes_categorized': result.get('notes_categorized', 0),
                'new_categories_created': result.get('new_categories_created', 0),
                'details': result.get('categorization_details')
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/find-related/<note_id>', methods=['GET'])
@token_required
def find_related_notes(current_user, note_id):
    """Encontra anotações relacionadas"""
    try:
        # Verifica se a anotação pertence ao usuário
        from src.models.note import Note
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        
        if not note:
            return jsonify({'error': 'Anotação não encontrada'}), 404
        
        result = ai_processor.find_related_notes(note_id)
        
        if result['success']:
            return jsonify({
                'related_notes': result['related_notes']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/search-external', methods=['POST'])
@token_required
def search_external_info(current_user):
    """Busca informações externas sobre um tópico"""
    try:
        data = request.get_json()
        
        if not data or not data.get('query'):
            return jsonify({'error': 'Query de busca é obrigatória'}), 400
        
        query = data['query']
        search_focus = data.get('focus')
        
        result = perplexity_service.search_related_information(
            user_id=current_user.id,
            note_content=query,
            search_focus=search_focus
        )
        
        if result['success']:
            return jsonify({
                'information': result['information'],
                'citations': result['citations'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/find-events', methods=['POST'])
@token_required
def find_events(current_user):
    """Busca eventos relacionados a um tópico"""
    try:
        data = request.get_json()
        
        if not data or not data.get('topic'):
            return jsonify({'error': 'Tópico é obrigatório'}), 400
        
        topic = data['topic']
        location = data.get('location')
        
        result = perplexity_service.find_related_events(
            user_id=current_user.id,
            note_content=topic,
            location=location
        )
        
        if result['success']:
            return jsonify({
                'events': result['events'],
                'citations': result['citations'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/suggest-tools', methods=['POST'])
@token_required
def suggest_tools(current_user):
    """Sugere ferramentas e apps para um tópico"""
    try:
        data = request.get_json()
        
        if not data or not data.get('topic'):
            return jsonify({'error': 'Tópico é obrigatório'}), 400
        
        topic = data['topic']
        platform = data.get('platform')
        
        result = perplexity_service.suggest_tools_and_apps(
            user_id=current_user.id,
            note_content=topic,
            platform=platform
        )
        
        if result['success']:
            return jsonify({
                'suggestions': result['suggestions'],
                'citations': result['citations'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/market-insights', methods=['POST'])
@token_required
def get_market_insights(current_user):
    """Obtém insights de mercado sobre um tópico"""
    try:
        data = request.get_json()
        
        if not data or not data.get('topic'):
            return jsonify({'error': 'Tópico é obrigatório'}), 400
        
        topic = data['topic']
        industry = data.get('industry')
        
        result = perplexity_service.get_market_insights(
            user_id=current_user.id,
            topic=topic,
            industry=industry
        )
        
        if result['success']:
            return jsonify({
                'insights': result['insights'],
                'citations': result['citations'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/fact-check', methods=['POST'])
@token_required
def fact_check(current_user):
    """Verifica veracidade de uma informação"""
    try:
        data = request.get_json()
        
        if not data or not data.get('claim'):
            return jsonify({'error': 'Informação para verificar é obrigatória'}), 400
        
        claim = data['claim']
        
        result = perplexity_service.fact_check_information(
            user_id=current_user.id,
            claim=claim
        )
        
        if result['success']:
            return jsonify({
                'verification': result['verification'],
                'citations': result['citations'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/analyze-text', methods=['POST'])
@token_required
def analyze_text(current_user):
    """Analisa texto livre com ChatGPT"""
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({'error': 'Texto para análise é obrigatório'}), 400
        
        text = data['text']
        user_preferences = current_user.get_preferences()
        
        result = chatgpt_service.analyze_note(
            user_id=current_user.id,
            note_content=text,
            user_preferences=user_preferences
        )
        
        if result['success']:
            return jsonify({
                'analysis': result['analysis'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/extract-tasks', methods=['POST'])
@token_required
def extract_tasks(current_user):
    """Extrai tarefas e prazos de um texto"""
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({'error': 'Texto é obrigatório'}), 400
        
        text = data['text']
        
        result = chatgpt_service.extract_tasks_and_deadlines(
            user_id=current_user.id,
            note_content=text
        )
        
        if result['success']:
            return jsonify({
                'extraction': result['extraction'],
                'tokens_used': result['tokens_used'],
                'cost': result['cost']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/stats', methods=['GET'])
@token_required
def get_ai_stats(current_user):
    """Retorna estatísticas de uso de IA"""
    try:
        result = ai_processor.get_processing_stats(current_user.id)
        
        if result['success']:
            return jsonify(result['stats']), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/test-connections', methods=['GET'])
@token_required
def test_ai_connections(current_user):
    """Testa conexões com APIs de IA"""
    try:
        chatgpt_connected = chatgpt_service.test_connection()
        perplexity_connected = perplexity_service.test_connection()
        
        return jsonify({
            'chatgpt': {
                'connected': chatgpt_connected,
                'status': 'OK' if chatgpt_connected else 'Falha'
            },
            'perplexity': {
                'connected': perplexity_connected,
                'status': 'OK' if perplexity_connected else 'Falha'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

