// src/api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:3001/api',
  timeout: 65000, // 65s para cubrir los GAs pesados
  headers: { 'Content-Type': 'application/json' },
});

export default api;
