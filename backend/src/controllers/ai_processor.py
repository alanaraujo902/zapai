import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.models.user import db, User
from src.models.note import Note, Insight
from src.models.category import Category
from src.services.chatgpt_service import ChatGPTService
from src.services.perplexity_service import PerplexityService
from src.services.whatsapp_service import WhatsAppService

class AIProcessor:
    """Orquestrador para processamento de anotações com IA"""
    
    def __init__(self):
        self.chatgpt = ChatGPTService()
        self.perplexity = PerplexityService()
        self.whatsapp = WhatsAppService()
    
    def process_note(self, note_id: str, user_preferences: dict = None) -> dict:
        """Processa uma anotação completa com IA"""
        try:
            # Busca anotação
            note = Note.query.get(note_id)
            if not note:
                return {'success': False, 'error': 'Anotação não encontrada'}
            
            # Verifica se usuário pode usar IA
            user = User.query.get(note.user_id)
            if not user.can_use_ai_features():
                return {'success': False, 'error': 'Limite de uso de IA atingido'}
            
            # Marca como processando
            note.mark_as_processing()
            db.session.commit()
            
            results = {}
            
            # 1. Análise inicial com ChatGPT
            chatgpt_result = self.chatgpt.analyze_note(
                user_id=note.user_id,
                note_content=note.content,
                user_preferences=user_preferences
            )
            
            if chatgpt_result['success']:
                results['chatgpt_analysis'] = chatgpt_result['analysis']
                
                # Aplica categoria sugerida
                category_name = chatgpt_result['analysis'].get('category_suggestion')
                if category_name:
                    category = Category.find_or_create_by_name(note.user_id, category_name)
                    note.category = category.name
                
                # Aplica tags sugeridas
                suggested_tags = chatgpt_result['analysis'].get('tags', [])
                note.set_tags(suggested_tags)
                
                # Cria insights
                self._create_insights_from_analysis(note, chatgpt_result['analysis'])
            
            # 2. Busca informações externas com Perplexity (se relevante)
            if self._should_search_external_info(note.content):
                perplexity_result = self.perplexity.search_related_information(
                    user_id=note.user_id,
                    note_content=note.content
                )
                
                if perplexity_result['success']:
                    results['external_info'] = perplexity_result['information']
                    results['citations'] = perplexity_result['citations']
                    
                    # Cria insight com informações externas
                    external_insight = Insight(
                        user_id=note.user_id,
                        note_id=note.id,
                        insight_type='external_info',
                        content=perplexity_result['information'],
                        confidence_score=0.8,
                        insight_metadata={
                            'citations': perplexity_result['citations'],
                            'source': 'perplexity'
                        }
                    )
                    db.session.add(external_insight)
            
            # 3. Extração de tarefas e prazos
            tasks_result = self.chatgpt.extract_tasks_and_deadlines(
                user_id=note.user_id,
                note_content=note.content
            )
            
            if tasks_result['success']:
                extraction = tasks_result['extraction']
                results['tasks'] = extraction.get('tasks', [])
                
                # Define prazo sugerido se encontrado
                tasks = extraction.get('tasks', [])
                if tasks:
                    # Pega a primeira tarefa com prazo
                    for task in tasks:
                        if task.get('deadline'):
                            try:
                                deadline = datetime.strptime(task['deadline'], '%Y-%m-%d')
                                note.deadline_suggested = deadline
                                break
                            except:
                                pass
                
                # Cria insights para tarefas
                for task in tasks:
                    task_insight = Insight(
                        user_id=note.user_id,
                        note_id=note.id,
                        insight_type='task',
                        content=task['task'],
                        confidence_score=task.get('confidence', 0.7),
                        insight_metadata={
                            'deadline': task.get('deadline'),
                            'priority': task.get('priority', 'média')
                        }
                    )
                    db.session.add(task_insight)
            
            # Marca como processada
            note.mark_as_processed()
            db.session.commit()
            
            # Envia insights via WhatsApp se habilitado
            if user.whatsapp_opt_in:
                self.whatsapp.send_ai_insights(
                    user_id=note.user_id,
                    note_id=note.id,
                    insights=chatgpt_result
                )
            
            return {
                'success': True,
                'note_id': note.id,
                'results': results
            }
            
        except Exception as e:
            # Marca como falha
            if 'note' in locals():
                note.mark_as_failed(str(e))
                db.session.commit()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_daily_notes(self, user_id: str, date: str = None) -> dict:
        """Processa todas as anotações do dia e gera resumo"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Busca anotações do dia
            start_date = datetime.strptime(date, '%Y-%m-%d')
            end_date = start_date + timedelta(days=1)
            
            notes = Note.query.filter(
                Note.user_id == user_id,
                Note.created_at >= start_date,
                Note.created_at < end_date
            ).all()
            
            if not notes:
                return {'success': True, 'message': 'Nenhuma anotação encontrada para o dia'}
            
            # Prepara dados das notas
            notes_data = []
            for note in notes:
                notes_data.append({
                    'id': note.id,
                    'content': note.content,
                    'category': note.category,
                    'tags': note.get_tags(),
                    'created_at': note.created_at.isoformat()
                })
            
            # Gera resumo diário
            summary_result = self.chatgpt.generate_daily_summary(
                user_id=user_id,
                notes=notes_data,
                date=date
            )
            
            if not summary_result['success']:
                return summary_result
            
            # Envia resumo via WhatsApp se habilitado
            user = User.query.get(user_id)
            if user and user.whatsapp_opt_in:
                self.whatsapp.send_daily_summary(user_id, summary_result['summary'])
            
            return {
                'success': True,
                'summary': summary_result['summary'],
                'notes_processed': len(notes)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def categorize_uncategorized_notes(self, user_id: str, limit: int = 10) -> dict:
        """Categoriza anotações sem categoria"""
        try:
            # Busca anotações sem categoria
            uncategorized_notes = Note.query.filter(
                Note.user_id == user_id,
                Note.category.is_(None)
            ).limit(limit).all()
            
            if not uncategorized_notes:
                return {'success': True, 'message': 'Nenhuma anotação sem categoria'}
            
            # Busca categorias existentes
            existing_categories = [cat.name for cat in Category.get_by_user(user_id)]
            
            # Prepara dados das notas
            notes_data = []
            for note in uncategorized_notes:
                notes_data.append({
                    'id': note.id,
                    'content': note.content[:200]  # Limita conteúdo
                })
            
            # Categoriza com ChatGPT
            categorization_result = self.chatgpt.categorize_notes(
                user_id=user_id,
                notes=notes_data,
                existing_categories=existing_categories
            )
            
            if not categorization_result['success']:
                return categorization_result
            
            categorization = categorization_result['categorization']
            applied_count = 0
            
            # Aplica categorizações
            for cat_data in categorization.get('categorizations', []):
                note_index = cat_data.get('note_index', 1) - 1  # Converte para índice 0-based
                
                if 0 <= note_index < len(uncategorized_notes):
                    note = uncategorized_notes[note_index]
                    category_name = cat_data.get('suggested_category')
                    
                    if category_name:
                        # Encontra ou cria categoria
                        category = Category.find_or_create_by_name(user_id, category_name)
                        note.category = category.name
                        applied_count += 1
            
            # Cria novas categorias sugeridas
            new_categories_created = 0
            for new_cat in categorization.get('new_categories', []):
                category_name = new_cat.get('name')
                if category_name and not Category.query.filter_by(
                    user_id=user_id, name=category_name
                ).first():
                    new_category = Category(
                        user_id=user_id,
                        name=category_name,
                        description=new_cat.get('description'),
                        icon=new_cat.get('suggested_icon', '📝'),
                        is_system_generated=True
                    )
                    db.session.add(new_category)
                    new_categories_created += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'notes_categorized': applied_count,
                'new_categories_created': new_categories_created,
                'categorization_details': categorization
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_related_notes(self, note_id: str) -> dict:
        """Encontra anotações relacionadas usando IA"""
        try:
            note = Note.query.get(note_id)
            if not note:
                return {'success': False, 'error': 'Anotação não encontrada'}
            
            # Busca outras anotações do usuário
            other_notes = Note.query.filter(
                Note.user_id == note.user_id,
                Note.id != note.id
            ).limit(50).all()  # Limita para performance
            
            if not other_notes:
                return {'success': True, 'related_notes': []}
            
            # TODO: Implementar análise de similaridade com embeddings
            # Por enquanto, busca por palavras-chave simples
            
            keywords = self._extract_keywords(note.content)
            related_notes = []
            
            for other_note in other_notes:
                similarity_score = self._calculate_simple_similarity(
                    note.content, other_note.content, keywords
                )
                
                if similarity_score > 0.3:  # Threshold de similaridade
                    related_notes.append({
                        'note_id': other_note.id,
                        'title': other_note.get_title(),
                        'similarity_score': similarity_score,
                        'category': other_note.category
                    })
            
            # Ordena por similaridade
            related_notes.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Atualiza nota com relacionadas
            related_ids = [rn['note_id'] for rn in related_notes[:5]]  # Top 5
            note.set_related_notes(related_ids)
            db.session.commit()
            
            return {
                'success': True,
                'related_notes': related_notes[:10]  # Retorna top 10
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_insights_from_analysis(self, note: Note, analysis: dict):
        """Cria insights baseados na análise do ChatGPT"""
        
        # Insight de resumo
        summary = analysis.get('summary')
        if summary:
            summary_insight = Insight(
                user_id=note.user_id,
                note_id=note.id,
                insight_type='summary',
                content=summary,
                confidence_score=analysis.get('confidence_score', 0.8)
            )
            db.session.add(summary_insight)
        
        # Insights de ações
        for action in analysis.get('action_items', []):
            action_insight = Insight(
                user_id=note.user_id,
                note_id=note.id,
                insight_type='action',
                content=action['action'],
                confidence_score=0.7,
                insight_metadata={'priority': action.get('priority', 'média')}
            )
            db.session.add(action_insight)
        
        # Insight de tópicos relacionados
        related_topics = analysis.get('related_topics', [])
        if related_topics:
            topics_insight = Insight(
                user_id=note.user_id,
                note_id=note.id,
                insight_type='connection',
                content=f"Tópicos relacionados: {', '.join(related_topics)}",
                confidence_score=0.6
            )
            db.session.add(topics_insight)
    
    def _should_search_external_info(self, content: str) -> bool:
        """Determina se deve buscar informações externas"""
        # Palavras-chave que indicam necessidade de busca externa
        search_keywords = [
            'preço', 'custo', 'valor', 'mercado', 'tendência',
            'notícia', 'evento', 'conferência', 'curso',
            'empresa', 'startup', 'investimento', 'ação',
            'tecnologia', 'ferramenta', 'app', 'software'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in search_keywords)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave simples do texto"""
        # Implementação simples - em produção usaria NLP mais avançado
        words = text.lower().split()
        
        # Remove palavras comuns
        stop_words = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
            'em', 'no', 'na', 'nos', 'nas', 'para', 'por', 'com', 'sem',
            'e', 'ou', 'mas', 'que', 'se', 'é', 'são', 'foi', 'foram'
        }
        
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return list(set(keywords))[:10]  # Top 10 palavras únicas
    
    def _calculate_simple_similarity(self, text1: str, text2: str, keywords: List[str]) -> float:
        """Calcula similaridade simples entre textos"""
        text2_lower = text2.lower()
        
        # Conta quantas palavras-chave aparecem no segundo texto
        matches = sum(1 for keyword in keywords if keyword in text2_lower)
        
        if not keywords:
            return 0.0
        
        return matches / len(keywords)
    
    def get_processing_stats(self, user_id: str) -> dict:
        """Retorna estatísticas de processamento do usuário"""
        try:
            # Conta anotações por status
            total_notes = Note.query.filter_by(user_id=user_id).count()
            processed_notes = Note.query.filter_by(user_id=user_id, status='processed').count()
            pending_notes = Note.query.filter_by(user_id=user_id, status='pending').count()
            processing_notes = Note.query.filter_by(user_id=user_id, status='processing').count()
            failed_notes = Note.query.filter_by(user_id=user_id, status='failed').count()
            
            # Conta insights gerados
            total_insights = Insight.query.filter_by(user_id=user_id).count()
            
            # Uso de APIs hoje
            from src.models.user import UsageLog
            today = datetime.now().date()
            
            chatgpt_usage_today = UsageLog.query.filter(
                UsageLog.user_id == user_id,
                UsageLog.api_type == 'chatgpt',
                db.func.date(UsageLog.created_at) == today
            ).count()
            
            perplexity_usage_today = UsageLog.query.filter(
                UsageLog.user_id == user_id,
                UsageLog.api_type == 'perplexity',
                db.func.date(UsageLog.created_at) == today
            ).count()
            
            return {
                'success': True,
                'stats': {
                    'total_notes': total_notes,
                    'processed_notes': processed_notes,
                    'pending_notes': pending_notes,
                    'processing_notes': processing_notes,
                    'failed_notes': failed_notes,
                    'total_insights': total_insights,
                    'api_usage_today': {
                        'chatgpt': chatgpt_usage_today,
                        'perplexity': perplexity_usage_today
                    }
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

