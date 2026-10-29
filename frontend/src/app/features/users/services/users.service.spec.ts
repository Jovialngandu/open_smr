import { HttpClient } from '@angular/common/http';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { vi } from 'vitest';

import { ManagedUser } from '../../../core/models/governance.models';
import { ContextService } from '../../../core/services/context.service';
import { UsersService } from './users.service';

describe('UsersService', () => {
  it('empêche de modifier ses propres droits ou accès', async () => {
    const post = vi.fn();
    const patch = vi.fn();
    TestBed.configureTestingModule({ providers: [
      { provide: HttpClient, useValue: { post, patch } },
      { provide: ContextService, useValue: {
        profile: signal({ id: 23 }), activeOrganizationId: signal('org-a'), activeScopeId: signal('scope-a'),
      } },
    ] });
    const service = TestBed.inject(UsersService);
    const self: ManagedUser = {
      id: '23', role_assignment_id: 'role-23', name: 'Moi', email: 'moi@example.com',
      role: 'RSSI', is_active: true, scope_ids: ['scope-a'],
    };

    expect(service.isCurrentUser(self)).toBe(true);
    await expect(firstValueFrom(service.assign(23, 'RISK_OWNER'))).rejects.toThrow('vos propres droits');
    service.changeRole(self, 'RISK_OWNER');
    service.toggle(self);
    service.setScopeAccess(self, false);
    expect(post).not.toHaveBeenCalled();
    expect(patch).not.toHaveBeenCalled();
  });
});
