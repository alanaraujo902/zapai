from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
import re
from src.models.user import db, User, Session
from src.models.category import Category
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Valida formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida força da senha"""
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    return True, "Senha válida"

def validate_phone(phone):
    """Valida formato do telefone"""
    if not phone:
        return True  # Telefone é opcional
    
    # Remove espaços e caracteres especiais
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Verifica se tem formato válido (com ou sem código do país)
    pattern = r'^\+?[1-9]\d{10,14}$'
    return re.match(pattern, clean_phone) is not None

def generate_token(user_id, expires_in_hours=24):
    """Gera token JWT para o usuário"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def generate_refresh_token(user_id, expires_in_days=30):
    """Gera refresh token para renovação"""
    payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=expires_in_days),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verifica header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token de acesso requerido'}), 401
        
        try:
            # Decodifica token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # Verifica se usuário existe
            current_user = User.query.get(current_user_id)
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Usuário inválido'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra novo usuário"""
    try:
        data = request.get_json()
        
        # Validação de dados obrigatórios
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        # Validações
        if not validate_email(email):
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_message}), 400
        
        if phone and not validate_phone(phone):
            return jsonify({'error': 'Formato de telefone inválido'}), 400
        
        # Verifica se email já existe
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já cadastrado'}), 409
        
        # Verifica se telefone já existe (se fornecido)
        if phone and User.query.filter_by(phone_number=phone).first():
            return jsonify({'error': 'Telefone já cadastrado'}), 409
        
        # Cria novo usuário
        user = User(
            email=email,
            password=password,
            name=name if name else None,
            phone_number=phone if phone else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Cria categorias padrão para o usuário
        Category.create_default_categories(user.id)
        
        # Gera tokens
        access_token = generate_token(user.id)
        refresh_token = generate_refresh_token(user.id)
        
        # Cria sessão
        session = Session(
            user_id=user.id,
            token_hash=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        # Adiciona informações do dispositivo se disponível
        user_agent = request.headers.get('User-Agent', '')
        device_info = {
            'user_agent': user_agent,
            'ip_address': request.remote_addr
        }
        session.set_device_info(device_info)
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 24 * 3600  # 24 horas em segundos
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Autentica usuário existente"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Busca usuário
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Conta desativada'}), 401
        
        # Gera tokens
        access_token = generate_token(user.id)
        refresh_token = generate_refresh_token(user.id)
        
        # Cria nova sessão
        session = Session(
            user_id=user.id,
            token_hash=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        # Adiciona informações do dispositivo
        user_agent = request.headers.get('User-Agent', '')
        device_info = {
            'user_agent': user_agent,
            'ip_address': request.remote_addr,
            'login_time': datetime.utcnow().isoformat()
        }
        session.set_device_info(device_info)
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 24 * 3600
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Renova access token usando refresh token"""
    try:
        data = request.get_json()
        
        if not data or not data.get('refresh_token'):
            return jsonify({'error': 'Refresh token é obrigatório'}), 400
        
        refresh_token = data['refresh_token']
        
        try:
            # Decodifica refresh token
            payload = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            if payload.get('type') != 'refresh':
                return jsonify({'error': 'Token inválido'}), 401
            
            user_id = payload['user_id']
            
            # Verifica se usuário existe e está ativo
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'Usuário inválido'}), 401
            
            # Verifica se sessão existe e está ativa
            session = Session.query.filter_by(
                user_id=user_id,
                token_hash=refresh_token,
                is_active=True
            ).first()
            
            if not session or session.is_expired():
                return jsonify({'error': 'Sessão inválida ou expirada'}), 401
            
            # Gera novo access token
            new_access_token = generate_token(user_id)
            
            # Atualiza último acesso da sessão
            session.last_accessed = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'access_token': new_access_token,
                'expires_in': 24 * 3600
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Refresh token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Refresh token inválido'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Faz logout do usuário (invalida sessão)"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token') if data else None
        
        if refresh_token:
            # Invalida sessão específica
            session = Session.query.filter_by(
                user_id=current_user.id,
                token_hash=refresh_token
            ).first()
            
            if session:
                session.is_active = False
                db.session.commit()
        else:
            # Invalida todas as sessões do usuário
            Session.query.filter_by(user_id=current_user.id).update({'is_active': False})
            db.session.commit()
        
        return jsonify({'message': 'Logout realizado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Retorna informações do usuário autenticado"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/link-whatsapp', methods=['POST'])
@token_required
def link_whatsapp(current_user):
    """Inicia processo de vinculação do WhatsApp"""
    try:
        data = request.get_json()
        
        if not data or not data.get('phone'):
            return jsonify({'error': 'Número de telefone é obrigatório'}), 400
        
        phone = data['phone'].strip()
        
        if not validate_phone(phone):
            return jsonify({'error': 'Formato de telefone inválido'}), 400
        
        # Verifica se telefone já está vinculado a outra conta
        existing_user = User.query.filter(
            User.phone_number == phone,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Telefone já vinculado a outra conta'}), 409
        
        # TODO: Implementar envio de código de verificação via WhatsApp
        # Por enquanto, apenas atualiza o telefone
        current_user.phone_number = phone
        current_user.whatsapp_opt_in = True
        db.session.commit()
        
        return jsonify({
            'message': 'WhatsApp vinculado com sucesso',
            'phone': phone
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/unlink-whatsapp', methods=['POST'])
@token_required
def unlink_whatsapp(current_user):
    """Remove vinculação do WhatsApp"""
    try:
        current_user.phone_number = None
        current_user.whatsapp_opt_in = False
        db.session.commit()
        
        return jsonify({'message': 'WhatsApp desvinculado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/sessions', methods=['GET'])
@token_required
def get_user_sessions(current_user):
    """Lista sessões ativas do usuário"""
    try:
        sessions = Session.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(Session.last_accessed.desc()).all()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@token_required
def revoke_session(current_user, session_id):
    """Revoga uma sessão específica"""
    try:
        session = Session.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        session.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Sessão revogada com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

