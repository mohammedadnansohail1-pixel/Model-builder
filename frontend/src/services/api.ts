import axios, { AxiosInstance, AxiosError } from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest: any = error.config;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Show error toast
    const message =
      (error.response?.data as any)?.detail || error.message || 'An error occurred';
    toast.error(message);

    return Promise.reject(error);
  }
);

export default api;

// API endpoints
export const authAPI = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/api/v1/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/api/v1/auth/login', data),

  logout: (refreshToken: string) =>
    api.post('/api/v1/auth/logout', { refresh_token: refreshToken }),

  getCurrentUser: () => api.get('/api/v1/users/me'),

  updateProfile: (data: {
    email?: string;
    username?: string;
    full_name?: string;
    avatar_url?: string;
  }) => api.put('/api/v1/users/me', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/api/v1/users/me/change-password', data),

  getApiKey: () => api.get('/api/v1/users/me/api-key'),

  regenerateApiKey: () => api.post('/api/v1/users/me/regenerate-api-key'),
};

export const organizationsAPI = {
  list: () => api.get('/api/v1/organizations'),

  create: (data: { name: string; slug: string; description?: string }) =>
    api.post('/api/v1/organizations', data),

  get: (id: string) => api.get(`/api/v1/organizations/${id}`),

  update: (id: string, data: { name?: string; description?: string }) =>
    api.put(`/api/v1/organizations/${id}`, data),

  delete: (id: string) => api.delete(`/api/v1/organizations/${id}`),
};

export const projectsAPI = {
  list: (organizationId?: string) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    return api.get('/api/v1/projects', { params });
  },

  create: (data: {
    name: string;
    organization_id: string;
    description?: string;
    tags?: string[];
  }) => api.post('/api/v1/projects', data),

  get: (id: string) => api.get(`/api/v1/projects/${id}`),

  update: (
    id: string,
    data: { name?: string; description?: string; tags?: string[]; settings?: any }
  ) => api.put(`/api/v1/projects/${id}`, data),

  delete: (id: string) => api.delete(`/api/v1/projects/${id}`),
};
