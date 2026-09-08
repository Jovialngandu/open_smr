import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { tap } from 'rxjs';

import { AUTH_ENDPOINTS } from '../config/api.config';
import {
  OrganizationRole,
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

  reset(): void {
    this.profileState.set(null);
    this.claimsState.set(null);
  }
}
