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

export const modelsAPI = {
  searchHuggingFace: (query: string, modelType?: string, limit?: number) =>
    api.post('/api/v1/models/search-huggingface', { query, model_type: modelType, limit }),

  list: (modelType?: string, skip?: number, limit?: number) => {
    const params: any = {};
    if (modelType) params.model_type = modelType;
    if (skip !== undefined) params.skip = skip;
    if (limit !== undefined) params.limit = limit;
    return api.get('/api/v1/models', { params });
  },

  import: (data: {
    name: string;
    model_type: string;
    model_id: string;
    description?: string;
    source?: string;
    tags?: string[];
  }) => api.post('/api/v1/models', data),

  get: (id: string) => api.get(`/api/v1/models/${id}`),

  update: (id: string, data: {
    name?: string;
    description?: string;
    tags?: string[];
    is_public?: boolean;
  }) => api.put(`/api/v1/models/${id}`, data),

  delete: (id: string) => api.delete(`/api/v1/models/${id}`),
};

export const datasetsAPI = {
  upload: (formData: FormData) => api.post('/api/v1/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),

  list: (projectId?: string, skip?: number, limit?: number) => {
    const params: any = {};
    if (projectId) params.project_id = projectId;
    if (skip !== undefined) params.skip = skip;
    if (limit !== undefined) params.limit = limit;
    return api.get('/api/v1/datasets', { params });
  },

  get: (id: string) => api.get(`/api/v1/datasets/${id}`),

  update: (id: string, data: {
    name?: string;
    description?: string;
    tags?: string[];
  }) => api.put(`/api/v1/datasets/${id}`, data),

  configureSplit: (id: string, data: {
    train_split: number;
    validation_split: number;
    test_split: number;
  }) => api.post(`/api/v1/datasets/${id}/configure-split`, data),

  delete: (id: string) => api.delete(`/api/v1/datasets/${id}`),
};

export const trainingAPI = {
  create: (data: {
    name: string;
    description?: string;
    project_id: string;
    base_model_id: string;
    dataset_id: string;
    fine_tuning_method: string;
    hyperparameters?: any;
  }) => api.post('/api/v1/training', data),

  list: (params?: {
    project_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/api/v1/training', { params }),

  get: (id: string) => api.get(`/api/v1/training/${id}`),

  update: (id: string, data: {
    name?: string;
    description?: string;
  }) => api.put(`/api/v1/training/${id}`, data),

  cancel: (id: string) => api.post(`/api/v1/training/${id}/cancel`),

  delete: (id: string) => api.delete(`/api/v1/training/${id}`),

  listConfigs: () => api.get('/api/v1/training/configs'),
};
