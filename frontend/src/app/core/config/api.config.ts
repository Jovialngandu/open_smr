export const API_CONFIG = {
  baseUrl: 'https://open-smr.onrender.com/api/v1',
  useMocks: false,
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
  organizations: `${API_CONFIG.baseUrl}/organizations/`,
  scopes: `${API_CONFIG.baseUrl}/scopes/`,
  assets: `${API_CONFIG.baseUrl}/assets/`,
  risks: `${API_CONFIG.baseUrl}/risks/`,
  heatmap: `${API_CONFIG.baseUrl}/heatmap/`,
  treatments: `${API_CONFIG.baseUrl}/treatments/tasks/`,
  evidences: `${API_CONFIG.baseUrl}/treatments/evidences/`,
  soa: `${API_CONFIG.baseUrl}/soa/`,
  soaVersions: `${API_CONFIG.baseUrl}/soa/versions/`,
  soaEntries: `${API_CONFIG.baseUrl}/soa/entries/`,

  users: `${API_CONFIG.baseUrl}/users/`,
} as const;

export function organizationMembersEndpoint(organizationId: string): string {
  return `${DOMAIN_ENDPOINTS.organizations}${organizationId}/members/`;
}

export function organizationMemberStatusEndpoint(organizationId: string, roleId: string): string {
  return `${organizationMembersEndpoint(organizationId)}${roleId}/toggle-status/`;
}

export function scopeDashboardEndpoint(scopeId: string): string {
  return `${DOMAIN_ENDPOINTS.scopes}${scopeId}/dashboard/`;
}

export function scopeAccessEndpoint(scopeId: string): string {
  return `${DOMAIN_ENDPOINTS.scopes}${scopeId}/access/`;
}

export function scopeAccessRemovalEndpoint(scopeId: string): string {
  return `${scopeAccessEndpoint(scopeId)}remove/`;
}

export function taskEvidencesEndpoint(taskId: string): string {
  return `${DOMAIN_ENDPOINTS.treatments}${taskId}/evidences/`;
}

export function soaExportEndpoint(scopeId: string): string {
  return `${API_CONFIG.baseUrl}/exporter/scopes/${scopeId}/export/`;
}