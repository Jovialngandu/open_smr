import { HttpClient } from '@angular/common/http';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';

import { ContextService } from '../../../core/services/context.service';
import { InvitationsService, OrganizationInvitation } from './invitations.service';

describe('InvitationsService', () => {
  it('refuse une invitation sans organisation active', async () => {
    const organizationId = signal<string | null>(null);
    const role = signal<'ADMIN' | null>(null);
    const post = vi.fn();
    TestBed.configureTestingModule({ providers: [
      { provide: HttpClient, useValue: { post } },
      { provide: ContextService, useValue: { activeOrganizationId: organizationId, activeRole: role } },
    ] });
    const service = TestBed.inject(InvitationsService);

    await expect(firstValueFrom(service.send('org-a', 'membre@example.com', 'RISK_OWNER'))).rejects.toThrow('Créez ou sélectionnez une organisation');
    expect(post).not.toHaveBeenCalled();

    organizationId.set('org-a');
    role.set('ADMIN');
    post.mockReturnValue(of({ id: 'inv-1' } as OrganizationInvitation));
    await firstValueFrom(service.send('org-a', 'membre@example.com', 'RISK_OWNER'));
    expect(post).toHaveBeenCalledOnce();
  });
});
