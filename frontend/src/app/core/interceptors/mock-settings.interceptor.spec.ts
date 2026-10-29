import { HttpHeaders, HttpParams, HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { API_CONFIG } from '../config/api.config';
import { EMAIL_LOGS_ENDPOINT, EmailLog, SETTINGS_ENDPOINT, UserPreferences } from '../../features/settings/services/settings.service';
import { mockSettingsInterceptor } from './mock-settings.interceptor';

describe('mockSettingsInterceptor', () => {
  beforeAll(() => Object.defineProperty(API_CONFIG, 'useMocks', { value: true, configurable: true }));
  afterAll(() => Object.defineProperty(API_CONFIG, 'useMocks', { value: false, configurable: true }));

  it('utilise la route Django hors du préfixe v1', () => {
    expect(SETTINGS_ENDPOINT).toBe('https://open-smr.onrender.com/api/settings/me/');
  });

  it('renvoie les préférences personnelles', async () => {
    const response = await intercept<UserPreferences>(new HttpRequest('GET', SETTINGS_ENDPOINT));
    expect(response.body?.language).toBe('fr');
    expect(response.body?.email_notifications).toBe(true);
  });

  it('enregistre une mise à jour partielle', async () => {
    const response = await intercept<UserPreferences>(new HttpRequest('PATCH', SETTINGS_ENDPOINT, {
      theme: 'DARK',
      timezone: 'Europe/Paris',
    }));
    expect(response.body?.theme).toBe('DARK');
    expect(response.body?.timezone).toBe('Europe/Paris');
  });

  it('limite le journal d’e-mails à l’organisation demandée', async () => {
    const request = new HttpRequest('GET', EMAIL_LOGS_ENDPOINT, null, {
      params: new HttpParams().set('organization_id', '8f4b8400-e29b-41d4-a716-446655440001'),
    });
    const response = await intercept<EmailLog[]>(request);
    expect(response.body).toHaveLength(1);
    expect(response.body?.[0].email_type).toBe('OVERDUE_TASK_ALERT');
  });

  it('renvoie les e-mails de toutes les organisations du compte sans filtre', async () => {
    const response = await intercept<EmailLog[]>(new HttpRequest('GET', EMAIL_LOGS_ENDPOINT));
    expect(response.body?.map((log) => log.id)).toEqual(['email-001', 'email-002']);
  });

  it('ne présente pas les e-mails de démonstration à un autre compte', async () => {
    const token = `header.${btoa(JSON.stringify({ user_id: 'another-user' }))}.signature`;
    const request = new HttpRequest('GET', EMAIL_LOGS_ENDPOINT, null, {
      headers: new HttpHeaders({ Authorization: `Bearer ${token}` }),
    });
    const response = await intercept<EmailLog[]>(request);
    expect(response.body).toEqual([]);
  });
});

function intercept<T>(request: HttpRequest<unknown>) {
  return firstValueFrom(mockSettingsInterceptor(request, () => {
    throw new Error('Le mock des paramètres aurait dû intercepter la requête.');
  })) as Promise<HttpResponse<T>>;
}
