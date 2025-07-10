import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.note import Note, Insight, MediaFile
from src.models.category import Category
from src.routes.auth import auth_bp
from src.routes.notes import notes_bp
from src.routes.categories import categories_bp
from src.routes.user import user_bp
from src.routes.whatsapp import whatsapp_bp
from src.routes.ai import ai_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurações
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'  # Em produção, usar variável de ambiente
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Habilita CORS para todas as rotas
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Registra blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(notes_bp, url_prefix='/api/notes')
app.register_blueprint(categories_bp, url_prefix='/api/categories')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
app.register_blueprint(ai_bp, url_prefix='/api/ai')

# Inicializa banco de dados
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve arquivos estáticos e SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas"""
    return {"error": "Endpoint não encontrado"}, 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    return {"error": "Erro interno do servidor"}, 500

@app.route('/api/health')
def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "message": "Sistema de Anotações com IA funcionando",
        "version": "1.0.0"
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

