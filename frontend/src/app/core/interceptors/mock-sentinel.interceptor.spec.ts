import { HttpHeaders, HttpRequest, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { API_CONFIG } from '../config/api.config';
import { SENTINEL_CONVERSATIONS_ENDPOINT, SentinelConversation, SentinelConversationDetail } from '../../features/sentinel/services/sentinel.service';
import { mockSentinelInterceptor, removeMockSentinelUser } from './mock-sentinel.interceptor';

describe('mockSentinelInterceptor', () => {
  const originalMocks = API_CONFIG.useMocks;
  beforeEach(() => {
    localStorage.clear();
    Object.defineProperty(API_CONFIG, 'useMocks', { value: true, configurable: true });
  });
  afterEach(() => Object.defineProperty(API_CONFIG, 'useMocks', { value: originalMocks, configurable: true }));

  const request = (method: string, url: string, userId: string, body?: unknown) => {
    const payload = btoa(JSON.stringify({ user_id: userId }));
    return new HttpRequest(method, url, body ?? null, { headers: new HttpHeaders({ Authorization: `Bearer header.${payload}.signature` }) });
  };
  const intercept = <T>(input: HttpRequest<unknown>) => firstValueFrom(mockSentinelInterceptor(input, () => {
    throw new Error('Le mock aurait dû intercepter la requête.');
  })) as Promise<HttpResponse<T>>;

  it('conserve les conversations après rechargement et les isole par compte', async () => {
    const created = await intercept<SentinelConversation>(request('POST', SENTINEL_CONVERSATIONS_ENDPOINT, 'user-a', {}));
    expect(created.status).toBe(201);
    const id = created.body!.id;
    const sent = await intercept<{ assistant_message: { role: string } }>(request('POST', `${SENTINEL_CONVERSATIONS_ENDPOINT}${id}/messages/`, 'user-a', { message: 'Comment préparer un audit ?' }));
    expect(sent.body?.assistant_message.role).toBe('assistant');

    const reopened = await intercept<SentinelConversationDetail>(request('GET', `${SENTINEL_CONVERSATIONS_ENDPOINT}${id}/`, 'user-a'));
    expect(reopened.body?.messages.map((message) => message.role)).toEqual(['user', 'assistant']);
    const list = await intercept<{ count: number; results: SentinelConversation[] }>(request('GET', SENTINEL_CONVERSATIONS_ENDPOINT, 'user-a'));
    expect(list.body?.results[0].title).toBe('Comment préparer un audit ?');

    const otherList = await intercept<{ count: number }>(request('GET', SENTINEL_CONVERSATIONS_ENDPOINT, 'user-b'));
    expect(otherList.body?.count).toBe(0);
    await expect(intercept(request('GET', `${SENTINEL_CONVERSATIONS_ENDPOINT}${id}/`, 'user-b'))).rejects.toMatchObject({ status: 404 });

    removeMockSentinelUser('user-a');
    const afterDeletion = await intercept<{ count: number }>(request('GET', SENTINEL_CONVERSATIONS_ENDPOINT, 'user-a'));
    expect(afterDeletion.body?.count).toBe(0);
  });
});
