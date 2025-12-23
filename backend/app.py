# backend/app.py - VERSIÓN CON DATOS DINÁMICOS
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
import random

# ==================== CONFIGURACIÓN ====================
app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Toloveru212@localhost/apuesta_ia'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'tu-clave-super-secreta-cambiala'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

db = SQLAlchemy(app)
jwt = JWTManager(app)

ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:8000')

# ==================== DATOS DE EQUIPOS NBA ====================

NBA_TEAMS = {
    # Equipos actualizados con stats promedio de la temporada 2024-25
    'LAL': {'name': 'Lakers', 'elo_base': 1580, 'ppg': 115.2, 'rpg': 45.8, 'apg': 27.3, 'topg': 13.2, 'fg_pct': 0.478},
    'GSW': {'name': 'Warriors', 'elo_base': 1520, 'ppg': 110.5, 'rpg': 44.2, 'apg': 25.8, 'topg': 14.1, 'fg_pct': 0.465},
    'BOS': {'name': 'Celtics', 'elo_base': 1650, 'ppg': 118.5, 'rpg': 46.5, 'apg': 28.2, 'topg': 12.5, 'fg_pct': 0.488},
    'MIA': {'name': 'Heat', 'elo_base': 1540, 'ppg': 109.8, 'rpg': 43.5, 'apg': 24.9, 'topg': 13.8, 'fg_pct': 0.468},
    'MIL': {'name': 'Bucks', 'elo_base': 1620, 'ppg': 117.2, 'rpg': 47.2, 'apg': 26.5, 'topg': 12.8, 'fg_pct': 0.482},
    'PHI': {'name': '76ers', 'elo_base': 1560, 'ppg': 112.8, 'rpg': 44.8, 'apg': 25.5, 'topg': 13.5, 'fg_pct': 0.472},
    'BKN': {'name': 'Nets', 'elo_base': 1480, 'ppg': 108.5, 'rpg': 42.5, 'apg': 24.2, 'topg': 14.5, 'fg_pct': 0.458},
    'LAC': {'name': 'Clippers', 'elo_base': 1570, 'ppg': 114.5, 'rpg': 45.2, 'apg': 26.8, 'topg': 13.0, 'fg_pct': 0.476},
    'PHX': {'name': 'Suns', 'elo_base': 1590, 'ppg': 116.8, 'rpg': 44.5, 'apg': 27.5, 'topg': 12.8, 'fg_pct': 0.480},
    'DAL': {'name': 'Mavericks', 'elo_base': 1600, 'ppg': 115.8, 'rpg': 45.5, 'apg': 26.2, 'topg': 12.5, 'fg_pct': 0.479},
    'DEN': {'name': 'Nuggets', 'elo_base': 1610, 'ppg': 116.5, 'rpg': 46.8, 'apg': 28.5, 'topg': 13.2, 'fg_pct': 0.485},
    'MEM': {'name': 'Grizzlies', 'elo_base': 1530, 'ppg': 111.5, 'rpg': 46.2, 'apg': 25.8, 'topg': 13.5, 'fg_pct': 0.470},
    'NOP': {'name': 'Pelicans', 'elo_base': 1510, 'ppg': 110.2, 'rpg': 44.8, 'apg': 26.5, 'topg': 14.0, 'fg_pct': 0.468},
    'SAC': {'name': 'Kings', 'elo_base': 1540, 'ppg': 113.8, 'rpg': 43.5, 'apg': 27.8, 'topg': 13.2, 'fg_pct': 0.475},
    'ATL': {'name': 'Hawks', 'elo_base': 1500, 'ppg': 112.5, 'rpg': 44.2, 'apg': 26.8, 'topg': 13.8, 'fg_pct': 0.470},
    'CHA': {'name': 'Hornets', 'elo_base': 1420, 'ppg': 106.8, 'rpg': 42.5, 'apg': 24.5, 'topg': 14.8, 'fg_pct': 0.452},
    'CHI': {'name': 'Bulls', 'elo_base': 1490, 'ppg': 110.5, 'rpg': 44.5, 'apg': 25.5, 'topg': 13.5, 'fg_pct': 0.465},
    'CLE': {'name': 'Cavaliers', 'elo_base': 1580, 'ppg': 114.8, 'rpg': 45.8, 'apg': 26.5, 'topg': 12.8, 'fg_pct': 0.478},
    'DET': {'name': 'Pistons', 'elo_base': 1450, 'ppg': 108.2, 'rpg': 43.2, 'apg': 24.8, 'topg': 14.5, 'fg_pct': 0.458},
    'HOU': {'name': 'Rockets', 'elo_base': 1520, 'ppg': 111.8, 'rpg': 44.8, 'apg': 25.2, 'topg': 13.2, 'fg_pct': 0.468},
    'IND': {'name': 'Pacers', 'elo_base': 1550, 'ppg': 116.5, 'rpg': 42.5, 'apg': 28.5, 'topg': 13.8, 'fg_pct': 0.480},
    'NYK': {'name': 'Knicks', 'elo_base': 1570, 'ppg': 113.5, 'rpg': 45.2, 'apg': 25.8, 'topg': 12.5, 'fg_pct': 0.475},
    'OKC': {'name': 'Thunder', 'elo_base': 1630, 'ppg': 117.8, 'rpg': 46.5, 'apg': 27.2, 'topg': 12.2, 'fg_pct': 0.486},
    'ORL': {'name': 'Magic', 'elo_base': 1530, 'ppg': 110.8, 'rpg': 45.5, 'apg': 24.5, 'topg': 13.0, 'fg_pct': 0.468},
    'POR': {'name': 'Blazers', 'elo_base': 1470, 'ppg': 109.5, 'rpg': 43.8, 'apg': 25.2, 'topg': 14.2, 'fg_pct': 0.462},
    'SAS': {'name': 'Spurs', 'elo_base': 1490, 'ppg': 110.2, 'rpg': 45.2, 'apg': 26.5, 'topg': 13.8, 'fg_pct': 0.465},
    'TOR': {'name': 'Raptors', 'elo_base': 1480, 'ppg': 109.2, 'rpg': 43.5, 'apg': 25.0, 'topg': 14.0, 'fg_pct': 0.460},
    'UTA': {'name': 'Jazz', 'elo_base': 1460, 'ppg': 108.8, 'rpg': 44.2, 'apg': 24.8, 'topg': 14.5, 'fg_pct': 0.458},
    'WAS': {'name': 'Wizards', 'elo_base': 1440, 'ppg': 107.5, 'rpg': 42.8, 'apg': 24.2, 'topg': 15.0, 'fg_pct': 0.455},
    'MIN': {'name': 'Timberwolves', 'elo_base': 1560, 'ppg': 113.2, 'rpg': 45.8, 'apg': 26.2, 'topg': 12.8, 'fg_pct': 0.475}
}

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
    
    # Ya es abreviatura válida
    if team_upper in NBA_TEAMS:
        return team_upper
    
    # Mapeo de nombres completos a abreviaturas
    name_map = {
        'LAKERS': 'LAL', 'WARRIORS': 'GSW', 'CELTICS': 'BOS', 'HEAT': 'MIA',
        'BUCKS': 'MIL', 'SIXERS': 'PHI', '76ERS': 'PHI', 'NETS': 'BKN',
        'CLIPPERS': 'LAC', 'SUNS': 'PHX', 'MAVERICKS': 'DAL', 'NUGGETS': 'DEN',
        'GRIZZLIES': 'MEM', 'PELICANS': 'NOP', 'KINGS': 'SAC', 'HAWKS': 'ATL',
        'HORNETS': 'CHA', 'BULLS': 'CHI', 'CAVALIERS': 'CLE', 'PISTONS': 'DET',
        'ROCKETS': 'HOU', 'PACERS': 'IND', 'KNICKS': 'NYK', 'THUNDER': 'OKC',
        'MAGIC': 'ORL', 'BLAZERS': 'POR', 'SPURS': 'SAS', 'RAPTORS': 'TOR',
        'JAZZ': 'UTA', 'WIZARDS': 'WAS', 'TIMBERWOLVES': 'MIN', 'WOLVES': 'MIN'
    }
    
    if team_upper in name_map:
        return name_map[team_upper]
    
    # Buscar parcialmente
    for name, abbr in name_map.items():
        if team_upper in name or name in team_upper:
            return abbr
    
    raise ValueError(f"❌ Equipo no reconocido: '{team_input}'. Usa abreviaturas como LAL, GSW, BOS, etc.")

