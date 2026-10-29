import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { SentinelConversation, SentinelMessage, SentinelService } from '../services/sentinel.service';
import { SentinelDrawerComponent } from './sentinel-drawer.component';

describe('SentinelDrawerComponent', () => {
  it('crée et utilise une conversation sans changer de page', () => {
    const id = '11111111-1111-4111-8111-111111111111';
    const conversation: SentinelConversation = { id, title: 'Nouvelle conversation', is_archived: false, created_at: '', updated_at: '', last_activity: '', message_count: 0 };
    const userMessage: SentinelMessage = { id: 'message-1', conversation_id: id, role: 'user', content: 'Bonjour', created_at: '' };
    const assistantMessage: SentinelMessage = { ...userMessage, id: 'message-2', role: 'assistant', content: 'Bonjour !' };
    const service = {
      list: vi.fn(() => of([])), create: vi.fn(() => of(conversation)),
      send: vi.fn(() => of({ conversation_id: id, user_message: userMessage, assistant_message: assistantMessage })),
    };
    TestBed.configureTestingModule({ providers: [{ provide: SentinelService, useValue: service }] });
    TestBed.overrideComponent(SentinelDrawerComponent, { set: { template: '', imports: [] } });
    const page = TestBed.createComponent(SentinelDrawerComponent).componentInstance as unknown as {
      draft: { set(value: string): void; (): string }; send(): void;
      detail: () => { messages: SentinelMessage[] } | null;
    };
    page.draft.set('Bonjour');
    page.send();
    expect(service.create).toHaveBeenCalledOnce();
    expect(service.send).toHaveBeenCalledWith(id, 'Bonjour');
    expect(page.detail()?.messages).toEqual([userMessage, assistantMessage]);
    expect(page.draft()).toBe('');
  });
});
