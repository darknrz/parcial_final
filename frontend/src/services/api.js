import axios from 'axios';

const API_BASE_URL = 'http://localhost:3001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const oddsApi = {
  // Obtener deportes
  getSports: async () => {
    const response = await api.get('/odds/sports');
    return response.data;
  },

  // Obtener eventos de un deporte
  getEvents: async (sportKey) => {
    const response = await api.get(`/odds/events/${sportKey}`);
    return response.data;
  },

  // Obtener odds de un evento específico
  getEventOdds: async (eventId) => {
    const response = await api.get(`/odds/event/${eventId}`);
    return response.data;
  },

  // Refrescar odds
  refreshOdds: async (sportKey) => {
    const response = await api.post(`/odds/refresh/${sportKey}`);
    return response.data;
  },
};

export default api;