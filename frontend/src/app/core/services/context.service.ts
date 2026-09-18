import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, forkJoin, map, Observable, of, tap } from 'rxjs';

import { AUTH_ENDPOINTS, DOMAIN_ENDPOINTS } from '../config/api.config';
import {
  OrganizationRole,
  ScopeSummary,
  SwitchContextRequest,
  SwitchContextResponse,
  UserProfile,
} from '../models/auth.models';
import { TokenStorageService } from './token-storage.service';

@Injectable({ providedIn: 'root' })
export class ContextService {
  private readonly http = inject(HttpClient);
  private readonly tokens = inject(TokenStorageService);
  private readonly profileState = signal<UserProfile | null>(null);
  private readonly claimsState = signal(this.tokens.claims());

  readonly profile = this.profileState.asReadonly();
  readonly claims = this.claimsState.asReadonly();
  readonly organizations = computed(() => this.profileState()?.roles ?? []);
  readonly activeOrganizationId = computed(() => this.claimsState()?.organization_id ?? null);
  readonly activeScopeId = computed(() => this.claimsState()?.scope_id ?? null);
  readonly activeRole = computed(() => this.claimsState()?.role ?? null);
  readonly activeOrganization = computed<OrganizationRole | null>(() =>
    this.organizations().find((item) => item.organization_id === this.activeOrganizationId()) ?? null,
  );

  setProfile(profile: UserProfile): void {
    this.profileState.set(profile);
  }

  hydrateProfile(profile: UserProfile): Observable<UserProfile> {
    if (!profile.roles.length) return of(profile);

    return forkJoin(profile.roles.map((role) =>
      this.http.get<ScopeSummary[]>(DOMAIN_ENDPOINTS.scopes, {
        params: { organization_id: role.organization_id },
      }).pipe(
        map((scopes) => ({ ...role, scopes })),
        catchError(() => of({ ...role, scopes: [] })),
      ),
    )).pipe(map((roles) => ({ ...profile, roles })));
  }

  syncClaims(): void {
    this.claimsState.set(this.tokens.claims());
  }

  switchContext(context: SwitchContextRequest) {
    return this.http.post<SwitchContextResponse>(AUTH_ENDPOINTS.switchContext, context).pipe(
      tap((response) => {
        this.tokens.save(response);
        this.syncClaims();
      }),
    );
  }

  createScope(organizationId: string, name: string, description: string): Observable<{ id: string; organization_id: string; name: string; description: string }> {
    return this.http.post<{ id: string; organization_id: string; name: string; description: string }>(DOMAIN_ENDPOINTS.scopes, { organization_id: organizationId, name, description }).pipe(
      tap((scope) => this.profileState.update((profile) => profile ? { ...profile, roles: profile.roles.map((role) => role.organization_id === organizationId ? { ...role, scopes: [...role.scopes, scope] } : role) } : profile)),
    );
  }

  createOrganization(name: string, code: string): Observable<{ id: string; name: string; code: string }> {
    return this.http.post<{ id: string; name: string; code: string }>(DOMAIN_ENDPOINTS.organizations, { name, code }).pipe(
      tap((organization) => this.profileState.update((profile) => profile ? {
        ...profile,
        roles: profile.roles.some((role) => role.organization_id === organization.id) ? profile.roles : [...profile.roles, { organization_id: organization.id, organization_name: organization.name, role: 'ADMIN', scopes: [] }],
      } : profile)),
    );
  }

  reset(): void {
    this.profileState.set(null);
    this.claimsState.set(null);
  }
}
