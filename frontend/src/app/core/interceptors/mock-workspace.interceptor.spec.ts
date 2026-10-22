import { HttpParams, HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { API_CONFIG, DOMAIN_ENDPOINTS, organizationMembersEndpoint } from '../config/api.config';
import { riskControlSuggestionsEndpoint } from '../../features/treatments/services/control-suggestions.service';
import { HeatmapApiResponse, SoaEntry, SoaVersion } from '../models/governance.models';
import { mockWorkspaceInterceptor } from './mock-workspace.interceptor';

const SCOPE_ID = '8f4b8400-e29b-41d4-a716-446655440101';

describe('mockWorkspaceInterceptor', () => {
  beforeAll(() => Object.defineProperty(API_CONFIG, 'useMocks', { value: true, configurable: true }));
  afterAll(() => Object.defineProperty(API_CONFIG, 'useMocks', { value: false, configurable: true }));
  it('retourne les 25 cases de la matrice du périmètre', async () => {
    const response = await intercept<HeatmapApiResponse>(new HttpRequest('GET', DOMAIN_ENDPOINTS.heatmap, null, { params: scopeParams() }));
    expect(response.body?.matrix).toHaveLength(25);
    expect(response.body?.total_risks).toBe(4);
  });

  it('classe les mesures suggérées selon le risque et l’action saisie', async () => {
    const response = await intercept<Array<{ id: string; code: string }>>(new HttpRequest('GET', riskControlSuggestionsEndpoint('risk-001'), null, { params: new HttpParams().set('context', 'Installer des sauvegardes') }));
    expect(response.body?.[0].code).toBe('A.8.13');
    expect(response.body?.[0].id).toBeTruthy();
  });

  it('retourne les 93 mesures de la SoA', async () => {
    const response = await intercept<Array<SoaEntry & { scope: string }>>(new HttpRequest('GET', DOMAIN_ENDPOINTS.soaEntries, null, { params: scopeParams() }));
    expect(response.body).toHaveLength(93);
    expect(response.body?.every((entry) => entry.scope === SCOPE_ID)).toBe(true);
  });

  it('conserve le contenu figé d’une version après une modification de la SoA courante', async () => {
    const created = await intercept<SoaVersion>(new HttpRequest('POST', DOMAIN_ENDPOINTS.soaVersions, { scope_id: SCOPE_ID, title: 'Instantané de test' }));
    const version = created.body!;
    expect(version.snapshot_data).toHaveLength(93);
    const first = version.snapshot_data[0];
    await intercept(new HttpRequest('PATCH', `${DOMAIN_ENDPOINTS.soaEntries}${first.entry_id}/`, { is_applicable: !first.is_applicable, justification: 'Justification modifiée après l’instantané' }));
    const versions = await intercept<SoaVersion[]>(new HttpRequest('GET', DOMAIN_ENDPOINTS.soaVersions, null, { params: scopeParams() }));
    const saved = versions.body?.find((item) => item.id === version.id);
    expect(saved?.snapshot_data[0]).toEqual(first);
  });

  it('filtre les tâches de traitement par risque, comme le backend', async () => {
    const response = await intercept<Array<{ risk: string; iso_control: string }>>(new HttpRequest('GET', DOMAIN_ENDPOINTS.treatments, null, { params: new HttpParams().set('risk_id', 'risk-001') }));
    expect(response.body).toHaveLength(1);
    expect(response.body?.[0].risk).toBe('risk-001');
    expect(response.body?.every((task) => Boolean(task.risk && task.iso_control))).toBe(true);
  });

  it('isole les membres de chaque organisation', async () => {
    const asteria = await intercept<Array<{ user: { id: number } }>>(new HttpRequest('GET', organizationMembersEndpoint('8f4b8400-e29b-41d4-a716-446655440001')));
    const novacare = await intercept<Array<{ user: { id: number } }>>(new HttpRequest('GET', organizationMembersEndpoint('8f4b8400-e29b-41d4-a716-446655440002')));
    expect(asteria.body?.map((member) => member.user.id)).toEqual([1, 2, 3]);
    expect(novacare.body?.map((member) => member.user.id)).toEqual([4]);
  });

  it('supprime une tâche de traitement sans la conserver dans la liste', async () => {
    const created = await intercept<{ id: string }>(new HttpRequest('POST', DOMAIN_ENDPOINTS.treatments, {
      risk: 'risk-001', iso_control: 'control-001', assignee: '2', title: 'Tâche temporaire', description: '', due_date: '2026-12-01',
    }, { params: new HttpParams().set('scope_id', SCOPE_ID).set('risk_code', 'RSK-PAY-001') }));
    expect((await intercept(new HttpRequest('DELETE', `${DOMAIN_ENDPOINTS.treatments}${created.body?.id}/`))).status).toBe(204);
    const remaining = await intercept<Array<{ id: string }>>(new HttpRequest('GET', DOMAIN_ENDPOINTS.treatments, null, { params: new HttpParams().set('risk_id', 'risk-001') }));
    expect(remaining.body?.some((task) => task.id === created.body?.id)).toBe(false);
  });
});

function scopeParams(): HttpParams { return new HttpParams().set('scope_id', SCOPE_ID); }
async function intercept<T>(request: HttpRequest<unknown>): Promise<HttpResponse<T>> {
  return firstValueFrom(mockWorkspaceInterceptor(request, () => { throw new Error('Le mock aurait dû intercepter la requête.'); })) as Promise<HttpResponse<T>>;
}
