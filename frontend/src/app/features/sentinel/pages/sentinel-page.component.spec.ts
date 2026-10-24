import { WritableSignal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { SentinelConversation, SentinelConversationDetail, SentinelMessage, SentinelRequestError, SentinelService } from '../services/sentinel.service';
import { SentinelPageComponent } from './sentinel-page.component';

describe('SentinelPageComponent', () => {
  it('garde le message enregistré quand la génération de réponse échoue', () => {
    const id = '11111111-1111-4111-8111-111111111111';
    const conversation: SentinelConversation = {
      id, title: 'Nouvelle conversation', is_archived: false,
      created_at: '2026-10-24T08:00:00Z', updated_at: '2026-10-24T08:00:00Z',
      last_activity: '2026-10-24T08:00:00Z', message_count: 0,
    };
    const detail: SentinelConversationDetail = { ...conversation, messages: [] };
    const saved: SentinelMessage = {
      id: 'message-1', conversation_id: id, role: 'user', content: 'Bonjour', created_at: '2026-10-24T08:01:00Z',
    };
    const service = {
      list: vi.fn(() => of([conversation])),
      get: vi.fn(() => of(detail)),
      send: vi.fn(() => throwError(() => new SentinelRequestError('Sentinel est indisponible.', saved))),
    };
    TestBed.configureTestingModule({ providers: [
      { provide: SentinelService, useValue: service },
      { provide: ActivatedRoute, useValue: { queryParamMap: of(convertToParamMap({ conversation: id })) } },
      { provide: Router, useValue: { navigate: vi.fn() } },
    ] });
    TestBed.overrideComponent(SentinelPageComponent, { set: { template: '', imports: [] } });
    const fixture = TestBed.createComponent(SentinelPageComponent);
    const page = fixture.componentInstance as unknown as {
      draft: WritableSignal<string>; send: () => void; messages: () => SentinelMessage[];
      sendError: () => string; sending: () => boolean;
    };

    page.draft.set('Bonjour');
    page.send();

    expect(service.send).toHaveBeenCalledWith(id, 'Bonjour');
    expect(page.messages()).toEqual([saved]);
    expect(page.draft()).toBe('');
    expect(page.sendError()).toContain('indisponible');
    expect(page.sending()).toBe(false);
  });
});
