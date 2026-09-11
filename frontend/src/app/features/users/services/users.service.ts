import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { ManagedUser } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly http = inject(HttpClient);
  private readonly usersState = signal<ManagedUser[]>([]);
  readonly users = this.usersState.asReadonly();
  fetch(): void { this.http.get<ManagedUser[]>(DOMAIN_ENDPOINTS.users).subscribe((users) => this.usersState.set(users)); }
  create(payload: Omit<ManagedUser, 'id'>): Observable<ManagedUser> { return this.http.post<ManagedUser>(DOMAIN_ENDPOINTS.users, payload).pipe(tap((created) => this.usersState.update((users) => [...users, created]))); }
  toggle(user: ManagedUser): void { this.http.patch<ManagedUser>(`${DOMAIN_ENDPOINTS.users}${user.id}/`, { is_active: !user.is_active }).subscribe((updated) => this.usersState.update((users) => users.map((item) => item.id === updated.id ? updated : item))); }
}
