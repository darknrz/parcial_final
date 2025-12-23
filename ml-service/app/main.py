# ml-service/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from typing import Optional
from model.predictor import Predictor
from model.trainer import Trainer

app = FastAPI(
    title="NBA ML Prediction Service",
    description="Servicio de Machine Learning para predicciones NBA",
    version="1.0.0"
)

# CORS para permitir requests desde el backend Node.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor instance
predictor = None
MODEL_PATH = os.path.join("models", "nba_xgb_model.pkl")

# ==================== MODELS ====================

class TeamFeatures(BaseModel):
    abbreviation: str
    teamId: int
    stats: dict
    lastGames: list
    injuries: list
    roll5_pts: float = 0
    roll5_reb: float = 0
    roll5_ast: float = 0
    roll5_tov: float = 0
    roll5_fg_pct: float = 0
    elo: float = 1500

class PredictRequest(BaseModel):
    home: TeamFeatures
    away: TeamFeatures
    metadata: Optional[dict] = {}

class PredictResponse(BaseModel):
    predicted_winner: str
    home_win_probability: float
    away_win_probability: float
    confidence: float

class TrainRequest(BaseModel):
    data_path: str = "data/nba_games_clean.csv"
    test_size: float = 0.2

# ==================== STARTUP ====================

@app.on_event("startup")
def startup_event():
    """Cargar modelo al iniciar el servidor"""
    global predictor
    
    print("\n" + "="*50)
    print(" Iniciando NBA ML Prediction Service...")
    print("="*50 + "\n")
    
    if os.path.exists(MODEL_PATH):
        try:
            predictor = Predictor()
            print(" Predictor XGBoost cargado correctamente")
            print(f" Modelo: {MODEL_PATH}\n")
        except Exception as e:
            print(f"  Error cargando predictor: {e}")
            print(" Entrena un modelo primero con POST /train\n")
    else:
        print("  Modelo no encontrado")
        print(f" Esperado en: {MODEL_PATH}")
        print(" Entrena un modelo primero con POST /train\n")

# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "NBA ML Prediction Service",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": predictor is not None,
        "endpoints": {
            "health": "/health",
            "predict": "POST /predict",
            "train": "POST /train"
        }
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": predictor is not None,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH)
    }

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """
    Predice el ganador de un partido NBA
    
    - **home**: Features del equipo local
    - **away**: Features del equipo visitante
    - **metadata**: Información adicional del partido (opcional)
    
    Returns:
    - predicted_winner: Abreviación del equipo ganador predicho
    - home_win_probability: Probabilidad de victoria local (0-1)
    - away_win_probability: Probabilidad de victoria visitante (0-1)
    - confidence: Nivel de confianza de la predicción (0-1)
    """
    global predictor
    
    if predictor is None:
        raise HTTPException(
            status_code=503, 
            detail="Modelo no cargado. Entrena un modelo primero con POST /train"
        )
    
    try:
        print(f"\n Prediciendo: {req.home.abbreviation} vs {req.away.abbreviation}")
        
        # Convertir request a dict para el predictor
        features_dict = req.dict()
        
        # Realizar predicción
        prediction = predictor.predict(features_dict)
        
        print(f" Predicción: {prediction['predicted_winner']} "
              f"(Confianza: {prediction['confidence']:.2%})\n")
        
        return prediction
        
    except Exception as e:
        print(f" Error en predicción: {e}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando predicción: {str(e)}"
        )

@app.post("/train")
def train(background_tasks: BackgroundTasks, req: TrainRequest = None):
    """
    Entrena un nuevo modelo con datos históricos
    
    - **data_path**: Ruta al CSV con datos históricos (default: data/nba_games_clean.csv)
    - **test_size**: Proporción de datos para validación (default: 0.2)
    
    El entrenamiento se ejecuta en background y el modelo se recarga automáticamente.
    """
    data_path = req.data_path if req else "data/nba_games_clean.csv"
    test_size = req.test_size if req else 0.2
    
    if not os.path.exists(data_path):
        raise HTTPException(
            status_code=404,
            detail=f"Archivo de datos no encontrado: {data_path}"
        )
    
    def run_training():
        """Función que se ejecuta en background"""
        global predictor
        
        print("\n" + "="*50)
        print(" INICIANDO ENTRENAMIENTO")
        print("="*50)
        print(f" Dataset: {data_path}")
        print(f" Test size: {test_size}")
        print()
        
        try:
            trainer = Trainer(data_csv=data_path)
            trainer.train(test_size=test_size)
            
            # Recargar predictor con nuevo modelo
            predictor = Predictor()
            
            print("\n" + "="*50)
            print(" ENTRENAMIENTO COMPLETADO")
            print(" Predictor recargado con nuevo modelo")
            print("="*50 + "\n")
            
        except Exception as e:
            print("\n" + "="*50)
            print(f"❌ ERROR EN ENTRENAMIENTO: {e}")
            print("="*50 + "\n")
    
    # Ejecutar en background
    background_tasks.add_task(run_training)
    
    return {
        "status": "training_started",
        "message": "El entrenamiento se está ejecutando en background",
        "data_path": data_path,
        "test_size": test_size
    }

@app.get("/model/info")
def model_info():
    """Información sobre el modelo actual"""
    if predictor is None:
        return {
            "model_loaded": False,
            "message": "No hay modelo cargado"
        }
    
    return {
        "model_loaded": True,
        "model_path": MODEL_PATH,
        "model_type": "XGBoost Classifier",
        "features": [
            "point_diff", "reb_diff", "ast_diff", "tov_diff",
            "roll5_point_diff", "roll5_reb_diff", "roll5_ast_diff",
            "home_advantage", "elo_diff", "injury_diff"
        ]
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n NBA ML Prediction Service")
    print("="*50)
    
    # Puerto configurable via environment variable
    port = int(os.getenv("ML_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Hot reload en desarrollo
        log_level="info"
    )