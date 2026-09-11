import { HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { AUTH_ENDPOINTS } from '../config/api.config';
import { AuthResponse } from '../models/auth.models';
import { mockAuthInterceptor } from './mock-auth.interceptor';

describe('mockAuthInterceptor', () => {
  it('retourne une session JWT au compte de demonstration', async () => {
    const request = new HttpRequest('POST', AUTH_ENDPOINTS.login, {
      username: 'demo@opensmr.fr',
      password: 'Demo1234!',
    });

    const response = await firstValueFrom(mockAuthInterceptor(request, () => {
      throw new Error('Le mock aurait du intercepter la requete.');
    })) as HttpResponse<AuthResponse>;

    expect(response.status).toBe(200);
    expect(response.body?.access.split('.')).toHaveLength(3);
  });

  it('refuse des identifiants invalides', async () => {
    const request = new HttpRequest('POST', AUTH_ENDPOINTS.login, {
      username: 'inconnu',
      password: 'incorrect',
    });

    await expect(firstValueFrom(mockAuthInterceptor(request, () => {
      throw new Error('Le mock aurait du intercepter la requete.');
    }))).rejects.toMatchObject({ status: 401 });
  });
});
