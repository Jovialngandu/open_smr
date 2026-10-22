import { API_CONFIG } from './api.config';

export const GOOGLE_OIDC_ENDPOINT = `${API_CONFIG.baseUrl}/auth/oidc/callback/`;

// Public OAuth client ID from Google Cloud. Set this to the same value as backend GOOGLE_CLIENT_ID.
export const GOOGLE_CLIENT_ID = '';
