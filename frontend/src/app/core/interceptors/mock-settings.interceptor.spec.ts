import { HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { API_CONFIG } from '../config/api.config';
import { SETTINGS_ENDPOINT, UserPreferences } from '../../features/settings/services/settings.service';
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
});

function intercept<T>(request: HttpRequest<unknown>) {
  return firstValueFrom(mockSettingsInterceptor(request, () => {
    throw new Error('Le mock des paramètres aurait dû intercepter la requête.');
  })) as Promise<HttpResponse<T>>;
}
