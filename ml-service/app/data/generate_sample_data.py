# ml-service/generate_sample_data.py
"""
Genera datos sintéticos de NBA para entrenar el modelo
SOLO PARA TESTING - En producción usa datos reales
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Equipos NBA (30 equipos)
teams = [
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GS",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NO", "NY",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SA", "TOR", "UTA", "WAS"
]

def generate_game_data(num_games=1000):
    """Genera datos sintéticos de partidos NBA"""
    
    np.random.seed(42)
    games = []
    
    start_date = datetime(2023, 10, 1)
    
    for i in range(num_games):
        # Seleccionar equipos random
        home_team = np.random.choice(teams)
        away_team = np.random.choice([t for t in teams if t != home_team])
        
        # Stats del equipo local (con ventaja de local)
        home_pts = np.random.normal(110, 12)
        home_reb = np.random.normal(45, 5)
        home_ast = np.random.normal(25, 4)
        home_tov = np.random.normal(13, 3)
        home_fg_pct = np.random.normal(0.46, 0.04)
        home_elo = np.random.normal(1520, 80)  # Ventaja local
        
        # Stats del equipo visitante
        away_pts = np.random.normal(107, 12)
        away_reb = np.random.normal(44, 5)
        away_ast = np.random.normal(24, 4)
        away_tov = np.random.normal(13, 3)
        away_fg_pct = np.random.normal(0.45, 0.04)
        away_elo = np.random.normal(1480, 80)  # Sin ventaja
        
        # Lesiones (random 0-3 por equipo)
        home_injuries = np.random.randint(0, 4)
        away_injuries = np.random.randint(0, 4)
        
        # Rolling stats (últimos 5 juegos)
        home_roll5_pts = np.random.normal(110, 8)
        home_roll5_reb = np.random.normal(45, 3)
        home_roll5_ast = np.random.normal(25, 3)
        
        away_roll5_pts = np.random.normal(107, 8)
        away_roll5_reb = np.random.normal(44, 3)
        away_roll5_ast = np.random.normal(24, 3)
        
        # Calcular diferencias (features principales)
        point_diff = home_pts - away_pts
        reb_diff = home_reb - away_reb
        ast_diff = home_ast - away_ast
        tov_diff = home_tov - away_tov
        elo_diff = home_elo - away_elo
        injury_diff = away_injuries - home_injuries
        roll5_point_diff = home_roll5_pts - away_roll5_pts
        roll5_reb_diff = home_roll5_reb - away_roll5_reb
        roll5_ast_diff = home_roll5_ast - away_roll5_ast
        
        # Ventaja de local (1 = local, 0 = visitante)
        home_advantage = 1
        
        # Determinar ganador (home_win: 1 si ganó local, 0 si ganó visitante)
        # Basado en point_diff + algo de randomness
        prob_home_win = 1 / (1 + np.exp(-0.1 * (point_diff + np.random.normal(0, 3))))
        home_win = 1 if np.random.random() < prob_home_win else 0
        
        # Fecha del partido
        game_date = start_date + timedelta(days=i % 180)
        
        games.append({
            'game_date': game_date.strftime('%Y-%m-%d'),
            'home_team': home_team,
            'away_team': away_team,
            'home_pts': round(home_pts, 1),
            'away_pts': round(away_pts, 1),
            'home_reb': round(home_reb, 1),
            'away_reb': round(away_reb, 1),
            'home_ast': round(home_ast, 1),
            'away_ast': round(away_ast, 1),
            'home_tov': round(home_tov, 1),
            'away_tov': round(away_tov, 1),
            'home_fg_pct': round(home_fg_pct, 3),
            'away_fg_pct': round(away_fg_pct, 3),
            'home_elo': round(home_elo, 1),
            'away_elo': round(away_elo, 1),
            'home_injuries': home_injuries,
            'away_injuries': away_injuries,
            'home_roll5_pts': round(home_roll5_pts, 1),
            'away_roll5_pts': round(away_roll5_pts, 1),
            'home_roll5_reb': round(home_roll5_reb, 1),
            'away_roll5_reb': round(away_roll5_reb, 1),
            'home_roll5_ast': round(home_roll5_ast, 1),
            'away_roll5_ast': round(away_roll5_ast, 1),
            # Features calculados
            'point_diff': round(point_diff, 1),
            'reb_diff': round(reb_diff, 1),
            'ast_diff': round(ast_diff, 1),
            'tov_diff': round(tov_diff, 1),
            'elo_diff': round(elo_diff, 1),
            'injury_diff': injury_diff,
            'roll5_point_diff': round(roll5_point_diff, 1),
            'roll5_reb_diff': round(roll5_reb_diff, 1),
            'roll5_ast_diff': round(roll5_ast_diff, 1),
            'home_advantage': home_advantage,
            # Target
            'home_win': home_win
        })
    
    return pd.DataFrame(games)

if __name__ == "__main__":
    print("🏀 Generando datos sintéticos de NBA...")
    print("=" * 50)
    
    # Generar 2000 partidos sintéticos
    df = generate_game_data(num_games=2000)
    
    # Crear carpeta data si no existe
    import os
    os.makedirs("data", exist_ok=True)
    
    # Guardar CSV
    output_path = "data/nba_games_clean.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Datos generados exitosamente")
    print(f"📊 Total de partidos: {len(df)}")
    print(f"📂 Archivo: {output_path}")
    print(f"🏆 Victorias locales: {df['home_win'].sum()} ({df['home_win'].mean()*100:.1f}%)")
    print(f"✈️  Victorias visitantes: {(1-df['home_win']).sum()} ({(1-df['home_win']).mean()*100:.1f}%)")
    print("\n📋 Columnas del dataset:")
    print(df.columns.tolist())
    print("\n👀 Primeras 3 filas:")
    print(df.head(3))
    print("\n" + "=" * 50)
    print("🎯 Ahora ejecuta: python main.py")
    print("📡 Luego entrena el modelo: POST http://localhost:8000/train")