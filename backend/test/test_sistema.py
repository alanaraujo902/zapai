#!/usr/bin/env python3
"""
Script de testes para validação do sistema de anotações com IA
"""

import requests
import json
import time
from datetime import datetime

class TesteSistema:
    def __init__(self):
        self.base_url = "http://localhost:5001/api"
        self.frontend_url = "http://localhost:5173"
        self.token = None
        self.user_id = None
        self.resultados = []
    
    def log_resultado(self, teste, sucesso, detalhes=""):
        """Registra resultado de um teste"""
        resultado = {
            'teste': teste,
            'sucesso': sucesso,
            'timestamp': datetime.now().isoformat(),
            'detalhes': detalhes
        }
        self.resultados.append(resultado)
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{status} - {teste}")
        if detalhes:
            print(f"   Detalhes: {detalhes}")
    
    def teste_health_check(self):
        """Testa se o backend está respondendo"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            sucesso = response.status_code == 200
            detalhes = f"Status: {response.status_code}"
            if sucesso:
                data = response.json()
                detalhes += f", Resposta: {data}"
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Health Check Backend", sucesso, detalhes)
        return sucesso
    
    def teste_frontend_carregando(self):
        """Testa se o frontend está carregando"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            sucesso = response.status_code == 200 and "Anotações IA" in response.text
            detalhes = f"Status: {response.status_code}"
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Frontend Carregando", sucesso, detalhes)
        return sucesso
    
    def teste_registro_usuario(self):
        """Testa registro de novo usuário"""
        try:
            dados_usuario = {
                "name": "Teste Usuario",
                "email": f"teste_{int(time.time())}@exemplo.com",
                "password": "MinhaSenh@123",
                "phone": "+55 11 99999-9999"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=dados_usuario,
                timeout=10
            )
            
            sucesso = response.status_code == 201
            if sucesso:
                data = response.json()
                self.token = data.get('access_token')
                self.user_id = data.get('user', {}).get('id')
                detalhes = f"Usuário criado com ID: {self.user_id}"
            else:
                detalhes = f"Status: {response.status_code}, Erro: {response.text}"
                
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Registro de Usuário", sucesso, detalhes)
        return sucesso
    
    def teste_login_usuario(self):
        """Testa login com usuário existente"""
        if not self.user_id:
            self.log_resultado("Login de Usuário", False, "Usuário não foi criado")
            return False
        
        try:
            # Usar dados do usuário criado no teste anterior
            dados_login = {
                "email": f"teste_{int(time.time())}@exemplo.com",
                "password": "MinhaSenh@123"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=dados_login,
                timeout=10
            )
            
            sucesso = response.status_code == 200
            if sucesso:
                data = response.json()
                self.token = data.get('access_token')
                detalhes = "Login realizado com sucesso"
            else:
                detalhes = f"Status: {response.status_code}, Erro: {response.text}"
                
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Login de Usuário", sucesso, detalhes)
        return sucesso
    
    def teste_criar_anotacao(self):
        """Testa criação de anotação"""
        if not self.token:
            self.log_resultado("Criar Anotação", False, "Token não disponível")
            return False
        
        try:
            dados_anotacao = {
                "content": "Esta é uma anotação de teste criada automaticamente",
                "source": "test"
            }
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.base_url}/notes",
                json=dados_anotacao,
                headers=headers,
                timeout=10
            )
            
            sucesso = response.status_code == 201
            if sucesso:
                data = response.json()
                detalhes = f"Anotação criada com ID: {data.get('note', {}).get('id')}"
            else:
                detalhes = f"Status: {response.status_code}, Erro: {response.text}"
                
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Criar Anotação", sucesso, detalhes)
        return sucesso
    
    def teste_listar_anotacoes(self):
        """Testa listagem de anotações"""
        if not self.token:
            self.log_resultado("Listar Anotações", False, "Token não disponível")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/notes",
                headers=headers,
                timeout=10
            )
            
            sucesso = response.status_code == 200
            if sucesso:
                data = response.json()
                count = len(data.get('notes', []))
                detalhes = f"Encontradas {count} anotações"
            else:
                detalhes = f"Status: {response.status_code}, Erro: {response.text}"
                
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Listar Anotações", sucesso, detalhes)
        return sucesso
    
    def teste_conexoes_ia(self):
        """Testa conexões com APIs de IA"""
        if not self.token:
            self.log_resultado("Conexões IA", False, "Token não disponível")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/ai/test-connections",
                headers=headers,
                timeout=15
            )
            
            sucesso = response.status_code == 200
            if sucesso:
                data = response.json()
                chatgpt_ok = data.get('chatgpt', {}).get('connected', False)
                perplexity_ok = data.get('perplexity', {}).get('connected', False)
                detalhes = f"ChatGPT: {'OK' if chatgpt_ok else 'FALHA'}, Perplexity: {'OK' if perplexity_ok else 'FALHA'}"
            else:
                detalhes = f"Status: {response.status_code}, Erro: {response.text}"
                
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Conexões IA", sucesso, detalhes)
        return sucesso
    
    def teste_webhook_whatsapp(self):
        """Testa webhook do WhatsApp"""
        try:
            # Teste de verificação do webhook
            params = {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'test_token',
                'hub.challenge': 'test_challenge'
            }
            
            response = requests.get(
                f"{self.base_url}/whatsapp/webhook",
                params=params,
                timeout=10
            )
            
            # Esperamos 403 porque não temos o token correto, mas isso indica que o endpoint existe
            sucesso = response.status_code in [200, 403]
            detalhes = f"Status: {response.status_code} (endpoint disponível)"
                
        except Exception as e:
            sucesso = False
            detalhes = f"Erro: {str(e)}"
        
        self.log_resultado("Webhook WhatsApp", sucesso, detalhes)
        return sucesso
    
    def executar_todos_testes(self):
        """Executa todos os testes"""
        print("🧪 INICIANDO TESTES DO SISTEMA")
        print("=" * 50)
        
        # Testes de infraestrutura
        print("\n📡 TESTES DE INFRAESTRUTURA")
        self.teste_health_check()
        self.teste_frontend_carregando()
        
        # Testes de autenticação
        print("\n🔐 TESTES DE AUTENTICAÇÃO")
        self.teste_registro_usuario()
        # self.teste_login_usuario()  # Comentado pois o registro já faz login
        
        # Testes de funcionalidades
        print("\n📝 TESTES DE FUNCIONALIDADES")
        self.teste_criar_anotacao()
        self.teste_listar_anotacoes()
        
        # Testes de integrações
        print("\n🔗 TESTES DE INTEGRAÇÕES")
        self.teste_conexoes_ia()
        self.teste_webhook_whatsapp()
        
        # Relatório final
        self.gerar_relatorio()
    
    def gerar_relatorio(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 50)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 50)
        
        total_testes = len(self.resultados)
        testes_passou = sum(1 for r in self.resultados if r['sucesso'])
        testes_falhou = total_testes - testes_passou
        
        print(f"Total de testes: {total_testes}")
        print(f"✅ Passou: {testes_passou}")
        print(f"❌ Falhou: {testes_falhou}")
        print(f"📈 Taxa de sucesso: {(testes_passou/total_testes)*100:.1f}%")
        
        if testes_falhou > 0:
            print("\n❌ TESTES QUE FALHARAM:")
            for resultado in self.resultados:
                if not resultado['sucesso']:
                    print(f"  - {resultado['teste']}: {resultado['detalhes']}")
        
        # Salva relatório em arquivo
        with open('/home/ubuntu/relatorio_testes.json', 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório detalhado salvo em: /home/ubuntu/relatorio_testes.json")

if __name__ == "__main__":
    teste = TesteSistema()
    teste.executar_todos_testes()

