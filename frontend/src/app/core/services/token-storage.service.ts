import { Injectable } from '@angular/core';

import { AuthTokens, JwtClaims } from '../models/auth.models';

const ACCESS_TOKEN_KEY = 'opensmr.access_token';
const REFRESH_TOKEN_KEY = 'opensmr.refresh_token';

@Injectable({ providedIn: 'root' })
export class TokenStorageService {
  get accessToken(): string | null {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY);
  }

  get refreshToken(): string | null {
    return sessionStorage.getItem(REFRESH_TOKEN_KEY);
  }

  save(tokens: AuthTokens): void {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  }

  clear(): void {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  claims(token = this.accessToken): JwtClaims | null {
    if (!token) return null;

    try {
      const payload = token.split('.')[1];
      const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
      const decoded = decodeURIComponent(
        atob(normalized)
          .split('')
          .map((character) => `%${character.charCodeAt(0).toString(16).padStart(2, '0')}`)
          .join(''),
      );
      return JSON.parse(decoded) as JwtClaims;
    } catch {
      return null;
    }
  }

  isAccessTokenValid(): boolean {
    const claims = this.claims();
    return !!claims && (!claims.exp || claims.exp * 1000 > Date.now());
  }
}
