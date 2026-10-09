import { HttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { UserProfile } from '../models/auth.models';
import { ContextService } from './context.service';
import { TokenStorageService } from './token-storage.service';

describe('ContextService', () => {
  const organizationId = 'organization-a';
  const scopeId = 'scope-a';
  const profile: UserProfile = {
    id: 'user-a', username: 'user.a', email: 'a@example.com', first_name: '', last_name: '', is_active: true,
    roles: [{ organization_id: organizationId, organization_name: 'Organisation A', role: 'ADMIN',
      scopes: [{ id: scopeId, organization_id: organizationId, name: 'Périmètre A', description: '' }] }],
  };
  let context: ContextService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        { provide: HttpClient, useValue: { post: () => of({ access: 'access', refresh: 'refresh' }) } },
        { provide: TokenStorageService, useValue: { claims: () => null, save: () => undefined } },
      ],
    });
    context = TestBed.inject(ContextService);
  });

  it('mémorise le dernier contexte du compte après une bascule réussie', () => {
    context.setProfile(profile);
    context.switchContext({ organization_id: organizationId, scope_id: scopeId }).subscribe();

    expect(context.preferredContext(profile)).toEqual({ organization_id: organizationId, scope_id: scopeId });
    expect(context.preferredContext({ ...profile, id: 'user-b' })).toBeNull();
  });

  it('écarte un périmètre dont l’accès a été retiré', () => {
    localStorage.setItem('opensmr.last_context.user-a', JSON.stringify({ organization_id: organizationId, scope_id: 'ancien-scope' }));

    expect(context.preferredContext(profile)).toBeNull();
    expect(localStorage.getItem('opensmr.last_context.user-a')).toBeNull();
  });
});
