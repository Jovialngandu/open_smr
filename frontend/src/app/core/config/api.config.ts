export const API_CONFIG = {
  baseUrl: 'http://127.0.0.1:8000/api/v1',
  useMocks: true,
  mockDelayMs: 550,
} as const;

export const AUTH_ENDPOINTS = {
  login: `${API_CONFIG.baseUrl}/auth/login/`,
  register: `${API_CONFIG.baseUrl}/auth/register/`,
  refresh: `${API_CONFIG.baseUrl}/auth/refresh/`,
  profile: `${API_CONFIG.baseUrl}/auth/me/`,
  switchContext: `${API_CONFIG.baseUrl}/auth/switch-context/`,
} as const;
