import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.models.user import UsageLog

class ChatGPTService:
    """Serviço para integração com API do ChatGPT/OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = 'https://api.openai.com/v1'
        self.model = 'gpt-4o-mini'  # Modelo mais econômico
        self.max_tokens = 1000
        
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """Faz requisição para API do OpenAI"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.base_url}/{endpoint}",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Erro na API OpenAI: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _log_usage(self, user_id: str, endpoint: str, tokens_used: int, cost: float):
        """Registra uso da API para controle de custos"""
        UsageLog.log_usage(
            user_id=user_id,
            api_type='chatgpt',
            endpoint=endpoint,
            tokens_used=tokens_used,
            cost=cost
        )
    
    def analyze_note(self, user_id: str, note_content: str, user_preferences: dict = None) -> dict:
        """Analisa uma anotação e retorna insights organizados"""
        
        # Prompt personalizado baseado nas preferências do usuário
        system_prompt = self._build_analysis_prompt(user_preferences)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analise esta anotação:\n\n{note_content}"}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            # Extrai informações de uso
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            # Registra uso
            self._log_usage(user_id, 'analyze_note', tokens_used, cost)
            
            # Processa resposta
            content = response['choices'][0]['message']['content']
            analysis = json.loads(content)
            
            return {
                'success': True,
                'analysis': analysis,
                'tokens_used': tokens_used,
                'cost': cost
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens_used': 0,
                'cost': 0
            }
    
    def categorize_notes(self, user_id: str, notes: List[dict], existing_categories: List[str] = None) -> dict:
        """Categoriza múltiplas anotações de uma vez"""
        
        # Prepara contexto das categorias existentes
        categories_context = ""
        if existing_categories:
            categories_context = f"Categorias existentes: {', '.join(existing_categories)}\n"
        
        # Prepara notas para análise
        notes_text = ""
        for i, note in enumerate(notes, 1):
            notes_text += f"{i}. {note.get('content', '')[:200]}...\n"
        
        system_prompt = f"""Você é um assistente especializado em organização de informações.
        
{categories_context}
Analise as anotações abaixo e sugira a melhor categoria para cada uma.
Prefira usar categorias existentes quando apropriado, mas pode sugerir novas se necessário.

Retorne um JSON com esta estrutura:
{{
    "categorizations": [
        {{
            "note_index": 1,
            "suggested_category": "nome_da_categoria",
            "confidence": 0.85,
            "reason": "explicação breve"
        }}
    ],
    "new_categories": [
        {{
            "name": "nova_categoria",
            "description": "descrição da categoria",
            "suggested_icon": "📝"
        }}
    ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": notes_text}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'categorize_notes', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            categorization = json.loads(content)
            
            return {
                'success': True,
                'categorization': categorization,
                'tokens_used': tokens_used,
                'cost': cost
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens_used': 0,
                'cost': 0
            }
    
    def generate_daily_summary(self, user_id: str, notes: List[dict], date: str) -> dict:
        """Gera resumo diário das anotações"""
        
        # Agrupa notas por categoria
        notes_by_category = {}
        for note in notes:
            category = note.get('category', 'Sem categoria')
            if category not in notes_by_category:
                notes_by_category[category] = []
            notes_by_category[category].append(note.get('content', ''))
        
        # Prepara contexto
        context = f"Resumo das anotações do dia {date}:\n\n"
        for category, category_notes in notes_by_category.items():
            context += f"**{category}:**\n"
            for note_content in category_notes:
                context += f"- {note_content[:150]}...\n"
            context += "\n"
        
        system_prompt = """Você é um assistente especializado em criar resumos organizados.

Analise as anotações do dia e crie um resumo estruturado que inclua:
1. Principais temas abordados
2. Tarefas e compromissos identificados
3. Insights e ideias importantes
4. Sugestões de ações para os próximos dias

Retorne um JSON com esta estrutura:
{
    "summary": {
        "main_themes": ["tema1", "tema2"],
        "tasks_identified": [
            {
                "task": "descrição da tarefa",
                "priority": "alta|média|baixa",
                "suggested_deadline": "YYYY-MM-DD ou null"
            }
        ],
        "key_insights": ["insight1", "insight2"],
        "action_suggestions": ["sugestão1", "sugestão2"],
        "overall_summary": "resumo geral do dia em 2-3 frases"
    }
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.4,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'daily_summary', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            summary = json.loads(content)
            
            return {
                'success': True,
                'summary': summary,
                'tokens_used': tokens_used,
                'cost': cost
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens_used': 0,
                'cost': 0
            }
    
    def extract_tasks_and_deadlines(self, user_id: str, note_content: str) -> dict:
        """Extrai tarefas e prazos de uma anotação"""
        
        system_prompt = """Você é um assistente especializado em identificar tarefas e prazos.

Analise o texto e identifique:
1. Tarefas explícitas ou implícitas
2. Datas e prazos mencionados
3. Prioridades sugeridas

Retorne um JSON com esta estrutura:
{
    "tasks": [
        {
            "task": "descrição da tarefa",
            "deadline": "YYYY-MM-DD ou null",
            "priority": "alta|média|baixa",
            "confidence": 0.85
        }
    ],
    "dates_mentioned": [
        {
            "date": "YYYY-MM-DD",
            "context": "contexto da data mencionada"
        }
    ]
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": note_content}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'extract_tasks', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            extraction = json.loads(content)
            
            return {
                'success': True,
                'extraction': extraction,
                'tokens_used': tokens_used,
                'cost': cost
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens_used': 0,
                'cost': 0
            }
    
    def _build_analysis_prompt(self, user_preferences: dict = None) -> str:
        """Constrói prompt personalizado baseado nas preferências do usuário"""
        
        base_prompt = """Você é um assistente especializado em análise e organização de anotações pessoais.

Analise a anotação fornecida e retorne insights úteis em formato JSON.
"""
        
        # Personaliza baseado nas preferências
        if user_preferences:
            focus_areas = user_preferences.get('focus_areas', [])
            if focus_areas:
                base_prompt += f"\nFoque especialmente em: {', '.join(focus_areas)}\n"
            
            organization_style = user_preferences.get('organization_style', 'balanced')
            if organization_style == 'detailed':
                base_prompt += "Forneça análises detalhadas e abrangentes.\n"
            elif organization_style == 'concise':
                base_prompt += "Mantenha as análises concisas e diretas.\n"
        
        base_prompt += """
Retorne um JSON com esta estrutura:
{
    "category_suggestion": "categoria sugerida",
    "tags": ["tag1", "tag2", "tag3"],
    "summary": "resumo em 1-2 frases",
    "key_points": ["ponto1", "ponto2"],
    "action_items": [
        {
            "action": "ação sugerida",
            "priority": "alta|média|baixa"
        }
    ],
    "related_topics": ["tópico1", "tópico2"],
    "sentiment": "positivo|neutro|negativo",
    "confidence_score": 0.85
}"""
        
        return base_prompt
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calcula custo baseado no número de tokens (GPT-4o-mini)"""
        # Preços aproximados por 1K tokens (input + output)
        cost_per_1k_tokens = 0.0002  # $0.0002 por 1K tokens
        return (tokens / 1000) * cost_per_1k_tokens
    
    def test_connection(self) -> bool:
        """Testa conexão com a API"""
        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            response = self._make_request('chat/completions', data)
            return True
        except:
            return False

