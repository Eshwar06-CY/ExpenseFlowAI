import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let accessToken = null;
let refreshSubscribers = [];
let isRefreshing = false;

export const setAccessToken = (token) => {
  accessToken = token;
};

export const getAccessToken = () => {
  return accessToken;
};

// Request interceptor: Inject Access Token
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 Unauthorized / Token Expiry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        handleLogoutRedirect();
        return Promise.reject(error);
      }

      if (!isRefreshing) {
        isRefreshing = true;

        try {
          // Attempt token rotation
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;

          setAccessToken(access_token);
          localStorage.setItem('refresh_token', refresh_token);

          isRefreshing = false;

          if (refreshSubscribers.length > 0) {
            refreshSubscribers.forEach((cb) => cb(access_token));
            refreshSubscribers = [];
          }

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          isRefreshing = false;
          refreshSubscribers = [];
          handleLogoutRedirect();
          return Promise.reject(refreshError);
        }
      } else {
        // Queue parallel requests until refresh completes
        return new Promise((resolve) => {
          refreshSubscribers.push((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }
    }

    return Promise.reject(error);
  }
);

function handleLogoutRedirect() {
  setAccessToken(null);
  localStorage.removeItem('refresh_token');
  window.dispatchEvent(new Event('auth-expired'));

  const path = window.location.pathname;
  if (path !== '/login' && path !== '/register' && path !== '/') {
    window.location.href = '/login';
  }
}

export default api;
