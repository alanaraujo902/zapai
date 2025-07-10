import os
import json
import requests
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional
from src.models.user import db, User
from src.models.note import Note
from src.models.category import Category

class WhatsAppService:
    """Serviço para integração com WhatsApp Business API"""
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        self.app_secret = os.getenv('WHATSAPP_APP_SECRET')
        self.base_url = 'https://graph.facebook.com/v18.0'
        
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verifica webhook do WhatsApp"""
        if mode == 'subscribe' and token == self.webhook_verify_token:
            return challenge
        return None
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verifica assinatura do webhook para segurança"""
        if not self.app_secret:
            return True  # Em desenvolvimento, pode pular verificação
        
        expected_signature = hmac.new(
            self.app_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def process_webhook_message(self, webhook_data: dict) -> dict:
        """Processa mensagem recebida via webhook"""
        try:
            # Extrai dados da mensagem
            entry = webhook_data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Verifica se há mensagens
            messages = value.get('messages', [])
            if not messages:
                return {'success': True, 'message': 'Nenhuma mensagem para processar'}
            
            results = []
            for message in messages:
                result = self._process_single_message(message, value)
                results.append(result)
            
            return {
                'success': True,
                'processed_messages': len(results),
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_single_message(self, message: dict, value: dict) -> dict:
        """Processa uma única mensagem"""
        try:
            # Extrai informações da mensagem
            from_number = message.get('from')
            message_id = message.get('id')
            timestamp = message.get('timestamp')
            message_type = message.get('type')
            
            # Busca usuário pelo número de telefone
            user = User.query.filter_by(phone_number=from_number).first()
            
            if not user:
                # Usuário não cadastrado - envia mensagem de boas-vindas
                self._send_welcome_message(from_number)
                return {
                    'success': True,
                    'action': 'welcome_sent',
                    'phone': from_number
                }
            
            # Processa conteúdo baseado no tipo
            content = self._extract_message_content(message)
            if not content:
                return {
                    'success': False,
                    'error': 'Tipo de mensagem não suportado',
                    'type': message_type
                }
            
            # Cria anotação
            note = Note(
                user_id=user.id,
                content=content,
                source='whatsapp',
                note_metadata={
                    'whatsapp_message_id': message_id,
                    'whatsapp_timestamp': timestamp,
                    'message_type': message_type,
                    'from_number': from_number
                }
            )
            
            db.session.add(note)
            db.session.commit()
            
            # Envia confirmação
            self._send_confirmation_message(from_number, note.id)
            
            # Agenda processamento IA (seria implementado com Celery/Redis)
            # self._schedule_ai_processing(note.id)
            
            return {
                'success': True,
                'action': 'note_created',
                'note_id': note.id,
                'user_id': user.id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_message_content(self, message: dict) -> Optional[str]:
        """Extrai conteúdo da mensagem baseado no tipo"""
        message_type = message.get('type')
        
        if message_type == 'text':
            return message.get('text', {}).get('body')
        
        elif message_type == 'image':
            # Para imagens, retorna caption + metadata
            image_data = message.get('image', {})
            caption = image_data.get('caption', '')
            image_id = image_data.get('id')
            
            # TODO: Baixar e processar imagem com OCR
            content = f"[IMAGEM] {caption}" if caption else "[IMAGEM]"
            return content
        
        elif message_type == 'document':
            # Para documentos
            doc_data = message.get('document', {})
            filename = doc_data.get('filename', 'documento')
            caption = doc_data.get('caption', '')
            
            content = f"[DOCUMENTO: {filename}] {caption}" if caption else f"[DOCUMENTO: {filename}]"
            return content
        
        elif message_type == 'audio':
            # Para áudios (seria processado com speech-to-text)
            return "[ÁUDIO] - Transcrição pendente"
        
        elif message_type == 'video':
            # Para vídeos
            video_data = message.get('video', {})
            caption = video_data.get('caption', '')
            
            content = f"[VÍDEO] {caption}" if caption else "[VÍDEO]"
            return content
        
        elif message_type == 'location':
            # Para localização
            location = message.get('location', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            name = location.get('name', '')
            address = location.get('address', '')
            
            content = f"[LOCALIZAÇÃO] {name} - {address} ({latitude}, {longitude})"
            return content
        
        return None
    
    def _send_welcome_message(self, phone_number: str):
        """Envia mensagem de boas-vindas para usuário não cadastrado"""
        message = """🤖 Olá! Sou seu assistente de anotações com IA.

Para começar a usar, você precisa se cadastrar no nosso app primeiro.

📱 Baixe o app: [LINK_DO_APP]
🌐 Acesse via web: [LINK_WEB]

Após o cadastro, vincule este número nas configurações para começar a enviar suas anotações!"""
        
        self._send_text_message(phone_number, message)
    
    def _send_confirmation_message(self, phone_number: str, note_id: str):
        """Envia confirmação de recebimento da anotação"""
        message = f"""✅ Anotação recebida e salva!

🆔 ID: {note_id[:8]}...
⏰ Processamento IA iniciado

Você receberá insights organizados em breve no app."""
        
        self._send_text_message(phone_number, message)
    
    def _send_text_message(self, phone_number: str, message: str):
        """Envia mensagem de texto via WhatsApp API"""
        if not self.access_token or not self.phone_number_id:
            return False
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'messaging_product': 'whatsapp',
            'to': phone_number,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def send_daily_summary(self, user_id: str, summary_data: dict):
        """Envia resumo diário para o usuário via WhatsApp"""
        user = User.query.get(user_id)
        if not user or not user.phone_number or not user.whatsapp_opt_in:
            return False
        
        # Formata resumo
        summary = summary_data.get('summary', {})
        message = f"""📊 *Resumo do seu dia*

🎯 *Principais temas:*
{', '.join(summary.get('main_themes', []))}

✅ *Tarefas identificadas:*
"""
        
        tasks = summary.get('tasks_identified', [])
        for task in tasks[:3]:  # Limita a 3 tarefas
            priority_emoji = {'alta': '🔴', 'média': '🟡', 'baixa': '🟢'}.get(task.get('priority', 'média'), '🟡')
            message += f"{priority_emoji} {task.get('task', '')}\n"
        
        if len(tasks) > 3:
            message += f"... e mais {len(tasks) - 3} tarefas\n"
        
        message += f"""
💡 *Insights principais:*
{chr(10).join(f"• {insight}" for insight in summary.get('key_insights', [])[:2])}

📱 Veja mais detalhes no app!"""
        
        return self._send_text_message(user.phone_number, message)
    
    def send_ai_insights(self, user_id: str, note_id: str, insights: dict):
        """Envia insights de IA para o usuário"""
        user = User.query.get(user_id)
        if not user or not user.phone_number or not user.whatsapp_opt_in:
            return False
        
        analysis = insights.get('analysis', {})
        
        message = f"""🤖 *Insights da sua anotação*

📂 *Categoria:* {analysis.get('category_suggestion', 'Não definida')}

📝 *Resumo:* {analysis.get('summary', '')}

🏷️ *Tags:* {', '.join(analysis.get('tags', []))}

✅ *Ações sugeridas:*
"""
        
        actions = analysis.get('action_items', [])
        for action in actions[:2]:  # Limita a 2 ações
            priority_emoji = {'alta': '🔴', 'média': '🟡', 'baixa': '🟢'}.get(action.get('priority', 'média'), '🟡')
            message += f"{priority_emoji} {action.get('action', '')}\n"
        
        message += "\n📱 Veja análise completa no app!"
        
        return self._send_text_message(user.phone_number, message)
    
    def send_reminder(self, user_id: str, reminder_text: str):
        """Envia lembrete para o usuário"""
        user = User.query.get(user_id)
        if not user or not user.phone_number or not user.whatsapp_opt_in:
            return False
        
        message = f"""⏰ *Lembrete*

{reminder_text}

📱 Gerencie seus lembretes no app!"""
        
        return self._send_text_message(user.phone_number, message)
    
    def get_media_url(self, media_id: str) -> Optional[str]:
        """Obtém URL de mídia para download"""
        if not self.access_token:
            return None
        
        url = f"{self.base_url}/{media_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('url')
        except:
            pass
        
        return None
    
    def download_media(self, media_url: str, save_path: str) -> bool:
        """Baixa arquivo de mídia"""
        if not self.access_token:
            return False
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(media_url, headers=headers, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except:
            pass
        
        return False
    
    def test_connection(self) -> bool:
        """Testa conexão com a API do WhatsApp"""
        if not self.access_token or not self.phone_number_id:
            return False
        
        url = f"{self.base_url}/{self.phone_number_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False

