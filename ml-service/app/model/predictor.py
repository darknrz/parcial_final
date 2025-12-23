# ml-service/app/model/predictor.py
import os
import joblib
import numpy as np
import pandas as pd
from model.feature_engineer import FeatureEngineer

MODEL_PATH = os.path.join("models", "nba_xgb_model.pkl")

class Predictor:
    """
    Clase para realizar predicciones con el modelo entrenado
    """
    
    def __init__(self):
        """Carga el modelo entrenado"""
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f" Modelo no encontrado en {MODEL_PATH}. "
                "Entrena un modelo primero con POST /train"
            )
        
        self.model = joblib.load(MODEL_PATH)
        self.engineer = FeatureEngineer()
        
        print(f" Modelo cargado desde {MODEL_PATH}")
    
    def predict(self, game_data):
        """
        Predice el ganador de un partido
        
        Args:
            game_data: Dict con estructura:
                {
                    'home': {
                        'abbreviation': 'LAL',
                        'teamId': 1610612747,
                        'stats': {...},
                        'roll5_pts': 112.5,
                        'roll5_reb': 45.0,
                        'roll5_ast': 26.0,
                        'elo': 1580,
                        'injuries': [...]
                    },
                    'away': {
                        'abbreviation': 'GSW',
                        'teamId': 1610612744,
                        'stats': {...},
                        'roll5_pts': 108.5,
                        'roll5_reb': 43.0,
                        'roll5_ast': 24.0,
                        'elo': 1520,
                        'injuries': [...]
                    }
                }
        
        Returns:
            Dict con predicción:
                {
                    'predicted_winner': 'LAL',
                    'home_win_probability': 0.65,
                    'away_win_probability': 0.35,
                    'confidence': 0.65
                }
        """
        try:
            print(f"\n Prediciendo: {game_data['home']['abbreviation']} vs {game_data['away']['abbreviation']}")
            
            # 1. Construir features desde datos de APIs
            features = self.engineer.build_features_from_api(
                game_data['home'], 
                game_data['away']
            )
            
            # 2. Convertir a DataFrame con nombres de columnas correctos
            feature_names = self.engineer.get_feature_names()
            X = pd.DataFrame([features], columns=feature_names)
            
            print(f" Features construidos: {X.shape}")
            print(f" Valores: {features}")
            
            # 3. Predecir
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            # prediction = 1 significa que gana el equipo local (home)
            # prediction = 0 significa que gana el equipo visitante (away)
            
            home_win_prob = float(probabilities[1])
            away_win_prob = float(probabilities[0])
            
            predicted_winner = game_data['home']['abbreviation'] if prediction == 1 else game_data['away']['abbreviation']
            confidence = max(home_win_prob, away_win_prob)
            
            result = {
                'predicted_winner': predicted_winner,
                'home_win_probability': home_win_prob,
                'away_win_probability': away_win_prob,
                'confidence': confidence
            }
            
            print(f" Predicción: {predicted_winner} (Confianza: {confidence:.2%})")
            
            return result
            
        except Exception as e:
            print(f" Error en predicción: {e}")
            raise Exception(f"Error en predicción: {e}")
    
    def predict_batch(self, games_data):
        """
        Predice múltiples partidos
        
        Args:
            games_data: Lista de dicts con estructura game_data
        
        Returns:
            Lista de predicciones
        """
        predictions = []
        
        for game in games_data:
            try:
                pred = self.predict(game)
                predictions.append(pred)
            except Exception as e:
                print(f" Error prediciendo {game.get('home', {}).get('abbreviation')} vs {game.get('away', {}).get('abbreviation')}: {e}")
                predictions.append({
                    'error': str(e),
                    'predicted_winner': None,
                    'home_win_probability': None,
                    'away_win_probability': None,
                    'confidence': None
                })
        
        return predictions