import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { forkJoin, map, Observable, of, tap } from 'rxjs';

import { organizationMembersEndpoint, organizationMemberStatusEndpoint, scopeAccessEndpoint, scopeAccessRemovalEndpoint } from '../../../core/config/api.config';
import { UserRole } from '../../../core/models/auth.models';
import { ManagedUser } from '../../../core/models/governance.models';
import { ContextService } from '../../../core/services/context.service';

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly http = inject(HttpClient);
  private readonly context = inject(ContextService);
  private readonly usersState = signal<ManagedUser[]>([]);
  readonly users = this.usersState.asReadonly();
  fetch(): void {
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId) return;
    const scopeId = this.context.activeScopeId();
    forkJoin({
      members: this.http.get<BackendMemberRole[]>(organizationMembersEndpoint(organizationId)),
      accesses: scopeId ? this.http.get<BackendScopeAccess[]>(scopeAccessEndpoint(scopeId)) : of([]),
    }).pipe(map(({ members, accesses }) => members.map((member) => toManagedUser(member, accesses, scopeId)))).subscribe((users) => this.usersState.set(users));
  }
  assign(userId: number, role: Exclude<UserRole, 'ADMIN'>): Observable<ManagedUser> {
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId) throw new Error('Aucune organisation active.');
    return this.http.post<BackendMemberRole>(organizationMembersEndpoint(organizationId), { user_id: userId, role }).pipe(map((member) => toManagedUser(member, [], this.context.activeScopeId())), tap((created) => this.usersState.update((users) => [...users.filter((user) => user.id !== created.id), created])));
  }
  toggle(user: ManagedUser): void {
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId || !user.role_assignment_id) return;
    this.http.patch<BackendMemberRole>(organizationMemberStatusEndpoint(organizationId, user.role_assignment_id), { is_active: !user.is_active }).pipe(map((member) => toManagedUser(member, [], this.context.activeScopeId()))).subscribe((updated) => this.usersState.update((users) => users.map((item) => item.id === updated.id ? { ...updated, scope_ids: item.scope_ids } : item)));
  }

  setScopeAccess(user: ManagedUser, granted: boolean): void {
    const scopeId = this.context.activeScopeId();
    if (!scopeId) return;
    const endpoint = granted ? scopeAccessEndpoint(scopeId) : scopeAccessRemovalEndpoint(scopeId);
    this.http.post(endpoint, { user_id: Number(user.id) }).subscribe(() =>
      this.usersState.update((users) => users.map((item) => item.id === user.id ? {
        ...item,
        scope_ids: granted ? [...new Set([...item.scope_ids, scopeId])] : item.scope_ids.filter((id) => id !== scopeId),
      } : item)),
    );
  }
}

interface BackendMemberRole {
  id: string;
  user: { id: number | string; username: string; email: string; first_name: string; last_name: string };
  role: ManagedUser['role'];
  is_active: boolean;
}

interface BackendScopeAccess { user: { id: number | string } }

function toManagedUser(member: BackendMemberRole, accesses: BackendScopeAccess[], scopeId: string | null): ManagedUser {
  const fullName = `${member.user.first_name} ${member.user.last_name}`.trim();
  const activeScopeId = accesses.some((access) => String(access.user.id) === String(member.user.id));
  return { id: String(member.user.id), role_assignment_id: member.id, name: fullName || member.user.username, email: member.user.email, role: member.role, is_active: member.is_active, scope_ids: activeScopeId && scopeId ? [scopeId] : [] };
}
