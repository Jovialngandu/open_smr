import { HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { AUTH_ENDPOINTS, DOMAIN_ENDPOINTS } from '../config/api.config';
import { AuthResponse } from '../models/auth.models';
import { mockAuthInterceptor } from './mock-auth.interceptor';

describe('mockAuthInterceptor', () => {
  it('retourne une session JWT au compte de demonstration', async () => {
    const request = new HttpRequest('POST', AUTH_ENDPOINTS.login, {
      username: 'demo.rssi',
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

  it('rattache une inscription à une organisation sans accorder de périmètre', async () => {
    const request = new HttpRequest('POST', AUTH_ENDPOINTS.register, {
      username: 'nouveau.mock', email: 'nouveau.mock@example.com', password: 'MotDePasse123!',
      first_name: 'Nouveau', last_name: 'Mock', join_organization_code: 'ASTERIA',
    });

    const response = await firstValueFrom(mockAuthInterceptor(request, () => {
      throw new Error('Le mock aurait dû intercepter la requête.');
    })) as HttpResponse<AuthResponse>;

    expect(response.status).toBe(201);
    expect(response.body?.user?.roles[0].role).toBe('RISK_OWNER');
    expect(response.body?.user?.roles[0].scopes).toEqual([]);
  });

  it('autorise la création d’un compte sans organisation', async () => {
    const request = new HttpRequest('POST', AUTH_ENDPOINTS.register, {
      username: 'sans.org', email: 'sans.org@example.com', password: 'MotDePasse123!',
    });
    const response = await firstValueFrom(mockAuthInterceptor(request, () => {
      throw new Error('Le mock aurait dû intercepter la requête.');
    })) as HttpResponse<AuthResponse>;
    expect(response.status).toBe(201);
    expect(response.body?.user?.roles).toEqual([]);
  });

  it('permet de créer une organisation après l’inscription', async () => {
    const created = await firstValueFrom(mockAuthInterceptor(new HttpRequest('POST', DOMAIN_ENDPOINTS.organizations, {
      name: 'Entreprise après inscription', code: 'APRESINSCRIPTION',
    }), () => { throw new Error('Requête non interceptée.'); })) as HttpResponse<{ id: string }>;
    expect(created.status).toBe(201);
    const switched = await firstValueFrom(mockAuthInterceptor(new HttpRequest('POST', AUTH_ENDPOINTS.switchContext, {
      organization_id: created.body?.id, scope_id: null,
    }), () => { throw new Error('Requête non interceptée.'); })) as HttpResponse<{ active_organization_id: string }>;
    expect(switched.body?.active_organization_id).toBe(created.body?.id);
  });
});
