# ml-service/fetch_nba_official_api.py
"""
Descarga datos REALES de NBA usando la API OFICIAL (100% GRATIS, sin API keys)
UBICACIÓN: ml-service/fetch_nba_official_api.py
"""
import pandas as pd
import requests
import time
from datetime import datetime
import os

# API oficial de NBA Stats (NO REQUIERE API KEY)
NBA_STATS_BASE = "https://stats.nba.com/stats"

# Headers para simular navegador (requerido por NBA.com)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive',
}

# Mapeo de abreviaturas a IDs oficiales
TEAM_IDS = {
    'ATL': 1610612737, 'BOS': 1610612738, 'BKN': 1610612751, 'CHA': 1610612766,
    'CHI': 1610612741, 'CLE': 1610612739, 'DAL': 1610612742, 'DEN': 1610612743,
    'DET': 1610612765, 'GSW': 1610612744, 'HOU': 1610612745, 'IND': 1610612754,
    'LAC': 1610612746, 'LAL': 1610612747, 'MEM': 1610612763, 'MIA': 1610612748,
    'MIL': 1610612749, 'MIN': 1610612750, 'NOP': 1610612740, 'NYK': 1610612752,
    'OKC': 1610612760, 'ORL': 1610612753, 'PHI': 1610612755, 'PHX': 1610612756,
    'POR': 1610612757, 'SAC': 1610612758, 'SAS': 1610612759, 'TOR': 1610612761,
    'UTA': 1610612762, 'WAS': 1610612764
}

# Reverso (ID a abreviatura)
ID_TO_TEAM = {v: k for k, v in TEAM_IDS.items()}


