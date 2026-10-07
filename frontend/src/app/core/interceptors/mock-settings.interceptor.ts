import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG } from '../config/api.config';
import { UserPreferences, UserPreferencesUpdate } from '../../features/settings/services/settings.service';

const SETTINGS_ENDPOINT = `${API_CONFIG.baseUrl}/settings/me/`;
const THEMES = ['LIGHT', 'DARK', 'SYSTEM'];

let preferences: UserPreferences = {
  id: 'preference-current-user',
  language: 'fr',
  theme: 'LIGHT',
  timezone: 'Africa/Kinshasa',
  email_notifications: true,
  created_at: '2026-09-01T08:00:00Z',
  updated_at: '2026-09-01T08:00:00Z',
};

export const mockSettingsInterceptor: HttpInterceptorFn = (request, next) => {
  if (!API_CONFIG.useMocks || request.url !== SETTINGS_ENDPOINT) return next(request);

  if (request.method === 'GET') return ok(preferences);

  if (request.method === 'PATCH') {
    const changes = request.body as Partial<UserPreferencesUpdate>;
    if (changes.theme && !THEMES.includes(changes.theme)) return fail('Le thème sélectionné est invalide.');
    if (changes.language !== undefined && !changes.language.trim()) return fail('La langue est obligatoire.');
    if (changes.timezone !== undefined && !changes.timezone.trim()) return fail('Le fuseau horaire est obligatoire.');
    preferences = { ...preferences, ...changes, updated_at: new Date().toISOString() };
    return ok(preferences);
  }

  return next(request);
};

function ok<T>(body: T) {
  return of(new HttpResponse({ body, status: 200 })).pipe(delay(API_CONFIG.mockDelayMs));
}

function fail(detail: string) {
  return throwError(() => new HttpErrorResponse({ status: 400, error: { detail } }));
}
