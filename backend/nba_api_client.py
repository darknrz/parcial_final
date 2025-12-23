# backend/app.py - VERSION CON APIs REALES
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    jwt_required, get_jwt_identity
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import requests
import os
import traceback

# ✅ IMPORTAR CLIENTE DE APIs REALES
from nba_api_client import NBAApiClient

# ==================== CONFIGURACIÓN ====================
app = Flask(__name__)

# CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# MySQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Toloveru212@localhost/apuesta_ia'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'tu-clave-super-secreta-cambiala'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# URL del servicio ML
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:8000')

# ✅ Inicializar cliente de APIs
nba_client = NBAApiClient()

# ==================== JWT ERROR HANDLERS ====================

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Token inválido', 'message': str(error)}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Token no proporcionado', 'message': 'Authorization header requerido'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token expirado', 'message': 'El token ha expirado'}), 401

# ==================== MODELOS ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    home_team = db.Column(db.String(10), nullable=False)
    away_team = db.Column(db.String(10), nullable=False)
    predicted_winner = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    home_win_prob = db.Column(db.Float, nullable=False)
    away_win_prob = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'predicted_winner': self.predicted_winner,
            'confidence': round(self.confidence * 100, 2),
            'home_win_prob': round(self.home_win_prob * 100, 2),
            'away_win_prob': round(self.away_win_prob * 100, 2),
            'created_at': self.created_at.isoformat()
        }


# ==================== HELPER FUNCTIONS ====================

def normalize_team_name(team_input: str) -> str:
    """Normaliza nombre de equipo a abreviatura de 3 letras"""
    team_upper = team_input.strip().upper()
    
    # Ya es abreviatura
    if len(team_upper) == 3 and team_upper in ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 
                                                  'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND',
                                                  'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN',
                                                  'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHX',
                                                  'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS']:
        return team_upper
    
    # Mapeo de nombres a abreviaturas
    name_map = {
        'LAKERS': 'LAL', 'WARRIORS': 'GSW', 'CELTICS': 'BOS', 'HEAT': 'MIA',
        'BUCKS': 'MIL', 'SIXERS': 'PHI', '76ERS': 'PHI', 'NETS': 'BKN',
        'CLIPPERS': 'LAC', 'SUNS': 'PHX', 'MAVERICKS': 'DAL', 'NUGGETS': 'DEN',
        'GRIZZLIES': 'MEM', 'PELICANS': 'NOP', 'KINGS': 'SAC', 'HAWKS': 'ATL',
        'HORNETS': 'CHA', 'BULLS': 'CHI', 'CAVALIERS': 'CLE', 'PISTONS': 'DET',
        'ROCKETS': 'HOU', 'PACERS': 'IND', 'KNICKS': 'NYK', 'THUNDER': 'OKC',
        'MAGIC': 'ORL', 'BLAZERS': 'POR', 'SPURS': 'SAS', 'RAPTORS': 'TOR',
        'JAZZ': 'UTA', 'WIZARDS': 'WAS', 'TIMBERWOLVES': 'MIN'
    }
    
    if team_upper in name_map:
        return name_map[team_upper]
    
    # Buscar parcialmente
    for name, abbr in name_map.items():
        if team_upper in name or name in team_upper:
            return abbr
    
    raise ValueError(f"Equipo no reconocido: {team_input}")


# ==================== RUTAS ====================

