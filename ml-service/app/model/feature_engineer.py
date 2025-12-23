# ml-service/app/model/feature_engineer.py
import pandas as pd
import numpy as np

class FeatureEngineer:
    """
    Clase para construir features desde datos crudos
    """
    
    def __init__(self):
        pass
    
    def build_features_from_csv(self, df):
        """
        Construye features desde un DataFrame con datos históricos
        
        Args:
            df: DataFrame con columnas como:
                - home_team, away_team
                - home_pts, away_pts (o equivalentes)
                - home_reb, away_reb
                - home_ast, away_ast
                - home_tov, away_tov
                - home_elo, away_elo
                - home_injuries, away_injuries
                - home_roll5_pts, away_roll5_pts (rolling stats)
                - home_win (target: 1 si ganó local, 0 si ganó visitante)
        
        Returns:
            DataFrame con features procesados y target 'winner'
        """
        print(f"Shape original: {df.shape}")
        print(f"Columnas disponibles: {df.columns.tolist()}")
        
        # Crear features de diferencia (más importantes para ML)
        features = pd.DataFrame()
        
        # 1. Diferencias de stats básicas
        if 'point_diff' in df.columns:
            features['point_diff'] = df['point_diff']
        else:
            features['point_diff'] = df['home_pts'] - df['away_pts']
        
        if 'reb_diff' in df.columns:
            features['reb_diff'] = df['reb_diff']
        else:
            features['reb_diff'] = df['home_reb'] - df['away_reb']
        
        if 'ast_diff' in df.columns:
            features['ast_diff'] = df['ast_diff']
        else:
            features['ast_diff'] = df['home_ast'] - df['away_ast']
        
        if 'tov_diff' in df.columns:
            features['tov_diff'] = df['tov_diff']
        else:
            features['tov_diff'] = df['home_tov'] - df['away_tov']
        
        # 2. Rolling stats differences (forma reciente)
        if 'roll5_point_diff' in df.columns:
            features['roll5_point_diff'] = df['roll5_point_diff']
        else:
            features['roll5_point_diff'] = df['home_roll5_pts'] - df['away_roll5_pts']
        
        if 'roll5_reb_diff' in df.columns:
            features['roll5_reb_diff'] = df['roll5_reb_diff']
        else:
            features['roll5_reb_diff'] = df['home_roll5_reb'] - df['away_roll5_reb']
        
        if 'roll5_ast_diff' in df.columns:
            features['roll5_ast_diff'] = df['roll5_ast_diff']
        else:
            features['roll5_ast_diff'] = df['home_roll5_ast'] - df['away_roll5_ast']
        
        # 3. Home advantage
        if 'home_advantage' in df.columns:
            features['home_advantage'] = df['home_advantage']
        else:
            features['home_advantage'] = 1  # Siempre 1 (es el equipo local)
        
        # 4. Elo rating difference
        if 'elo_diff' in df.columns:
            features['elo_diff'] = df['elo_diff']
        else:
            features['elo_diff'] = df['home_elo'] - df['away_elo']
        
        # 5. Injury difference
        if 'injury_diff' in df.columns:
            features['injury_diff'] = df['injury_diff']
        else:
            features['injury_diff'] = df['away_injuries'] - df['home_injuries']
        
        # 6. Target: home_win
        features['winner'] = df['home_win']
        
        # Eliminar NaN si existen
        features = features.fillna(0)
        
        print(f" Features construidos: {features.shape}")
        print(f" Features: {features.columns.tolist()}")
        
        return features
    
    def build_features_from_api(self, home_data, away_data):
        """
        Construye features desde datos en tiempo real de las APIs
        
        Args:
            home_data: Dict con stats del equipo local
                {
                    'abbreviation': 'LAL',
                    'stats': {...},
                    'roll5_pts': 112.5,
                    'roll5_reb': 45.0,
                    'roll5_ast': 26.0,
                    'elo': 1580,
                    'injuries': [...]
                }
            away_data: Dict con stats del equipo visitante (misma estructura)
        
        Returns:
            Array con features en el orden correcto para predicción
        """
        # Extraer stats
        home_stats = home_data.get('stats', {})
        away_stats = away_data.get('stats', {})
        
        # 1. Diferencia de puntos (aproximada por PPG de temporada)
        point_diff = home_stats.get('points_per_game', 0) - away_stats.get('points_per_game', 0)
        
        # 2. Diferencia de rebotes
        reb_diff = home_stats.get('rebounds', 0) - away_stats.get('rebounds', 0)
        
        # 3. Diferencia de asistencias
        ast_diff = home_stats.get('assists', 0) - away_stats.get('assists', 0)
        
        # 4. Diferencia de pérdidas
        tov_diff = home_stats.get('turnovers', 0) - away_stats.get('turnovers', 0)
        
        # 5. Rolling stats differences (últimos 5 juegos)
        roll5_point_diff = home_data.get('roll5_pts', 0) - away_data.get('roll5_pts', 0)
        roll5_reb_diff = home_data.get('roll5_reb', 0) - away_data.get('roll5_reb', 0)
        roll5_ast_diff = home_data.get('roll5_ast', 0) - away_data.get('roll5_ast', 0)
        
        # 6. Home advantage (siempre 1 para el equipo local)
        home_advantage = 1
        
        # 7. Elo rating difference
        elo_diff = home_data.get('elo', 1500) - away_data.get('elo', 1500)
        
        # 8. Injury difference (más lesiones en visitante favorece al local)
        injury_diff = len(away_data.get('injuries', [])) - len(home_data.get('injuries', []))
        
        # Crear array en el orden correcto
        features = [
            point_diff,
            reb_diff,
            ast_diff,
            tov_diff,
            roll5_point_diff,
            roll5_reb_diff,
            roll5_ast_diff,
            home_advantage,
            elo_diff,
            injury_diff
        ]
        
        return features
    
    def get_feature_names(self):
        """Retorna los nombres de las features en orden"""
        return [
            'point_diff',
            'reb_diff',
            'ast_diff',
            'tov_diff',
            'roll5_point_diff',
            'roll5_reb_diff',
            'roll5_ast_diff',
            'home_advantage',
            'elo_diff',
            'injury_diff'
        ]