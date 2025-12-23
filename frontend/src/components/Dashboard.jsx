import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, TrendingUp, LogOut, History, Trophy, BarChart3, Loader, Activity, Calendar, Target } from 'lucide-react';
import axios from 'axios';
import AnalyzeText from './AnalyzeText';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('analyze');
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        navigate('/login');
        return;
      }

      // Obtener perfil de usuario con sus predicciones
      const profileResponse = await axios.get(`${API_URL}/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setUser(profileResponse.data.user);
      setPredictions(profileResponse.data.recent_predictions || []);
      
    } catch (err) {
      console.error('Error fetching profile:', err);
      if (err.response?.status === 401) {
        localStorage.clear();
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePredictionComplete = () => {
    fetchProfile();
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <Loader className="w-12 h-12 text-emerald-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 font-medium">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">

              <div>

                <p className=" text-gray-400 uppercase tracking-wider">Portal Deportivo NBA</p>
              </div>
            </div>

            {/* User Info */}
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Usuario</p>
                <p className="font-bold text-white">{user?.username}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg hover:bg-red-600 hover:border-red-600 transition"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Salir</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 pt-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard
            icon={<User className="w-6 h-6 text-emerald-400" />}
            title="Usuario Activo"
            value={user?.username}
            color="emerald"
          />
          <StatCard
            icon={<BarChart3 className="w-6 h-6 text-blue-400" />}
            title="Predicciones"
            value={predictions.length}
            color="blue"
          />
          <StatCard
            icon={<Activity className="w-6 h-6 text-purple-400" />}
            title="Modelo"
            value="XGBoost"
            color="purple"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="bg-slate-900 border border-slate-800 rounded-t-xl p-2">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('analyze')}
              className={`flex-1 py-3 px-6 rounded-lg font-bold transition-all flex items-center justify-center gap-2 uppercase tracking-wide ${
                activeTab === 'analyze'
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-800 text-gray-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              <TrendingUp className="w-5 h-5" />
              Analizar
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 py-3 px-6 rounded-lg font-bold transition-all flex items-center justify-center gap-2 uppercase tracking-wide ${
                activeTab === 'history'
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-800 text-gray-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              <History className="w-5 h-5" />
              Historial
              <span className="bg-slate-950 px-2 py-0.5 rounded text-xs">
                {predictions.length}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 pb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-b-xl p-8 min-h-[500px]">
          {activeTab === 'analyze' && <AnalyzeText onPredictionComplete={handlePredictionComplete} />}
          {activeTab === 'history' && <PredictionHistory predictions={predictions} />}
        </div>
      </main>


    </div>
  );
}

// ========================================
// COMPONENTE: StatCard
// ========================================

function StatCard({ icon, title, value, color }) {
  const colorClasses = {
    emerald: 'bg-emerald-500/10 border-emerald-500/30',
    blue: 'bg-blue-500/10 border-blue-500/30',
    purple: 'bg-purple-500/10 border-purple-500/30'
  };

  return (
    <div className={`${colorClasses[color]} border rounded-xl p-4 flex items-center gap-4`}>
      <div className="bg-slate-950 p-3 rounded-lg">
        {icon}
      </div>
      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{title}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
      </div>
    </div>
  );
}

// ========================================
// COMPONENTE: PredictionHistory
// ========================================

function PredictionHistory({ predictions }) {
  const [showAll, setShowAll] = useState(true);
  const displayLimit = 10;
  const displayedPredictions = showAll ? predictions : predictions.slice(0, displayLimit);

  if (predictions.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="bg-slate-800 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-4">
          <History className="w-12 h-12 text-gray-600" />
        </div>
        <p className="text-gray-300 text-xl font-bold mb-2">
          Sin predicciones
        </p>
        <p className="text-gray-500 text-sm">
          Haz tu primera predicción en la pestaña "Analizar"
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center">
            <History className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Historial</h2>
            <p className="text-sm text-gray-400">
              {showAll ? `Mostrando todas (${predictions.length})` : `Mostrando ${Math.min(displayLimit, predictions.length)} de ${predictions.length}`}
            </p>
          </div>
        </div>
        
        {predictions.length > displayLimit && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg hover:bg-slate-700 transition text-sm font-semibold"
          >
            {showAll ? `Mostrar solo ${displayLimit}` : `Ver todas (${predictions.length})`}
          </button>
        )}
      </div>

      <div className="space-y-4 max-h-[calc(100vh-400px)] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900">
        {displayedPredictions.map((pred) => (
          <div
            key={pred.id}
            className="bg-slate-950 border border-slate-800 rounded-xl p-6 hover:border-emerald-500/50 transition"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-2xl font-bold text-white mb-1">
                  {pred.home_team} <span className="text-gray-600">vs</span> {pred.away_team}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Calendar className="w-3 h-3" />
                  {new Date(pred.created_at).toLocaleString('es-ES', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2 mb-1">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  <p className="text-xs text-gray-400 uppercase">Ganador</p>
                </div>
                <p className="text-3xl font-bold text-emerald-400">
                  {pred.predicted_winner}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-900 border border-emerald-500/30 rounded-lg p-3 text-center">
                <div className="flex items-center justify-center gap-1 mb-1">
                  <Target className="w-3 h-3 text-emerald-400" />
                  <p className="text-xs text-gray-400 uppercase">Confianza</p>
                </div>
                <p className="text-xl font-bold text-emerald-400">
                  {pred.confidence}%
                </p>
              </div>
              <div className="bg-slate-900 border border-blue-500/30 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-400 mb-1 uppercase">{pred.home_team}</p>
                <p className="text-xl font-bold text-blue-400">
                  {pred.home_win_prob}%
                </p>
              </div>
              <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-400 mb-1 uppercase">{pred.away_team}</p>
                <p className="text-xl font-bold text-purple-400">
                  {pred.away_win_prob}%
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {predictions.length > displayLimit && (
        <div className="mt-6 text-center pt-4 border-t border-slate-800">
          <p className="text-gray-400 text-sm mb-3">
            {showAll ? `Viendo todas las ${predictions.length} predicciones` : `Viendo ${displayLimit} de ${predictions.length} predicciones`}
          </p>
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-6 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition font-semibold"
          >
            {showAll ? `Mostrar solo ${displayLimit}` : `Ver todas las predicciones (${predictions.length})`}
          </button>
        </div>
      )}
    </div>
  );
}