import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { UserRole } from '../../../../core/models/auth.models';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { ContextService } from '../../../../core/services/context.service';
import { UsersService } from '../../services/users.service';

@Component({ selector: 'app-users-page', imports: [TopbarComponent, ReactiveFormsModule], templateUrl: './users-page.component.html' })
export class UsersPageComponent {
  protected readonly service = inject(UsersService);
  protected readonly context = inject(ContextService);
  private readonly fb = inject(FormBuilder);
  protected readonly modalOpen = signal(false);
  protected readonly feedback = signal('');
  protected readonly submitError = signal('');
  protected readonly canManageRoles = computed(() => this.context.activeRole() === 'ADMIN');
  protected readonly form = this.fb.nonNullable.group({ userId: ['', [Validators.required, Validators.pattern(/^\d+$/)]], role: ['RISK_OWNER' as Exclude<UserRole, 'ADMIN'>, Validators.required] });
  constructor() { this.service.fetch(); }
  protected submit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue(); this.submitError.set('');
    this.service.assign(Number(value.userId), value.role).subscribe({ next: (user) => { this.feedback.set(`${user.name} a bien été affecté à l’organisation.`); this.modalOpen.set(false); this.form.reset({ userId: '', role: 'RISK_OWNER' }); }, error: () => this.submitError.set('L’affectation n’a pas pu être enregistrée. Vérifiez que le compte existe déjà.') });
  }
}
