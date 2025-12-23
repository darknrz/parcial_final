import { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, Loader, Trophy, BarChart3, Activity, X, Check } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export default function AnalyzeText({ onPredictionComplete }) {
  const [homeTeam, setHomeTeam] = useState(null);
  const [awayTeam, setAwayTeam] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [teams, setTeams] = useState([]);
  const [searchHome, setSearchHome] = useState('');
  const [searchAway, setSearchAway] = useState('');

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/teams`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setTeams(response.data.teams);
    } catch (err) {
      console.error('Error cargando equipos:', err);
    }
  };

  const handleAnalyze = async () => {
    if (!homeTeam || !awayTeam) {
      setError('Selecciona ambos equipos para continuar');
      return;
    }

    if (homeTeam.abbr === awayTeam.abbr) {
      setError('No puedes seleccionar el mismo equipo dos veces');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const text = `${homeTeam.abbr} vs ${awayTeam.abbr}`;
      
      const response = await axios.post(
        `${API_URL}/analyze-text`,
        { text },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setResult(response.data);
      
      // Notificar al Dashboard que se completó una predicción
      if (onPredictionComplete) {
        onPredictionComplete();
      }
      
    } catch (err) {
      console.error('❌ Error en análisis:', err);
      
      if (err.response?.status === 401) {
        setError('Sesión expirada. Por favor inicia sesión nuevamente.');
        setTimeout(() => {
          localStorage.clear();
          window.location.href = '/login';
        }, 2000);
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err.code === 'ERR_NETWORK') {
        setError('Error de conexión. Verifica que el servidor esté corriendo.');
      } else {
        setError('Error al realizar la predicción. Intenta nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  const resetSelection = () => {
    setHomeTeam(null);
    setAwayTeam(null);
    setResult(null);
    setError('');
    setSearchHome('');
    setSearchAway('');
  };

  const filteredTeamsHome = teams.filter(team => 
    team.name.toLowerCase().includes(searchHome.toLowerCase()) ||
    team.abbr.toLowerCase().includes(searchHome.toLowerCase())
  );

  const filteredTeamsAway = teams.filter(team => 
    team.name.toLowerCase().includes(searchAway.toLowerCase()) ||
    team.abbr.toLowerCase().includes(searchAway.toLowerCase())
  ).filter(team => team.abbr !== homeTeam?.abbr);

  const getWinnerColor = (winner, team) => {
    if (winner === team) {
      return 'bg-emerald-500/10 border-emerald-500';
    }
    return 'bg-slate-800 border-slate-700';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 70) return 'text-emerald-400';
    if (confidence >= 60) return 'text-yellow-400';
    return 'text-orange-400';
  };

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 bg-emerald-500 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Predictor NBA</h2>
            <p className="text-sm text-gray-400">Análisis con inteligencia artificial</p>
          </div>
        </div>
        <div className="w-20 h-1 bg-emerald-500"></div>
      </div>

      {/* Selector de Equipos */}
      {!result && (
        <div className="space-y-6">
          {/* Equipo Local */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                <h3 className="text-lg font-bold text-white uppercase tracking-wide">Equipo Local</h3>
              </div>
              {homeTeam && (
                <button
                  onClick={() => setHomeTeam(null)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {!homeTeam ? (
              <>
                <input
                  type="text"
                  placeholder="Buscar equipo..."
                  value={searchHome}
                  onChange={(e) => setSearchHome(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-lg text-white placeholder-gray-500 mb-4 focus:outline-none focus:border-emerald-500"
                />
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-60 overflow-y-auto">
                  {filteredTeamsHome.map((team) => (
                    <button
                      key={team.abbr}
                      onClick={() => setHomeTeam(team)}
                      className="px-3 py-2 bg-slate-950 hover:bg-emerald-500/10 border border-slate-700 hover:border-emerald-500 rounded-lg transition text-left"
                    >
                      <span className="font-bold text-emerald-400">{team.abbr}</span>
                      <span className="text-gray-400 text-xs ml-2 block">{team.name}</span>
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <div className="bg-slate-950 border-2 border-emerald-500 rounded-lg p-4 flex items-center gap-3">
                <Check className="w-6 h-6 text-emerald-400 flex-shrink-0" />
                <div>
                  <p className="text-2xl font-bold text-emerald-400">{homeTeam.abbr}</p>
                  <p className="text-sm text-gray-400">{homeTeam.name}</p>
                </div>
              </div>
            )}
          </div>

          {/* VS Divider */}
          {homeTeam && (
            <div className="flex items-center justify-center">
              <div className="bg-slate-800 border border-slate-700 rounded-lg px-6 py-2">
                <span className="text-2xl font-bold text-gray-400">VS</span>
              </div>
            </div>
          )}

          {/* Equipo Visitante */}
          {homeTeam && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <h3 className="text-lg font-bold text-white uppercase tracking-wide">Equipo Visitante</h3>
                </div>
                {awayTeam && (
                  <button
                    onClick={() => setAwayTeam(null)}
                    className="text-gray-400 hover:text-white transition"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              {!awayTeam ? (
                <>
                  <input
                    type="text"
                    placeholder="Buscar equipo..."
                    value={searchAway}
                    onChange={(e) => setSearchAway(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-lg text-white placeholder-gray-500 mb-4 focus:outline-none focus:border-blue-500"
                  />
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-60 overflow-y-auto">
                    {filteredTeamsAway.map((team) => (
                      <button
                        key={team.abbr}
                        onClick={() => setAwayTeam(team)}
                        className="px-3 py-2 bg-slate-950 hover:bg-blue-500/10 border border-slate-700 hover:border-blue-500 rounded-lg transition text-left"
                      >
                        <span className="font-bold text-blue-400">{team.abbr}</span>
                        <span className="text-gray-400 text-xs ml-2 block">{team.name}</span>
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <div className="bg-slate-950 border-2 border-blue-500 rounded-lg p-4 flex items-center gap-3">
                  <Check className="w-6 h-6 text-blue-400 flex-shrink-0" />
                  <div>
                    <p className="text-2xl font-bold text-blue-400">{awayTeam.abbr}</p>
                    <p className="text-sm text-gray-400">{awayTeam.name}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Botón Analizar */}
          {homeTeam && awayTeam && (
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full py-4 bg-emerald-500 text-white font-bold text-lg rounded-lg hover:bg-emerald-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 uppercase tracking-wide"
            >
              {loading ? (
                <>
                  <Loader className="w-6 h-6 animate-spin" />
                  Analizando...
                </>
              ) : (
                <>
                  <Activity className="w-6 h-6" />
                  Predecir Ganador
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div className="space-y-6">
          {/* Matchup */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center">
            <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">Partido Analizado</p>
            <h3 className="text-4xl font-bold text-white mb-2">
              {result.matchup}
            </h3>
            {result.stats_source && (
              <p className="text-xs text-gray-500">{result.stats_source}</p>
            )}
          </div>

          {/* Ganador */}
          <div className="bg-emerald-500/10 border-2 border-emerald-500 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="bg-emerald-500 p-3 rounded-lg">
                  <Trophy className="w-8 h-8 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400 uppercase tracking-wide mb-1">Ganador Predicho</p>
                  <p className="text-4xl font-bold text-emerald-400">
                    {result.prediction.winner}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400 uppercase tracking-wide mb-1">Confianza</p>
                <p className={`text-5xl font-bold ${getConfidenceColor(result.prediction.confidence)}`}>
                  {result.prediction.confidence}%
                </p>
              </div>
            </div>
          </div>

          {/* Probabilidades */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className={`rounded-xl p-6 border-2 transition-all ${
              getWinnerColor(result.prediction.winner, result.matchup.split(' vs ')[0])
            }`}>
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
                <p className="text-xs text-gray-400 uppercase tracking-wider">Local</p>
              </div>
              <p className="text-2xl font-bold text-white mb-2">
                {result.matchup.split(' vs ')[0]}
              </p>
              <p className="text-4xl font-bold text-emerald-400">
                {result.prediction.home_win_probability}%
              </p>
            </div>

            <div className={`rounded-xl p-6 border-2 transition-all ${
              getWinnerColor(result.prediction.winner, result.matchup.split(' vs ')[1])
            }`}>
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                <p className="text-xs text-gray-400 uppercase tracking-wider">Visitante</p>
              </div>
              <p className="text-2xl font-bold text-white mb-2">
                {result.matchup.split(' vs ')[1]}
              </p>
              <p className="text-4xl font-bold text-blue-400">
                {result.prediction.away_win_probability}%
              </p>
            </div>
          </div>

          {/* Info */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-gray-400">
                <Activity className="w-4 h-4" />
                <span>Modelo: <span className="font-semibold text-white">XGBoost ML</span></span>
              </div>
              <div className="text-gray-500">
                ID: #{result.id}
              </div>
            </div>
          </div>

          {/* Botón Nueva Predicción */}
          <button
            onClick={resetSelection}
            className="w-full py-3 bg-slate-800 border border-slate-700 text-white font-semibold rounded-lg hover:bg-slate-700 transition"
          >
            Nueva Predicción
          </button>
        </div>
      )}
    </div>
  );
}