def fetch_season_games(season="2024-25", max_games=500):
    """
    Descarga partidos de la temporada desde la API oficial de NBA
    
    Args:
        season: Temporada (ej: "2024-25")
        max_games: Máximo de partidos a descargar
    
    Returns:
        DataFrame con partidos
    """
    print(f"\n🏀 Descargando partidos de la temporada {season}")
    print("="*60)
    
    # Endpoint de scoreboard por fecha
    url = f"{NBA_STATS_BASE}/leaguegamelog"
    
    params = {
        'Season': season,
        'SeasonType': 'Regular Season',
        'LeagueID': '00',  # NBA
        'Direction': 'DESC',
        'Sorter': 'DATE',
        'Counter': 0
    }
    
    try:
        print("📡 Consultando NBA Stats API (oficial, sin API key)...")
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parsear respuesta
            headers = data['resultSets'][0]['headers']
            rows = data['resultSets'][0]['rowSet']
            
            if not rows:
                print("❌ No hay datos disponibles")
                return pd.DataFrame()
            
            df = pd.DataFrame(rows, columns=headers)
            
            print(f"✅ {len(df)} registros descargados")
            
            # Procesar datos
            games_dict = {}
            
            for _, row in df.iterrows():
                game_id = row['GAME_ID']
                team_id = row['TEAM_ID']
                team_abbr = ID_TO_TEAM.get(team_id, 'UNK')
                
                if game_id not in games_dict:
                    games_dict[game_id] = {
                        'game_id': game_id,
                        'game_date': row['GAME_DATE'],
                        'matchup': row['MATCHUP']
                    }
                
                # Determinar si es home o away
                if '@' in row['MATCHUP']:
                    # Away team (juega "@")
                    games_dict[game_id]['away_team'] = team_abbr
                    games_dict[game_id]['away_pts'] = row['PTS']
                    games_dict[game_id]['away_reb'] = row['REB']
                    games_dict[game_id]['away_ast'] = row['AST']
                    games_dict[game_id]['away_tov'] = row['TOV']
                    games_dict[game_id]['away_fg_pct'] = row['FG_PCT']
                else:
                    # Home team (juega "vs.")
                    games_dict[game_id]['home_team'] = team_abbr
                    games_dict[game_id]['home_pts'] = row['PTS']
                    games_dict[game_id]['home_reb'] = row['REB']
                    games_dict[game_id]['home_ast'] = row['AST']
                    games_dict[game_id]['home_tov'] = row['TOV']
                    games_dict[game_id]['home_fg_pct'] = row['FG_PCT']
            
            # Convertir a DataFrame
            games_list = []
            for game_id, game_data in games_dict.items():
                # Solo agregar si tiene ambos equipos
                if 'home_team' in game_data and 'away_team' in game_data:
                    games_list.append(game_data)
            
            df_games = pd.DataFrame(games_list)
            
            # Limitar a max_games
            df_games = df_games.head(max_games)
            
            print(f"✅ {len(df_games)} partidos completos procesados")
            
            return df_games
            
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def fetch_team_stats(season="2024-25"):
    """
    Obtiene estadísticas de todos los equipos
    
    Returns:
        Dict con stats por equipo
    """
    print(f"\n📊 Descargando estadísticas de equipos...")
    
    url = f"{NBA_STATS_BASE}/leaguestandingsv3"
    
    params = {
        'Season': season,
        'SeasonType': 'Regular Season',
        'LeagueID': '00'
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            headers = data['resultSets'][0]['headers']
            rows = data['resultSets'][0]['rowSet']
            
            df = pd.DataFrame(rows, columns=headers)
            
            team_stats = {}
            for _, row in df.iterrows():
                team_id = row['TeamID']
                team_abbr = ID_TO_TEAM.get(team_id, 'UNK')
                
                wins = row['WINS']
                losses = row['LOSSES']
                total = wins + losses
                win_pct = wins / total if total > 0 else 0.5
                
                # Calcular ELO basado en win%
                elo = 1500 + (win_pct - 0.5) * 400
                
                team_stats[team_abbr] = {
                    'wins': wins,
                    'losses': losses,
                    'win_pct': win_pct,
                    'elo': round(elo, 1)
                }
            
            print(f"✅ Stats de {len(team_stats)} equipos obtenidas")
            return team_stats
            
        else:
            print(f"⚠️  No se pudieron obtener stats de equipos")
            return {}
            
    except Exception as e:
        print(f"⚠️  Error obteniendo stats: {e}")
        return {}


def enrich_games_with_stats(df, team_stats):
    """
    Enriquece los partidos con estadísticas adicionales
    """
    print(f"\n🔧 Enriqueciendo datos con features ML...")
    
    # Determinar ganador
    df['home_win'] = (df['home_pts'] > df['away_pts']).astype(int)
    df['point_diff'] = df['home_pts'] - df['away_pts']
    
    # Calcular diferencias
    df['reb_diff'] = df['home_reb'] - df['away_reb']
    df['ast_diff'] = df['home_ast'] - df['away_ast']
    df['tov_diff'] = df['home_tov'] - df['away_tov']
    
    # Asignar ELO a cada equipo
    df['home_elo'] = df['home_team'].map(lambda x: team_stats.get(x, {}).get('elo', 1500))
    df['away_elo'] = df['away_team'].map(lambda x: team_stats.get(x, {}).get('elo', 1500))
    df['elo_diff'] = df['home_elo'] - df['away_elo']
    
    # Lesiones (simuladas - en producción usar API de injuries)
    import numpy as np
    np.random.seed(42)
    df['home_injuries'] = np.random.randint(0, 4, size=len(df))
    df['away_injuries'] = np.random.randint(0, 4, size=len(df))
    df['injury_diff'] = df['away_injuries'] - df['home_injuries']
    
    # Rolling stats (últimos 5 partidos)
    df = df.sort_values('game_date')
    
    df['home_roll5_pts'] = df.groupby('home_team')['home_pts'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    df['away_roll5_pts'] = df.groupby('away_team')['away_pts'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    
    df['home_roll5_reb'] = df.groupby('home_team')['home_reb'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    df['away_roll5_reb'] = df.groupby('away_team')['away_reb'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    
    df['home_roll5_ast'] = df.groupby('home_team')['home_ast'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    df['away_roll5_ast'] = df.groupby('away_team')['away_ast'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    
    # Diferencias rolling
    df['roll5_point_diff'] = df['home_roll5_pts'] - df['away_roll5_pts']
    df['roll5_reb_diff'] = df['home_roll5_reb'] - df['away_roll5_reb']
    df['roll5_ast_diff'] = df['home_roll5_ast'] - df['away_roll5_ast']
    
    # Home advantage
    df['home_advantage'] = 1
    
    print(f"✅ Features añadidos correctamente")
    
    return df


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🏀 NBA DATA FETCHER - API Oficial (SIN API KEYS)")
    print("="*60)
    
    # 1. Obtener stats de equipos (para ELO)
    print("\n[PASO 1/3] Obteniendo estadísticas de equipos...")
    team_stats = fetch_team_stats(season="2024-25")
    
    if not team_stats:
        print("⚠️  No se pudieron obtener stats, usando defaults")
        team_stats = {team: {'elo': 1500, 'wins': 15, 'losses': 15} 
                     for team in TEAM_IDS.keys()}
    
    # 2. Descargar partidos
    print("\n[PASO 2/3] Descargando partidos...")
    df_games = fetch_season_games(season="2024-25", max_games=500)
    
    if len(df_games) == 0:
        print("\n❌ No se pudieron descargar partidos")
        print("💡 SOLUCIÓN: Usa datos sintéticos")
        print("   python app/generate_sample_data.py")
        return
    
    print(f"✅ {len(df_games)} partidos descargados")
    
    # 3. Enriquecer con stats
    print("\n[PASO 3/3] Enriqueciendo datos...")
    df_enriched = enrich_games_with_stats(df_games, team_stats)
    
    # 4. Guardar CSV
    os.makedirs("data", exist_ok=True)
    output_path = "data/nba_games_clean.csv"
    
    df_enriched.to_csv(output_path, index=False)
    
    print("\n" + "="*60)
    print("✅ DATOS DESCARGADOS Y GUARDADOS")
    print("="*60)
    print(f"📂 Archivo: {output_path}")
    print(f"📊 Total partidos: {len(df_enriched)}")
    print(f"🏆 Victorias locales: {df_enriched['home_win'].sum()} ({df_enriched['home_win'].mean()*100:.1f}%)")
    print(f"✈️  Victorias visitantes: {(1-df_enriched['home_win']).sum()} ({(1-df_enriched['home_win']).mean()*100:.1f}%)")
    
    print("\n📋 Columnas disponibles:")
    print(df_enriched.columns.tolist())
    
    print("\n👀 Primeros 3 partidos:")
    print(df_enriched[['game_date', 'home_team', 'away_team', 'home_pts', 'away_pts', 'home_win']].head(3))
    
    print("\n📊 Distribución por equipo local:")
    print(df_enriched['home_team'].value_counts().head(10))
    
    print("\n" + "="*60)
    print("📝 PRÓXIMOS PASOS:")
    print("="*60)
    print("1. Inicia el servidor ML: python app/main.py")
    print("2. Entrena el modelo: python train_model.py")
    print("3. Inicia el backend: cd ../backend && python app.py")
    print("\n🎯 ¡Datos REALES de la API oficial de NBA!")


if __name__ == "__main__":
    main()