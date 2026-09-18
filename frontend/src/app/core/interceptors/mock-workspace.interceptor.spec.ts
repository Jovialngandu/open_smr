import { HttpParams, HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { DOMAIN_ENDPOINTS, organizationMembersEndpoint } from '../config/api.config';
import { HeatmapApiResponse, SoaEntry } from '../models/governance.models';
import { mockWorkspaceInterceptor } from './mock-workspace.interceptor';

const SCOPE_ID = '8f4b8400-e29b-41d4-a716-446655440101';

describe('mockWorkspaceInterceptor', () => {
  it('retourne les 25 cases de la matrice du périmètre', async () => {
    const response = await intercept<HeatmapApiResponse>(new HttpRequest('GET', DOMAIN_ENDPOINTS.heatmap, null, { params: scopeParams() }));
    expect(response.body?.matrix).toHaveLength(25);
    expect(response.body?.total_risks).toBe(4);
  });

  it('retourne les 93 mesures de la SoA', async () => {
    const response = await intercept<SoaEntry[]>(new HttpRequest('GET', DOMAIN_ENDPOINTS.soa, null, { params: scopeParams() }));
    expect(response.body).toHaveLength(93);
    expect(response.body?.every((entry) => entry.scope_id === SCOPE_ID)).toBe(true);
  });

  it('filtre les tâches de traitement par périmètre', async () => {
    const response = await intercept<Array<{ risk: string; iso_control: string }>>(new HttpRequest('GET', DOMAIN_ENDPOINTS.treatments, null, { params: scopeParams() }));
    expect(response.body).toHaveLength(3);
    expect(response.body?.every((task) => Boolean(task.risk && task.iso_control))).toBe(true);
  });

  it('isole les membres de chaque organisation', async () => {
    const asteria = await intercept<Array<{ user: { id: number } }>>(new HttpRequest('GET', organizationMembersEndpoint('8f4b8400-e29b-41d4-a716-446655440001')));
    const novacare = await intercept<Array<{ user: { id: number } }>>(new HttpRequest('GET', organizationMembersEndpoint('8f4b8400-e29b-41d4-a716-446655440002')));
    expect(asteria.body?.map((member) => member.user.id)).toEqual([1, 2, 3]);
    expect(novacare.body?.map((member) => member.user.id)).toEqual([4]);
  });
});

function scopeParams(): HttpParams { return new HttpParams().set('scope_id', SCOPE_ID); }
async function intercept<T>(request: HttpRequest<unknown>): Promise<HttpResponse<T>> {
  return firstValueFrom(mockWorkspaceInterceptor(request, () => { throw new Error('Le mock aurait dû intercepter la requête.'); })) as Promise<HttpResponse<T>>;
}