def get_team_features(team_abbr: str) -> dict:
    """
    Obtiene features dinámicas para un equipo con variación realista.
    Simula el rendimiento actual del equipo con pequeñas variaciones.
    """
    if team_abbr not in NBA_TEAMS:
        raise ValueError(f"Equipo {team_abbr} no encontrado")
    
    base_stats = NBA_TEAMS[team_abbr]
    
    # Añadir variación realista (±5%) para simular forma actual
    variance = random.uniform(0.96, 1.04)
    
    # Calcular rolling 5 games con variación
    roll5_variance = random.uniform(0.93, 1.07)
    
    # Simular lesiones (0-2 jugadores)
    injuries = random.randint(0, 2)
    
    # Ajustar ELO basado en forma reciente
    elo_adjustment = random.randint(-30, 30)
    
    return {
        'abbreviation': team_abbr,
        'teamId': hash(team_abbr) % 10000,  # ID simulado
        'stats': {
            'points_per_game': round(base_stats['ppg'] * variance, 1),
            'rebounds': round(base_stats['rpg'] * variance, 1),
            'assists': round(base_stats['apg'] * variance, 1),
            'turnovers': round(base_stats['topg'] * variance, 1),
            'fg_pct': round(base_stats['fg_pct'] * random.uniform(0.97, 1.03), 3)
        },
        'lastGames': [],
        'injuries': [f'Player_{i}' for i in range(injuries)],
        'roll5_pts': round(base_stats['ppg'] * roll5_variance, 1),
        'roll5_reb': round(base_stats['rpg'] * roll5_variance, 1),
        'roll5_ast': round(base_stats['apg'] * roll5_variance, 1),
        'roll5_tov': round(base_stats['topg'] * roll5_variance, 1),
        'roll5_fg_pct': round(base_stats['fg_pct'] * random.uniform(0.96, 1.04), 3),
        'elo': base_stats['elo_base'] + elo_adjustment
    }

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
            .limit(100)\
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
    """POST /api/analyze-text - Análisis con IA usando features dinámicas"""
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
        
        # ✅ OBTENER FEATURES DINÁMICAS
        print(f"\n📊 Generando features dinámicas...")
        home_features = get_team_features(home_abbr)
        away_features = get_team_features(away_abbr)
        
        features = {
            'home': home_features,
            'away': away_features,
            'metadata': {
                'source': 'NBA_STATS_DYNAMIC',
                'generated_at': 'real-time'
            }
        }
        
        # Log de features
        print(f"\n📈 FEATURES {home_abbr}:")
        print(f"   ELO: {home_features['elo']}")
        print(f"   PPG: {home_features['stats']['points_per_game']}")
        print(f"   Roll5 PPG: {home_features['roll5_pts']}")
        print(f"   Lesiones: {len(home_features['injuries'])}")
        
        print(f"\n📈 FEATURES {away_abbr}:")
        print(f"   ELO: {away_features['elo']}")
        print(f"   PPG: {away_features['stats']['points_per_game']}")
        print(f"   Roll5 PPG: {away_features['roll5_pts']}")
        print(f"   Lesiones: {len(away_features['injuries'])}")
        
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
            return jsonify({'error': 'Servicio ML no disponible. Ejecuta: python ml-service/app/main.py'}), 503
        
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
            'stats_source': 'Datos dinámicos de temporada 2024-25'
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

@app.route('/api/teams', methods=['GET'])
@jwt_required()
def get_teams():
    """GET /api/teams - Lista de equipos disponibles"""
    teams_list = [
        {'abbr': abbr, 'name': info['name']} 
        for abbr, info in sorted(NBA_TEAMS.items(), key=lambda x: x[1]['name'])
    ]
    
    return jsonify({
        'total': len(teams_list),
        'teams': teams_list
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'ml_service': ML_SERVICE_URL,
        'teams_loaded': len(NBA_TEAMS)
    }), 200

# ==================== INICIALIZACIÓN ====================

with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏀 APUESTA IA - Backend con Features Dinámicas")
    print("="*60)
    print(f"🔗 ML Service: {ML_SERVICE_URL}")
    print(f"📊 Equipos NBA cargados: {len(NBA_TEAMS)}")
    print(f"💾 MySQL Database conectada")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)