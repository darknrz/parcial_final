# ml-service/train_model.py
"""
Script para entrenar el modelo ML via API
UBICACIÓN: ml-service/train_model.py (raíz del proyecto)
"""
import requests
import json
import time

ML_API_URL = "http://localhost:8000"

def train_model():
    """Entrena el modelo enviando request a /train"""
    
    print("\n Iniciando entrenamiento del modelo...")
    print("=" * 50)
    
    payload = {
        "data_path": "data/nba_games_clean.csv",
        "test_size": 0.2
    }
    
    try:
        response = requests.post(
            f"{ML_API_URL}/train",
            json=payload,
            timeout=300  # 5 minutos timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n Entrenamiento iniciado correctamente")
            print(f" Dataset: {result.get('data_path')}")
            print(f" Test size: {result.get('test_size')}")
            print("\n El entrenamiento se está ejecutando en background...")
            print(" Puedes ver el progreso en la terminal del servidor ML")
            
            # Esperar un poco y verificar que el modelo esté listo
            print("\n Esperando 15 segundos para que termine el entrenamiento...")
            for i in range(15, 0, -1):
                print(f"   {i} segundos...", end='\r')
                time.sleep(1)
            print("\n")
            
            # Verificar health
            check_health()
            
        else:
            print(f"\n Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n Error: No se pudo conectar al servidor ML")
        print("💡 Asegúrate de que el servidor esté corriendo:")
        print("   cd ml-service/app")
        print("   python main.py")
        
    except Exception as e:
        print(f"\n Error inesperado: {e}")

def check_health():
    """Verifica el estado del servidor ML"""
    
    print("\n Verificando estado del servidor...")
    
    try:
        response = requests.get(f"{ML_API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            health = response.json()
            
            print("\n" + "=" * 50)
            print(" ESTADO DEL SERVIDOR ML")
            print("=" * 50)
            print(f" Modelo cargado: {' SÍ' if health.get('model_loaded') else '❌ NO'}")
            print(f" Ruta del modelo: {health.get('model_path')}")
            print(f" Archivo existe: {' SÍ' if health.get('model_exists') else '❌ NO'}")
            
            if health.get('model_loaded'):
                print("\n ¡TODO LISTO! El sistema está funcionando")
                print(" Ahora puedes:")
                print(f"   1. Hacer predicciones: POST {ML_API_URL}/predict")
                print(f"   2. Iniciar backend Node.js: node backend/server.js")
            else:
                print("\n  Modelo no cargado todavía")
                print(" Opciones:")
                print("   1. Espera 5-10 segundos más y vuelve a ejecutar: python train_model.py")
                print("   2. Verifica logs del servidor ML")
                print("   3. Revisa que exista: data/nba_games_clean.csv")
        else:
            print(f"❌ Error en health check: {response.status_code}")
            
    except Exception as e:
        print(f" Error verificando health: {e}")

def test_prediction():
    """Prueba una predicción de ejemplo"""
    
    print("\n Probando predicción de ejemplo...")
    print("=" * 50)
    print(" Partido: LAL (Lakers) vs GSW (Warriors)")
    
    # Datos de prueba
    test_data = {
        "home": {
            "abbreviation": "LAL",
            "teamId": 1610612747,
            "stats": {
                "games_played": 20,
                "wins": 12,
                "losses": 8,
                "points_per_game": 112.5,
                "rebounds": 45.2,
                "assists": 26.1,
                "turnovers": 13.5
            },
            "lastGames": [],
            "injuries": [],
            "roll5_pts": 115.2,
            "roll5_reb": 46.0,
            "roll5_ast": 27.5,
            "roll5_tov": 12.8,
            "roll5_fg_pct": 0.478,
            "elo": 1580
        },
        "away": {
            "abbreviation": "GSW",
            "teamId": 1610612744,
            "stats": {
                "games_played": 20,
                "wins": 10,
                "losses": 10,
                "points_per_game": 108.3,
                "rebounds": 43.5,
                "assists": 24.8,
                "turnovers": 14.2
            },
            "lastGames": [],
            "injuries": [],
            "roll5_pts": 110.5,
            "roll5_reb": 44.2,
            "roll5_ast": 25.3,
            "roll5_tov": 13.9,
            "roll5_fg_pct": 0.465,
            "elo": 1520
        }
    }
    
    try:
        response = requests.post(
            f"{ML_API_URL}/predict",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            prediction = response.json()
            
            print("\n" + "=" * 50)
            print(" PREDICCIÓN EXITOSA")
            print("=" * 50)
            print(f" Ganador predicho: {prediction['predicted_winner']}")
            print(f" Confianza: {prediction['confidence']:.1%}")
            print(f" Prob. LOCAL (LAL): {prediction['home_win_probability']:.1%}")
            print(f"  Prob. VISITANTE (GSW): {prediction['away_win_probability']:.1%}")
            
        elif response.status_code == 503:
            print("\n  Modelo no está cargado todavía")
            print(" Entrena el modelo primero")
            
        else:
            print(f"\n Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f" Error en predicción: {e}")

if __name__ == "__main__":
    print("\n NBA ML MODEL TRAINER & TESTER")
    print("=" * 50)
    print(" Ubicación: ml-service/train_model.py")
    print("=" * 50)
    
    # 1. Verificar conexión
    print("\n[1/4] Verificando conexión con servidor ML...")
    check_health()
    
    # 2. Entrenar modelo
    print("\n[2/4] Entrenando modelo...")
    train_model()
    
    # 3. Verificar de nuevo
    print("\n[3/4] Verificando que el modelo esté cargado...")
    check_health()
    
    # 4. Probar predicción
    print("\n[4/4] Probando predicción...")
    test_prediction()
    
    print("\n" + "=" * 50)
    print(" SCRIPT COMPLETADO")
    print("=" * 50)
    print("\n PRÓXIMOS PASOS:")
    print("   1. Si el modelo está cargado: cd backend && node server.js")
    print("   2. Si no está cargado: espera 10 seg y vuelve a ejecutar este script")
    print("   3. Verifica logs del servidor ML en la otra terminal")
    print("\n Para entrenar de nuevo: python train_model.py")