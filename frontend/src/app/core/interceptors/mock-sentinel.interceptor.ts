import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG } from '../config/api.config';
import {
  SENTINEL_CONVERSATIONS_ENDPOINT,
  SentinelConversation,
  SentinelConversationDetail,
  SentinelMessage,
} from '../../features/sentinel/services/sentinel.service';

type StoredConversation = SentinelConversationDetail;

export function removeMockSentinelUser(userId: string): void {
  localStorage.removeItem(storageKey(userId));
}

export const mockSentinelInterceptor: HttpInterceptorFn = (request, next) => {
  if (!API_CONFIG.useMocks || !request.url.startsWith(SENTINEL_CONVERSATIONS_ENDPOINT)) return next(request);
  const userId = mockUserId(request.headers.get('Authorization'));
  if (!userId) return failure(401, 'Connectez-vous pour accéder à Sentinel.');
  const conversations = readConversations(userId);
  const suffix = request.url.slice(SENTINEL_CONVERSATIONS_ENDPOINT.length);

  if (!suffix && request.method === 'GET') {
    const results = conversations.map(({ messages, ...conversation }) => ({ ...conversation, message_count: messages.length }))
      .sort((a, b) => b.last_activity.localeCompare(a.last_activity));
    return success({ count: results.length, results });
  }

  if (!suffix && request.method === 'POST') {
    const title = String((request.body as { title?: string } | null)?.title ?? '').trim().slice(0, 200) || 'Nouvelle conversation';
    const now = new Date().toISOString();
    const conversation: StoredConversation = {
      id: crypto.randomUUID(), title, is_archived: false, created_at: now,
      updated_at: now, last_activity: now, messages: [],
    };
    writeConversations(userId, [conversation, ...conversations]);
    const { messages: _messages, ...summary } = conversation;
    return success<SentinelConversation>({ ...summary, message_count: 0 }, 201);
  }

  const match = suffix.match(/^([0-9a-f-]{36})\/(messages\/)?$/i);
  if (!match) return next(request);
  const conversation = conversations.find((item) => item.id === match[1]);
  if (!conversation) return failure(404, 'Cette conversation est introuvable.');

  if (!match[2] && request.method === 'GET') return success(conversation);

  if (match[2] && request.method === 'POST') {
    const message = String((request.body as { message?: string } | null)?.message ?? '').trim();
    if (!message || message.length > 2000) return failure(400, 'Le message doit contenir entre 1 et 2 000 caractères.');
    const now = new Date().toISOString();
    if (conversation.title === 'Nouvelle conversation') conversation.title = message.slice(0, 80);
    const userMessage: SentinelMessage = {
      id: crypto.randomUUID(), conversation_id: conversation.id, role: 'user', content: message, created_at: now,
    };
    const assistantMessage: SentinelMessage = {
      id: crypto.randomUUID(), conversation_id: conversation.id, role: 'assistant',
      content: 'Réponse de démonstration : Sentinel sera disponible lorsque le service IA sera connecté. Vos conversations restent consultables dans ce navigateur.',
      created_at: new Date(Date.now() + 1).toISOString(),
    };
    conversation.messages.push(userMessage, assistantMessage);
    conversation.last_activity = assistantMessage.created_at;
    conversation.updated_at = assistantMessage.created_at;
    writeConversations(userId, conversations);
    return success({ conversation_id: conversation.id, user_message: userMessage, assistant_message: assistantMessage }, 201);
  }

  return next(request);
};

function mockUserId(authorization: string | null): string | null {
  if (!authorization) return null;
  try {
    const payload = authorization.replace(/^Bearer\s+/i, '').split('.')[1];
    return String(JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/'))).user_id ?? '') || null;
  } catch { return null; }
}

function storageKey(userId: string): string { return `opensmr.mock_sentinel.${userId}`; }

function readConversations(userId: string): StoredConversation[] {
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey(userId)) ?? '[]') as unknown;
    return Array.isArray(stored) ? stored as StoredConversation[] : [];
  } catch { return []; }
}

function writeConversations(userId: string, conversations: StoredConversation[]): void {
  localStorage.setItem(storageKey(userId), JSON.stringify(conversations));
}

function success<T>(body: T, status = 200) {
  return of(new HttpResponse({ body, status })).pipe(delay(API_CONFIG.mockDelayMs));
}

function failure(status: number, detail: string) {
  return throwError(() => new HttpErrorResponse({ status, error: { detail } }));
}
