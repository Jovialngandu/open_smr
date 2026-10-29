import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, throwError } from 'rxjs';

import { API_CONFIG } from '../../../core/config/api.config';

export const SENTINEL_CONVERSATIONS_ENDPOINT = `${API_CONFIG.baseUrl}/chat/conversations/`;

export interface SentinelConversation {
  id: string;
  title: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  last_activity: string;
  message_count: number;
}

export interface SentinelMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface SentinelConversationDetail extends Omit<SentinelConversation, 'message_count'> {
  messages: SentinelMessage[];
}

export interface SentinelSendResponse {
  conversation_id: string;
  user_message: SentinelMessage;
  assistant_message?: SentinelMessage | null;
  detail?: string;
}

@Injectable({ providedIn: 'root' })
export class SentinelService {
  private readonly http = inject(HttpClient);

  list(): Observable<SentinelConversation[]> {
    return this.http.get<{ count: number; results: SentinelConversation[] }>(SENTINEL_CONVERSATIONS_ENDPOINT)
      .pipe(map((response) => response.results), catchError((error) => throwError(() => sentinelError(error))));
  }

  create(): Observable<SentinelConversation> {
    return this.http.post<SentinelConversation>(SENTINEL_CONVERSATIONS_ENDPOINT, {})
      .pipe(catchError((error) => throwError(() => sentinelError(error))));
  }

  get(id: string): Observable<SentinelConversationDetail> {
    return this.http.get<SentinelConversationDetail>(`${SENTINEL_CONVERSATIONS_ENDPOINT}${encodeURIComponent(id)}/`)
      .pipe(catchError((error) => throwError(() => sentinelError(error))));
  }

  send(id: string, message: string): Observable<SentinelSendResponse> {
    return this.http.post<SentinelSendResponse>(`${SENTINEL_CONVERSATIONS_ENDPOINT}${encodeURIComponent(id)}/messages/`, { message })
      .pipe(catchError((error) => throwError(() => sentinelError(error))));
  }
}

export class SentinelRequestError extends Error {
  constructor(message: string, readonly savedUserMessage?: SentinelMessage) { super(message); }
}

function sentinelError(error: unknown): SentinelRequestError {
  if (error instanceof HttpErrorResponse) {
    const saved = error.error?.user_message as SentinelMessage | undefined;
    if (error.status === 0) return new SentinelRequestError('Connexion au serveur impossible. Réessayez plus tard.', saved);
    if (error.status === 429) return new SentinelRequestError('Sentinel reçoit trop de demandes. Réessayez dans un instant.', saved);
    if (error.status === 503 || error.status === 504) return new SentinelRequestError(
      saved ? 'Sentinel est momentanément indisponible. Votre message reste dans la conversation.' : 'Sentinel est momentanément indisponible. Réessayez plus tard.', saved,
    );
    if (error.status === 404) return new SentinelRequestError('Cette conversation n’est plus disponible.', saved);
    const detail = error.error?.detail ?? error.error?.message;
    if (typeof detail === 'string') return new SentinelRequestError(detail, saved);
    if (Array.isArray(detail) && detail.length) return new SentinelRequestError(String(detail[0]), saved);
  }
  return new SentinelRequestError('Une erreur est survenue. Réessayez.', undefined);
}
