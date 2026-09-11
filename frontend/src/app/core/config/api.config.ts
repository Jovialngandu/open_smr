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

export const DOMAIN_ENDPOINTS = {
  assets: `${API_CONFIG.baseUrl}/assets/`,
  risks: `${API_CONFIG.baseUrl}/risks/`,
  heatmap: `${API_CONFIG.baseUrl}/heatmap/`,
  treatments: `${API_CONFIG.baseUrl}/treatments/`,
  evidences: `${API_CONFIG.baseUrl}/treatment/evidences/`,
  soa: `${API_CONFIG.baseUrl}/soa/`,
  users: `${API_CONFIG.baseUrl}/users/`,
} as const;

export function soaExportEndpoint(scopeId: string, format: 'pdf' | 'csv'): string {
  return `${API_CONFIG.baseUrl}/scopes/${scopeId}/soa/export/?format=${format}`;
}
