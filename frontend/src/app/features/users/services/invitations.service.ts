import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';

import { API_CONFIG, DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { UserRole } from '../../../core/models/auth.models';
import { ContextService } from '../../../core/services/context.service';

export interface UserSearchResult {
  id: number | string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface OrganizationInvitation {
  id: string;
  organization: { id: string; name: string };
  invited_user_email: string;
  role: UserRole;
  status: 'PENDING' | 'ACCEPTED' | 'DECLINED';
  expires_at: string;
}

@Injectable({ providedIn: 'root' })
export class InvitationsService {
  private readonly http = inject(HttpClient);
  private readonly context = inject(ContextService);

  searchUsers(query: string): Observable<UserSearchResult[]> {
    return this.http.get<UserSearchResult[]>(`${DOMAIN_ENDPOINTS.users}search/`, {
      params: new HttpParams().set('q', query.trim()),
    }).pipe(catchError((error) => throwError(() => invitationError(error))));
  }

  send(organizationId: string, email: string, role: UserRole): Observable<OrganizationInvitation> {
    if (!organizationId || this.context.activeOrganizationId() !== organizationId) {
      return throwError(() => new Error('Créez ou sélectionnez une organisation avant d’inviter un membre.'));
    }
    if (!['ADMIN', 'RSSI'].includes(this.context.activeRole() ?? '')) {
      return throwError(() => new Error('Seuls les administrateurs et RSSI peuvent inviter un membre.'));
    }
    const normalizedEmail = email.trim().toLowerCase();
    if (normalizedEmail === this.context.profile()?.email.trim().toLowerCase()) {
      return throwError(() => new Error('Vous ne pouvez pas vous inviter vous-même.'));
    }
    return this.http.post<OrganizationInvitation>(`${DOMAIN_ENDPOINTS.organizations}${organizationId}/invitations/`, {
      invited_user_email: normalizedEmail, role,
    }).pipe(catchError((error) => throwError(() => invitationError(error))));
  }

  accept(token: string): Observable<{ detail: string; invitation: OrganizationInvitation }> {
    return this.decide('accept', token);
  }

  decline(token: string): Observable<{ detail: string; invitation: OrganizationInvitation }> {
    return this.decide('decline', token);
  }

  private decide(action: 'accept' | 'decline', token: string): Observable<{ detail: string; invitation: OrganizationInvitation }> {
    return this.http.post<{ detail: string; invitation: OrganizationInvitation }>(`${API_CONFIG.baseUrl}/organizations/invitations/${action}/`, { token })
      .pipe(catchError((error) => throwError(() => invitationError(error))));
  }
}

export function invitationError(error: unknown): Error {
  if (error instanceof HttpErrorResponse) {
    const payload = error.error as Record<string, unknown> | null;
    const detail = payload?.['detail'] ?? payload?.['token'] ?? payload?.['invited_user_email'] ?? payload?.['role'];
    if (typeof detail === 'string') return new Error(detail);
    if (Array.isArray(detail) && detail.length) return new Error(String(detail[0]));
    if (error.status === 404) return new Error('Cette invitation est introuvable ou le lien est incorrect.');
    if (error.status === 403) return new Error('Ce compte ne peut pas utiliser cette invitation. Vérifiez l’adresse e-mail connectée.');
    if (error.status === 0) return new Error('Le serveur est indisponible. Réessayez plus tard.');
  }
  return new Error('Impossible de traiter cette invitation. Réessayez.');
}
