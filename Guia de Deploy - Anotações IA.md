# Guia de Deploy - Anotações IA

**Versão:** 1.0.0  
**Ambiente:** Produção  
**Última Atualização:** Julho 2025

---

## 🎯 Visão Geral

Este guia fornece instruções detalhadas para deploy do Sistema de Anotações IA em ambiente de produção. Inclui configurações de segurança, otimizações de performance e monitoramento.

## 📋 Pré-requisitos

### Infraestrutura Necessária

**Servidor Principal:**
- Ubuntu 22.04 LTS (recomendado)
- 8GB RAM mínimo (16GB recomendado)
- 50GB SSD (100GB+ para alta escala)
- 2 vCPUs mínimo (4+ recomendado)

**Banco de Dados:**
- PostgreSQL 14+ com backup automatizado
- Redis 6+ para cache e sessões
- Conexões SSL configuradas

**Rede e Segurança:**
- Domínio próprio com DNS configurado
- Certificado SSL válido (Let's Encrypt ou comercial)
- Firewall configurado (UFW ou iptables)
- Proxy reverso (Nginx recomendado)

### Contas e APIs Necessárias

**Serviços de IA:**
- Conta OpenAI com acesso GPT-4
- Conta Perplexity AI com créditos
- Limites de API configurados

**WhatsApp Business:**
- Conta Meta Business verificada
- WhatsApp Business API configurada
- Webhook URL configurada

**Monitoramento (Opcional):**
- Conta Sentry para error tracking
- Prometheus/Grafana para métricas
- Uptime monitoring (UptimeRobot, etc.)

## 🚀 Processo de Deploy

### 1. Preparação do Servidor

```bash
# Atualização do sistema
sudo apt update && sudo apt upgrade -y

# Instalação de dependências básicas
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib redis-server git curl

# Configuração de firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Criação de usuário para aplicação
sudo adduser anotacoes
sudo usermod -aG sudo anotacoes
```

### 2. Configuração do Banco de Dados

```bash
# Configuração PostgreSQL
sudo -u postgres psql

-- Criação do banco e usuário
CREATE DATABASE anotacoes_prod;
CREATE USER anotacoes_user WITH ENCRYPTED PASSWORD 'senha_super_segura';
GRANT ALL PRIVILEGES ON DATABASE anotacoes_prod TO anotacoes_user;
ALTER USER anotacoes_user CREATEDB;
\q

# Configuração Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Configuração de backup automático
sudo crontab -e
# Adicionar linha para backup diário às 2h
0 2 * * * pg_dump -U anotacoes_user -h localhost anotacoes_prod | gzip > /backup/anotacoes_$(date +\%Y\%m\%d).sql.gz
```

### 3. Deploy do Backend

```bash
# Clone do repositório
cd /home/anotacoes
git clone https://github.com/usuario/anotacoes-ia.git
cd anotacoes-ia/backend

# Configuração do ambiente Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Configuração de variáveis de ambiente
cp .env.example .env.prod
nano .env.prod
```

**Arquivo .env.prod:**
```bash
# Banco de dados
DATABASE_URL=postgresql://anotacoes_user:senha_super_segura@localhost/anotacoes_prod
REDIS_URL=redis://localhost:6379/0

# Segurança
SECRET_KEY=chave_secreta_super_complexa_aqui
JWT_SECRET_KEY=outra_chave_secreta_para_jwt

# APIs externas
OPENAI_API_KEY=sk-sua_chave_openai_aqui
PERPLEXITY_API_KEY=pplx-sua_chave_perplexity_aqui

# WhatsApp
WHATSAPP_VERIFY_TOKEN=token_verificacao_webhook_seguro
WHATSAPP_ACCESS_TOKEN=seu_token_whatsapp_business

# Configurações de produção
FLASK_ENV=production
DEBUG=False
TESTING=False

# Monitoramento
SENTRY_DSN=https://sua_dsn_sentry_aqui
```

```bash
# Migração do banco de dados
export FLASK_APP=src/main.py
flask db upgrade

# Teste do backend
python src/main.py
# Ctrl+C para parar

# Configuração do serviço systemd
sudo nano /etc/systemd/system/anotacoes-backend.service
```

**Arquivo anotacoes-backend.service:**
```ini
[Unit]
Description=Anotacoes IA Backend
After=network.target

[Service]
User=anotacoes
Group=anotacoes
WorkingDirectory=/home/anotacoes/anotacoes-ia/backend
Environment=PATH=/home/anotacoes/anotacoes-ia/backend/venv/bin
EnvironmentFile=/home/anotacoes/anotacoes-ia/backend/.env.prod
ExecStart=/home/anotacoes/anotacoes-ia/backend/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 src.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Ativação do serviço
sudo systemctl daemon-reload
sudo systemctl enable anotacoes-backend
sudo systemctl start anotacoes-backend
sudo systemctl status anotacoes-backend
```

### 4. Deploy do Frontend

```bash
# Configuração do frontend
cd /home/anotacoes/anotacoes-ia/frontend
npm install

# Configuração de variáveis de ambiente
nano .env.production
```

**Arquivo .env.production:**
```bash
REACT_APP_API_URL=https://seu-dominio.com/api
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

```bash
# Build para produção
npm run build

# Cópia para diretório web
sudo mkdir -p /var/www/anotacoes-ia
sudo cp -r build/* /var/www/anotacoes-ia/
sudo chown -R www-data:www-data /var/www/anotacoes-ia
```

### 5. Configuração do Nginx

```bash
# Configuração do site
sudo nano /etc/nginx/sites-available/anotacoes-ia
```

**Arquivo anotacoes-ia:**
```nginx
# Redirecionamento HTTP para HTTPS
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

# Configuração HTTPS principal
server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # Configurações SSL seguras
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Configuração de logs
    access_log /var/log/nginx/anotacoes-ia.access.log;
    error_log /var/log/nginx/anotacoes-ia.error.log;

    # Proxy para API backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Servir arquivos estáticos do frontend
    location / {
        root /var/www/anotacoes-ia;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache para assets estáticos
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Configuração específica para webhook WhatsApp
    location /api/whatsapp/webhook {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Sem timeout para webhooks
        proxy_read_timeout 300s;
    }

    # Configuração de compressão
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

```bash
# Ativação do site
sudo ln -s /etc/nginx/sites-available/anotacoes-ia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Configuração SSL com Let's Encrypt

```bash
# Instalação Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenção do certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Configuração de renovação automática
sudo crontab -e
# Adicionar linha para renovação automática
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Configurações de Produção

### Otimizações de Performance

**PostgreSQL (postgresql.conf):**
```sql
# Configurações de memória
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 64MB

# Configurações de checkpoint
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Configurações de conexão
max_connections = 200
```

**Redis (redis.conf):**
```conf
# Configurações de memória
maxmemory 1gb
maxmemory-policy allkeys-lru

# Configurações de persistência
save 900 1
save 300 10
save 60 10000

# Configurações de rede
timeout 300
tcp-keepalive 300
```

### Monitoramento e Logs

**Configuração Logrotate:**
```bash
sudo nano /etc/logrotate.d/anotacoes-ia
```

```conf
/var/log/nginx/anotacoes-ia.*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}

/home/anotacoes/anotacoes-ia/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 anotacoes anotacoes
}
```

**Script de Monitoramento:**
```bash
#!/bin/bash
# /home/anotacoes/scripts/health-check.sh

# Verificação do backend
if ! curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "Backend down, restarting..."
    sudo systemctl restart anotacoes-backend
    # Enviar alerta por email/Slack
fi

# Verificação do banco de dados
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "Database connection failed"
    # Enviar alerta crítico
fi

# Verificação de espaço em disco
DISK_USAGE=$(df / | grep -vE '^Filesystem' | awk '{print $5}' | sed 's/%//g')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is ${DISK_USAGE}%"
    # Enviar alerta de espaço
fi
```

```bash
# Configuração do cron para monitoramento
chmod +x /home/anotacoes/scripts/health-check.sh
crontab -e
# Adicionar verificação a cada 5 minutos
*/5 * * * * /home/anotacoes/scripts/health-check.sh
```

## 🔒 Segurança

### Configurações de Firewall

```bash
# Configuração UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Proteção contra ataques de força bruta
sudo apt install fail2ban
sudo nano /etc/fail2ban/jail.local
```

**Arquivo jail.local:**
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/*error.log
findtime = 600
bantime = 7200
maxretry = 10
```

### Backup e Recuperação

**Script de Backup Completo:**
```bash
#!/bin/bash
# /home/anotacoes/scripts/backup.sh

BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump -U anotacoes_user -h localhost anotacoes_prod | gzip > $BACKUP_DIR/database.sql.gz

# Backup dos arquivos de configuração
tar -czf $BACKUP_DIR/config.tar.gz /home/anotacoes/anotacoes-ia/backend/.env.prod /etc/nginx/sites-available/anotacoes-ia

# Backup dos logs importantes
tar -czf $BACKUP_DIR/logs.tar.gz /var/log/nginx/anotacoes-ia.*.log /home/anotacoes/anotacoes-ia/backend/logs/

# Limpeza de backups antigos (manter 30 dias)
find /backup -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

## 📊 Monitoramento

### Métricas Importantes

**Sistema:**
- CPU usage < 70%
- Memory usage < 80%
- Disk usage < 80%
- Network latency < 100ms

**Aplicação:**
- Response time < 500ms
- Error rate < 1%
- Uptime > 99.9%
- Database connections < 80% do limite

**APIs Externas:**
- OpenAI API calls/min
- Perplexity API calls/min
- WhatsApp webhook response time
- Rate limiting status

### Alertas Recomendados

1. **Críticos:** Database down, application down, disk full
2. **Importantes:** High error rate, slow response time, API limits
3. **Informativos:** High usage, backup completion, certificate expiry

## 🚀 Deploy Automatizado

**Script de Deploy:**
```bash
#!/bin/bash
# /home/anotacoes/scripts/deploy.sh

set -e

echo "Starting deployment..."

# Backup antes do deploy
/home/anotacoes/scripts/backup.sh

# Atualização do código
cd /home/anotacoes/anotacoes-ia
git pull origin main

# Atualização do backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade

# Atualização do frontend
cd ../frontend
npm install
npm run build
sudo cp -r build/* /var/www/anotacoes-ia/

# Restart dos serviços
sudo systemctl restart anotacoes-backend
sudo systemctl reload nginx

# Verificação de saúde
sleep 10
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "Deployment successful!"
else
    echo "Deployment failed - rolling back..."
    # Implementar rollback aqui
    exit 1
fi
```

---

**🎉 Parabéns!** Seu sistema Anotações IA está agora rodando em produção com todas as configurações de segurança e performance otimizadas!

