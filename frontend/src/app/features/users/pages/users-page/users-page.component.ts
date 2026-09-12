import { Component, inject, signal } from '@angular/core';
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
  protected readonly form = this.fb.nonNullable.group({ name: ['', Validators.required], email: ['', [Validators.required, Validators.email]], role: ['RISK_OWNER' as Exclude<UserRole, 'ADMIN'>, Validators.required] });
  constructor() { this.service.fetch(); }
  protected submit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue(); const scopeId = this.context.activeScopeId(); this.submitError.set('');
    this.service.create({ ...value, name: value.name.trim(), email: value.email.trim().toLowerCase(), is_active: true, scope_ids: scopeId ? [scopeId] : [] }).subscribe({ next: () => { this.feedback.set(`L’invitation de ${value.name.trim()} a bien été créée.`); this.modalOpen.set(false); this.form.reset({ name: '', email: '', role: 'RISK_OWNER' }); }, error: () => this.submitError.set('L’invitation n’a pas pu être créée.') });
  }
}
