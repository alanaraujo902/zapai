import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from src.models.user import UsageLog

class PerplexityService:
    """Serviço para integração com API do Perplexity"""
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.base_url = 'https://api.perplexity.ai'
        self.model = 'llama-3.1-sonar-small-128k-online'  # Modelo com acesso à web
        
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """Faz requisição para API do Perplexity"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY não configurada")
        
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
            raise Exception(f"Erro na API Perplexity: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _log_usage(self, user_id: str, endpoint: str, tokens_used: int, cost: float):
        """Registra uso da API para controle de custos"""
        UsageLog.log_usage(
            user_id=user_id,
            api_type='perplexity',
            endpoint=endpoint,
            tokens_used=tokens_used,
            cost=cost
        )
    
    def search_related_information(self, user_id: str, note_content: str, search_focus: str = None) -> dict:
        """Busca informações relacionadas ao conteúdo da anotação"""
        
        # Constrói query de busca baseada no conteúdo
        if search_focus:
            query = f"Busque informações atualizadas sobre: {search_focus}. Contexto: {note_content[:300]}"
        else:
            query = f"Busque informações relevantes e atualizadas relacionadas a: {note_content[:300]}"
        
        messages = [
            {
                "role": "system",
                "content": """Você é um assistente de pesquisa especializado. 
                Busque informações atualizadas e relevantes sobre o tópico fornecido.
                Foque em:
                - Informações recentes e verificadas
                - Dados estatísticos quando relevantes
                - Tendências e desenvolvimentos atuais
                - Recursos úteis e referências
                
                Organize a resposta de forma clara e estruturada."""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.2,
            "return_citations": True,
            "return_images": False
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            # Extrai informações de uso
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            # Registra uso
            self._log_usage(user_id, 'search_information', tokens_used, cost)
            
            # Processa resposta
            content = response['choices'][0]['message']['content']
            citations = response.get('citations', [])
            
            return {
                'success': True,
                'information': content,
                'citations': citations,
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
    
    def find_related_events(self, user_id: str, note_content: str, location: str = None) -> dict:
        """Busca eventos relacionados ao conteúdo da anotação"""
        
        location_context = f" em {location}" if location else ""
        query = f"Busque eventos, conferências, workshops ou atividades relacionadas a: {note_content[:200]}{location_context}. Inclua datas, locais e informações de inscrição quando disponíveis."
        
        messages = [
            {
                "role": "system",
                "content": """Você é um assistente especializado em encontrar eventos e atividades.
                Busque informações sobre:
                - Eventos próximos relacionados ao tópico
                - Conferências e workshops
                - Cursos e treinamentos
                - Meetups e networking
                - Webinars e eventos online
                
                Para cada evento encontrado, inclua:
                - Nome e descrição
                - Data e horário
                - Local (presencial/online)
                - Informações de inscrição
                - Custo (se aplicável)"""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.3,
            "return_citations": True
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'find_events', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            citations = response.get('citations', [])
            
            return {
                'success': True,
                'events': content,
                'citations': citations,
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
    
    def suggest_tools_and_apps(self, user_id: str, note_content: str, platform: str = None) -> dict:
        """Sugere ferramentas e aplicativos relacionados ao conteúdo"""
        
        platform_context = f" para {platform}" if platform else ""
        query = f"Sugira ferramentas, aplicativos e recursos úteis relacionados a: {note_content[:200]}{platform_context}. Inclua opções gratuitas e pagas, com descrições e links quando possível."
        
        messages = [
            {
                "role": "system",
                "content": """Você é um especialista em ferramentas e tecnologia.
                Sugira recursos úteis como:
                - Aplicativos móveis e web
                - Ferramentas online
                - Software especializado
                - Extensões de navegador
                - APIs e serviços
                
                Para cada sugestão, inclua:
                - Nome e descrição
                - Plataformas suportadas
                - Preço (gratuito/pago)
                - Principais funcionalidades
                - Link oficial quando possível
                - Alternativas similares"""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.3,
            "return_citations": True
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'suggest_tools', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            citations = response.get('citations', [])
            
            return {
                'success': True,
                'suggestions': content,
                'citations': citations,
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
    
    def get_market_insights(self, user_id: str, topic: str, industry: str = None) -> dict:
        """Busca insights de mercado sobre um tópico específico"""
        
        industry_context = f" na indústria de {industry}" if industry else ""
        query = f"Forneça insights de mercado atualizados sobre: {topic}{industry_context}. Inclua tendências, estatísticas, oportunidades e desafios."
        
        messages = [
            {
                "role": "system",
                "content": """Você é um analista de mercado especializado.
                Forneça insights abrangentes incluindo:
                - Tendências atuais do mercado
                - Estatísticas e dados relevantes
                - Oportunidades emergentes
                - Principais desafios
                - Previsões e projeções
                - Principais players do mercado
                - Fatores de crescimento
                
                Base suas análises em dados recentes e fontes confiáveis."""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.2,
            "return_citations": True
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'market_insights', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            citations = response.get('citations', [])
            
            return {
                'success': True,
                'insights': content,
                'citations': citations,
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
    
    def fact_check_information(self, user_id: str, claim: str) -> dict:
        """Verifica a veracidade de uma informação"""
        
        query = f"Verifique a veracidade desta informação e forneça fontes confiáveis: {claim}"
        
        messages = [
            {
                "role": "system",
                "content": """Você é um verificador de fatos especializado.
                Para cada verificação, forneça:
                - Status da verificação (verdadeiro/falso/parcialmente verdadeiro/inconclusivo)
                - Explicação detalhada
                - Fontes confiáveis que sustentam ou refutam a informação
                - Contexto adicional relevante
                - Nuances importantes
                
                Seja imparcial e baseie-se apenas em fontes verificáveis."""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 600,
            "temperature": 0.1,
            "return_citations": True
        }
        
        try:
            response = self._make_request('chat/completions', data)
            
            usage = response.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used)
            
            self._log_usage(user_id, 'fact_check', tokens_used, cost)
            
            content = response['choices'][0]['message']['content']
            citations = response.get('citations', [])
            
            return {
                'success': True,
                'verification': content,
                'citations': citations,
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
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calcula custo baseado no número de tokens"""
        # Preços aproximados do Perplexity por 1K tokens
        cost_per_1k_tokens = 0.001  # $0.001 por 1K tokens (estimativa)
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

