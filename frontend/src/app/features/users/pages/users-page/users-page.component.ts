import { Component, computed, effect, inject, signal } from '@angular/core';
import { LucidePlus, LucideCheck, LucideX, LucideCircleAlert } from '@lucide/angular';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, debounceTime, distinctUntilChanged, of, Subject, switchMap, tap } from 'rxjs';

import { UserRole } from '../../../../core/models/auth.models';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { ContextService } from '../../../../core/services/context.service';
import { InvitationsService, UserSearchResult } from '../../services/invitations.service';
import { UsersService } from '../../services/users.service';

@Component({ selector: 'app-users-page', imports: [TopbarComponent, ReactiveFormsModule, LucidePlus, LucideCheck, LucideX, LucideCircleAlert], templateUrl: './users-page.component.html', styleUrl: './users-page.component.scss' })
export class UsersPageComponent {
  protected readonly service = inject(UsersService);
  protected readonly context = inject(ContextService);
  private readonly invitations = inject(InvitationsService);
  private readonly fb = inject(FormBuilder);
  private readonly searchTerms = new Subject<string>();
  protected readonly modalOpen = signal(false);
  protected readonly feedback = signal('');
  protected readonly submitError = signal('');
  protected readonly searchError = signal('');
  protected readonly searching = signal(false);
  protected readonly sending = signal(false);
  protected readonly suggestions = signal<UserSearchResult[]>([]);
  protected readonly canInvite = computed(() => !!this.context.activeOrganizationId() && ['ADMIN', 'RSSI'].includes(this.context.activeRole() ?? ''));
  protected readonly canManageRoles = computed(() => this.context.activeRole() === 'ADMIN');
  protected isSelfEmail(email: string): boolean {
    const currentEmail = this.context.profile()?.email;
    return !!currentEmail && email.trim().toLowerCase() === currentEmail.trim().toLowerCase();
  }
  protected readonly form = this.fb.nonNullable.group({ email: ['', [Validators.required, Validators.email]], role: ['RISK_OWNER' as UserRole, Validators.required] });
  constructor() {
    effect(() => { this.context.activeOrganizationId(); this.context.activeScopeId(); this.feedback.set(''); this.closeModal(); this.service.fetch(); });
    this.searchTerms.pipe(
      debounceTime(250), distinctUntilChanged(),
      switchMap((query) => {
        if (query.trim().length < 2) { this.searching.set(false); return of([]); }
        this.searching.set(true);
        this.searchError.set('');
        return this.invitations.searchUsers(query).pipe(
          catchError((error: Error) => { this.searchError.set(error.message); return of([]); }),
          tap(() => this.searching.set(false)),
        );
      }),
      takeUntilDestroyed(),
    ).subscribe((users) => this.suggestions.set(users.filter((user) => !this.isSelfEmail(user.email))));
  }
  protected openModal(): void {
    if (!this.canInvite()) return;
    this.submitError.set('');
    this.modalOpen.set(true);
  }
  protected closeModal(): void { this.modalOpen.set(false); this.suggestions.set([]); this.searchError.set(''); this.form.reset({ email: '', role: 'RISK_OWNER' }); }
  protected onEmailInput(event: Event): void { const value = (event.target as HTMLInputElement).value; this.form.controls.email.setValue(value); this.searchTerms.next(value); }
  protected chooseUser(user: UserSearchResult): void { if (this.isSelfEmail(user.email)) return; this.form.controls.email.setValue(user.email); this.suggestions.set([]); this.searchTerms.next(''); }
  protected submit(): void {
    if (!this.canInvite() || this.sending()) return;
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId) { this.submitError.set('Choisissez une organisation avant d’inviter un membre.'); return; }
    const { email, role } = this.form.getRawValue();
    if (this.isSelfEmail(email)) { this.submitError.set('Vous ne pouvez pas vous inviter vous-même.'); return; }
    this.submitError.set(''); this.sending.set(true);
    this.invitations.send(organizationId, email, role).subscribe({
      next: () => { this.sending.set(false); this.closeModal(); this.feedback.set(`Invitation envoyée à ${email.trim()}.`); },
      error: (error: Error) => { this.sending.set(false); this.submitError.set(error.message); },
    });
  }
}
