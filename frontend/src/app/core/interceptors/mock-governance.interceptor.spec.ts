import { HttpParams, HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../config/api.config';
import { Asset, Risk } from '../models/governance.models';
import { mockGovernanceInterceptor } from './mock-governance.interceptor';

const DIGITAL_SCOPE_ID = '8f4b8400-e29b-41d4-a716-446655440101';

describe('mockGovernanceInterceptor', () => {
  it('filtre les actifs selon le périmètre actif', async () => {
    const request = new HttpRequest('GET', DOMAIN_ENDPOINTS.assets, null, {
      params: new HttpParams().set('scope_id', DIGITAL_SCOPE_ID),
    });

    const response = await intercept<Asset[]>(request);

    expect(response.body).toHaveLength(4);
    expect(response.body?.every((asset) => asset.scope_id === DIGITAL_SCOPE_ID)).toBe(true);
  });

  it('calcule la criticité DIC lors de la création d’un actif', async () => {
    const request = new HttpRequest('POST', DOMAIN_ENDPOINTS.assets, {
      scope_id: DIGITAL_SCOPE_ID,
      name: 'Référentiel documentaire',
      category: 'DATA',
      owner_id: '1',
      description: 'Documents du SMSI.',
      confidentiality: 2,
      integrity: 3,
      availability: 1,
    });

    const response = await intercept<Asset>(request);

    expect(response.status).toBe(201);
    expect(response.body?.criticality).toBe(3);
  });

  it('calcule le score brut lors de la création d’un risque', async () => {
    const request = new HttpRequest('POST', DOMAIN_ENDPOINTS.risks, {
      asset_id: 'asset-001',
      code: 'RSK-TEST-001',
      threat_description: 'Scénario de test.',
      likelihood: 4,
      impact: 5,
      status: 'OPEN',
    });

    const response = await intercept<Risk>(request);

    expect(response.status).toBe(201);
    expect(response.body?.score).toBe(20);
    expect(response.body?.scope_id).toBe(DIGITAL_SCOPE_ID);
  });
});

async function intercept<T>(request: HttpRequest<unknown>): Promise<HttpResponse<T>> {
  return firstValueFrom(mockGovernanceInterceptor(request, () => {
    throw new Error('Le mock aurait dû intercepter la requête.');
  })) as Promise<HttpResponse<T>>;
}
