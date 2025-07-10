from flask import Blueprint, request, jsonify
from src.services.whatsapp_service import WhatsAppService
from src.routes.auth import token_required

whatsapp_bp = Blueprint('whatsapp', __name__)
whatsapp_service = WhatsAppService()

@whatsapp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verifica webhook do WhatsApp"""
    try:
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        result = whatsapp_service.verify_webhook(mode, token, challenge)
        
        if result:
            return result, 200
        else:
            return 'Forbidden', 403
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    """Recebe mensagens do WhatsApp"""
    try:
        # Verifica assinatura para segurança
        signature = request.headers.get('X-Hub-Signature-256', '')
        payload = request.get_data(as_text=True)
        
        if not whatsapp_service.verify_signature(payload, signature):
            return 'Unauthorized', 401
        
        # Processa mensagem
        webhook_data = request.get_json()
        result = whatsapp_service.process_webhook_message(webhook_data)
        
        if result['success']:
            return 'OK', 200
        else:
            return jsonify({'error': result.get('error')}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/send-message', methods=['POST'])
@token_required
def send_message(current_user):
    """Envia mensagem via WhatsApp (para testes)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('phone') or not data.get('message'):
            return jsonify({'error': 'Telefone e mensagem são obrigatórios'}), 400
        
        phone = data['phone']
        message = data['message']
        
        success = whatsapp_service._send_text_message(phone, message)
        
        if success:
            return jsonify({'message': 'Mensagem enviada com sucesso'}), 200
        else:
            return jsonify({'error': 'Falha ao enviar mensagem'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/test-connection', methods=['GET'])
@token_required
def test_connection(current_user):
    """Testa conexão com WhatsApp API"""
    try:
        is_connected = whatsapp_service.test_connection()
        
        return jsonify({
            'connected': is_connected,
            'message': 'Conexão OK' if is_connected else 'Falha na conexão'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

