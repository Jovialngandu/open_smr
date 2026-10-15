import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG } from '../config/api.config';
import { EMAIL_LOGS_ENDPOINT, EmailLog, SETTINGS_ENDPOINT, UserPreferences, UserPreferencesUpdate } from '../../features/settings/services/settings.service';
const THEMES = ['LIGHT', 'DARK', 'SYSTEM'];
const DEMO_USER_ID = '8f4b8400-e29b-41d4-a716-446655440000';
const emailLogs: Array<EmailLog & { organization_id: string; user_id: string }> = [
  { id: 'email-001', user_id: DEMO_USER_ID, organization_id: '8f4b8400-e29b-41d4-a716-446655440001', email_type: 'OVERDUE_TASK_ALERT', recipient: 'demo@opensmr.fr', subject: 'Rappel : action de sécurité en retard', sent_at: '2026-09-11T08:00:00Z', status: true, error_message: null },
  { id: 'email-002', user_id: DEMO_USER_ID, organization_id: '8f4b8400-e29b-41d4-a716-446655440002', email_type: 'RISK_NOTIFICATION', recipient: 'demo@opensmr.fr', subject: 'Suivi des risques du périmètre', sent_at: '2026-09-10T08:00:00Z', status: true, error_message: null },
];

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
  if (!API_CONFIG.useMocks) return next(request);
  if (request.url === EMAIL_LOGS_ENDPOINT && request.method === 'GET') {
    const organizationId = request.params.get('organization_id');
    const userId = mockUserId(request.headers.get('Authorization'));
    return ok(emailLogs.filter((log) => log.user_id === userId && (!organizationId || log.organization_id === organizationId)).map(({ organization_id: _organizationId, user_id: _userId, ...log }) => log));
  }
  if (request.url !== SETTINGS_ENDPOINT) return next(request);

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

function mockUserId(authorization: string | null): string {
  if (!authorization) return DEMO_USER_ID;
  try {
    const payload = authorization.replace(/^Bearer\s+/i, '').split('.')[1];
    return String(JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/'))).user_id ?? '');
  } catch { return ''; }
}

function ok<T>(body: T) {
  return of(new HttpResponse({ body, status: 200 })).pipe(delay(API_CONFIG.mockDelayMs));
}

function fail(detail: string) {
  return throwError(() => new HttpErrorResponse({ status: 400, error: { detail } }));
}
