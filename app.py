from flask import Flask
import os

# Importa Blueprints
from controllers.login_controller import login_bp
from controllers.motorista_controller import motorista_bp
from controllers.ajudante_controller import ajudante_bp
from controllers.supervisor_controller import supervisor_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao-fraca')

# Registra Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(motorista_bp)
app.register_blueprint(ajudante_bp)
app.register_blueprint(supervisor_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
