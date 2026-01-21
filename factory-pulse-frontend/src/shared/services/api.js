import axios from 'axios';

/**
 * Axios API Instance.
 * Configured with the backend base URL and default headers.
 * Acts as the central point for all HTTP requests in the application.
 */
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
});

/**
 * Request Interceptor.
 * Automatically checks for a stored JWT Access Token and attaches it 
 * to the Authorization header of every outgoing request.
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response Interceptor.
 * Handles global API responses and errors.
 * Specifically watches for 401 Unauthorized status (invalid or expired token)
 * to automatically clear session data and redirect the user to the login page.
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid: Force logout
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;