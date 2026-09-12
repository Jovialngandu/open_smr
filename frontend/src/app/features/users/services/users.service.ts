import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { map, Observable, tap } from 'rxjs';

import { organizationMembersEndpoint, organizationMemberStatusEndpoint } from '../../../core/config/api.config';
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
    this.http.get<BackendMemberRole[]>(organizationMembersEndpoint(organizationId)).pipe(map((members) => members.map(toManagedUser))).subscribe((users) => this.usersState.set(users));
  }
  assign(userId: number, role: Exclude<UserRole, 'ADMIN'>): Observable<ManagedUser> {
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId) throw new Error('Aucune organisation active.');
    return this.http.post<BackendMemberRole>(organizationMembersEndpoint(organizationId), { user_id: userId, role }).pipe(map(toManagedUser), tap((created) => this.usersState.update((users) => [...users.filter((user) => user.id !== created.id), created])));
  }
  toggle(user: ManagedUser): void {
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId || !user.role_assignment_id) return;
    this.http.patch<BackendMemberRole>(organizationMemberStatusEndpoint(organizationId, user.role_assignment_id), { is_active: !user.is_active }).pipe(map(toManagedUser)).subscribe((updated) => this.usersState.update((users) => users.map((item) => item.id === updated.id ? updated : item)));
  }
}

interface BackendMemberRole {
  id: string;
  user: { id: number | string; username: string; email: string; first_name: string; last_name: string };
  role: ManagedUser['role'];
  is_active: boolean;
}

function toManagedUser(member: BackendMemberRole): ManagedUser {
  const fullName = `${member.user.first_name} ${member.user.last_name}`.trim();
  return { id: String(member.user.id), role_assignment_id: member.id, name: fullName || member.user.username, email: member.user.email, role: member.role, is_active: member.is_active, scope_ids: [] };
}