@app.route('/api/register', methods=['POST'])
def register():
    """POST /api/register - Registrar usuario"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'El usuario ya existe'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ Usuario registrado: {username}")
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en register: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error al registrar: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """POST /api/login - Autenticación con JWT"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        access_token = create_access_token(identity=str(user.id))
        
        print(f"✅ Login exitoso: {username}")
        
        return jsonify({
            'message': 'Login exitoso',
            'token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error en login: {str(e)}'}), 500


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    """GET /api/profile - Perfil protegido por token"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        predictions = Prediction.query.filter_by(user_id=user_id)\
            .order_by(Prediction.created_at.desc())\
            .limit(10)\
            .all()
        
        return jsonify({
            'user': user.to_dict(),
            'total_predictions': len(user.predictions),
            'recent_predictions': [p.to_dict() for p in predictions]
        }), 200
        
    except Exception as e:
        print(f"❌ ERROR in /api/profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error: {str(e)}'}), 500


@app.route('/api/analyze-text', methods=['POST'])
@jwt_required()
def analyze_text():
    """POST /api/analyze-text - Análisis con IA usando APIS REALES"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        text = data.get('text', '')
        home_team = data.get('homeTeam') or data.get('home_team')
        away_team = data.get('awayTeam') or data.get('away_team')
        
        # Parsear texto si viene en formato "LAL vs GSW"
        if text and not (home_team and away_team):
            parts = text.upper().replace(' ', '').split('VS')
            if len(parts) == 2:
                home_team = parts[0].strip()
                away_team = parts[1].strip()
        
        if not home_team or not away_team:
            return jsonify({'error': 'Formato: "LAL vs GSW" o "Lakers vs Warriors"'}), 400
        
        print(f"\n{'='*60}")
        print(f"🏀 NUEVA PREDICCIÓN")
        print(f"{'='*60}")
        print(f"Usuario: {user_id}")
        print(f"Partido: {home_team} vs {away_team}")
        
        # Normalizar nombres de equipos
        try:
            home_abbr = normalize_team_name(home_team)
            away_abbr = normalize_team_name(away_team)
            print(f"✅ Equipos normalizados: {home_abbr} vs {away_abbr}")
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # ✅ OBTENER FEATURES REALES DESDE APIs
        print(f"\n📡 Consultando APIs para obtener stats reales...")
        features = nba_client.get_matchup_features(home_abbr, away_abbr)
        
        # Log de features obtenidas
        print(f"\n📊 FEATURES OBTENIDAS:")
        print(f"   {home_abbr}:")
        print(f"      ELO: {features['home']['elo']}")
        print(f"      PPG: {features['home']['stats']['points_per_game']}")
        print(f"      Record: {features['home']['stats']['wins']}-{features['home']['stats']['losses']}")
        print(f"   {away_abbr}:")
        print(f"      ELO: {features['away']['elo']}")
        print(f"      PPG: {features['away']['stats']['points_per_game']}")
        print(f"      Record: {features['away']['stats']['wins']}-{features['away']['stats']['losses']}")
        print(f"   Source: {features['metadata']['source']}")
        
        # Llamar al servicio ML
        print(f"\n📡 Enviando a ML Service...")
        
        try:
            ml_response = requests.post(
                f'{ML_SERVICE_URL}/predict',
                json=features,
                timeout=30
            )
            
            if ml_response.status_code != 200:
                print(f"❌ ML Service error: {ml_response.status_code}")
                return jsonify({'error': 'Error en modelo ML'}), 500
            
            prediction_data = ml_response.json()
            
            print(f"\n✅ PREDICCIÓN DEL MODELO:")
            print(f"   Ganador: {prediction_data['predicted_winner']}")
            print(f"   Confianza: {prediction_data['confidence']:.2%}")
            print(f"   Prob. Home: {prediction_data['home_win_probability']:.2%}")
            print(f"   Prob. Away: {prediction_data['away_win_probability']:.2%}")
            
        except requests.exceptions.ConnectionError:
            print("❌ No se pudo conectar al servicio ML")
            return jsonify({'error': 'Servicio ML no disponible'}), 503
        
        # Guardar en DB
        prediction = Prediction(
            user_id=user_id,
            home_team=home_abbr,
            away_team=away_abbr,
            predicted_winner=prediction_data['predicted_winner'],
            confidence=prediction_data['confidence'],
            home_win_prob=prediction_data['home_win_probability'],
            away_win_prob=prediction_data['away_win_probability']
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        print(f"\n✅ Predicción guardada: ID={prediction.id}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'matchup': f'{home_abbr} vs {away_abbr}',
            'prediction': {
                'winner': prediction_data['predicted_winner'],
                'confidence': round(prediction_data['confidence'] * 100, 2),
                'home_win_probability': round(prediction_data['home_win_probability'] * 100, 2),
                'away_win_probability': round(prediction_data['away_win_probability'] * 100, 2)
            },
            'id': prediction.id,
            'stats_source': features['metadata']['source']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en analyze_text: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions/history', methods=['GET'])
@jwt_required()
def prediction_history():
    """GET /api/predictions/history - Historial"""
    try:
        user_id = int(get_jwt_identity())
        
        predictions = Prediction.query.filter_by(user_id=user_id)\
            .order_by(Prediction.created_at.desc())\
            .all()
        
        return jsonify({
            'total': len(predictions),
            'predictions': [p.to_dict() for p in predictions]
        }), 200
        
    except Exception as e:
        print(f"❌ Error en history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upcoming-games', methods=['GET'])
@jwt_required()
def upcoming_games():
    """GET /api/upcoming-games - Partidos próximos desde APIs"""
    try:
        games = nba_client.get_upcoming_games_odds_api()
        
        return jsonify({
            'total': len(games),
            'games': games
        }), 200
        
    except Exception as e:
        print(f"❌ Error obteniendo partidos: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'ml_service': ML_SERVICE_URL,
        'nba_apis': 'connected'
    }), 200


# ==================== INICIALIZACIÓN ====================

with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏀 APUESTA IA - Backend Flask + MySQL + JWT + APIs REALES")
    print("="*60)
    print(f"🔗 ML Service: {ML_SERVICE_URL}")
    print(f"📡 NBA APIs: RapidAPI + The Odds API")
    print(f"💾 MySQL Database conectada")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)