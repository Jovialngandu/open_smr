import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { catchError, finalize, Observable, tap, throwError } from 'rxjs';

import { API_CONFIG } from '../../../core/config/api.config';

export const SETTINGS_ENDPOINT = `${API_CONFIG.baseUrl.replace(/\/v1\/?$/, '')}/settings/me/`;

export type AppTheme = 'LIGHT' | 'DARK' | 'SYSTEM';

export interface UserPreferences {
  id: string;
  language: string;
  theme: AppTheme;
  timezone: string;
  email_notifications: boolean;
  created_at: string;
  updated_at: string;
}

export type UserPreferencesUpdate = Pick<UserPreferences, 'language' | 'theme' | 'timezone' | 'email_notifications'>;

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly http = inject(HttpClient);
  private readonly preferencesState = signal<UserPreferences | null>(null);
  private readonly loadingState = signal(false);
  private readonly savingState = signal(false);
  private readonly errorState = signal('');

  readonly preferences = this.preferencesState.asReadonly();
  readonly loading = this.loadingState.asReadonly();
  readonly saving = this.savingState.asReadonly();
  readonly error = this.errorState.asReadonly();

  constructor() {
    const savedTheme = localStorage.getItem('opensmr.theme') as AppTheme | null;
    if (savedTheme && ['LIGHT', 'DARK', 'SYSTEM'].includes(savedTheme)) this.applyTheme(savedTheme);
  }

  load(): Observable<UserPreferences> {
    this.loadingState.set(true);
    this.errorState.set('');
    return this.http.get<UserPreferences>(SETTINGS_ENDPOINT).pipe(
      tap((preferences) => {
        this.preferencesState.set(preferences);
        localStorage.setItem('opensmr.theme', preferences.theme);
        this.applyTheme(preferences.theme);
      }),
      catchError((error) => {
        const friendly = this.friendlyError(error, 'Impossible de charger vos préférences.');
        this.errorState.set(friendly.message);
        return throwError(() => friendly);
      }),
      finalize(() => this.loadingState.set(false)),
    );
  }

  save(changes: UserPreferencesUpdate): Observable<UserPreferences> {
    this.savingState.set(true);
    this.errorState.set('');
    return this.http.patch<UserPreferences>(SETTINGS_ENDPOINT, changes).pipe(
      tap((preferences) => {
        this.preferencesState.set(preferences);
        localStorage.setItem('opensmr.theme', preferences.theme);
        this.applyTheme(preferences.theme);
      }),
      catchError((error) => {
        const friendly = this.friendlyError(error, 'Impossible d’enregistrer vos préférences.');
        this.errorState.set(friendly.message);
        return throwError(() => friendly);
      }),
      finalize(() => this.savingState.set(false)),
    );
  }

  applyTheme(theme: AppTheme): void {
    const resolved = theme === 'SYSTEM'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme.toLowerCase();
    document.documentElement.dataset['theme'] = resolved;
    document.documentElement.style.colorScheme = resolved;
  }

  private friendlyError(error: unknown, fallback: string): Error {
    if (error instanceof HttpErrorResponse) {
      const detail = error.error?.detail ?? Object.values(error.error ?? {})[0];
      if (typeof detail === 'string') return new Error(detail);
      if (Array.isArray(detail) && detail[0]) return new Error(String(detail[0]));
    }
    return new Error(fallback);
  }
}
