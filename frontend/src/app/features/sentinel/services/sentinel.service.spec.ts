import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import {
  SENTINEL_CONVERSATIONS_ENDPOINT, SentinelConversation, SentinelConversationDetail,
  SentinelMessage, SentinelRequestError, SentinelService,
} from './sentinel.service';

describe('SentinelService', () => {
  let service: SentinelService;
  let http: HttpTestingController;
  const id = '11111111-1111-4111-8111-111111111111';
  const conversation: SentinelConversation = {
    id, title: 'Audit SI', is_archived: false, created_at: '2026-10-24T08:00:00Z',
    updated_at: '2026-10-24T08:00:00Z', last_activity: '2026-10-24T08:00:00Z', message_count: 0,
  };
  const userMessage: SentinelMessage = {
    id: 'message-1', conversation_id: id, role: 'user', content: 'Bonjour', created_at: '2026-10-24T08:01:00Z',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(SentinelService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('respecte le contrat Django pour lister, créer et ouvrir une conversation', async () => {
    const list = firstValueFrom(service.list());
    http.expectOne(SENTINEL_CONVERSATIONS_ENDPOINT).flush({ count: 1, results: [conversation] });
    expect(await list).toEqual([conversation]);

    const create = firstValueFrom(service.create());
    const createRequest = http.expectOne(SENTINEL_CONVERSATIONS_ENDPOINT);
    expect(createRequest.request.method).toBe('POST');
    expect(createRequest.request.body).toEqual({});
    createRequest.flush(conversation, { status: 201, statusText: 'Created' });
    expect((await create).id).toBe(id);

    const detail: SentinelConversationDetail = { ...conversation, messages: [userMessage] };
    const opened = firstValueFrom(service.get(id));
    http.expectOne(`${SENTINEL_CONVERSATIONS_ENDPOINT}${id}/`).flush(detail);
    expect((await opened).messages).toEqual([userMessage]);
  });

  it('envoie uniquement le message courant et conserve le message enregistré lors d’un échec IA', async () => {
    const sent = firstValueFrom(service.send(id, 'Bonjour'));
    const request = http.expectOne(`${SENTINEL_CONVERSATIONS_ENDPOINT}${id}/messages/`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ message: 'Bonjour' });
    request.flush({ conversation_id: id, user_message: userMessage, detail: 'Service indisponible' }, { status: 503, statusText: 'Service Unavailable' });

    await expect(sent).rejects.toMatchObject({ savedUserMessage: userMessage });
  });
});
