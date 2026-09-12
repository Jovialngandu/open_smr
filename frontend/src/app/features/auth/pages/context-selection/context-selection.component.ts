import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';
import { ContextService } from '../../../../core/services/context.service';

@Component({ selector: 'app-context-selection', imports: [ReactiveFormsModule], host: { class: 'context-page' }, templateUrl: './context-selection.component.html' })
export class ContextSelectionComponent {
  protected readonly context = inject(ContextService);
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  protected readonly organizationId = signal(this.context.activeOrganizationId() ?? this.context.organizations()[0]?.organization_id ?? '');
  protected readonly selectedOrganization = computed(() => this.context.organizations().find((organization) => organization.organization_id === this.organizationId()) ?? null);
  protected readonly scopeId = signal(this.context.activeScopeId() ?? this.selectedOrganization()?.scopes?.[0]?.id ?? '');
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly canCreateScope = computed(() => ['ADMIN', 'RSSI'].includes(this.selectedOrganization()?.role ?? ''));
  protected readonly scopeForm = this.fb.nonNullable.group({ name: ['', [Validators.required, Validators.maxLength(255)]], description: [''] });

  protected changeOrganization(event: Event): void {
    const id = (event.target as HTMLSelectElement).value;
    this.organizationId.set(id);
    const organization = this.context.organizations().find((item) => item.organization_id === id);
    this.scopeId.set(organization?.scopes?.[0]?.id ?? '');
    this.error.set('');
  }

  protected continue(): void {
    if (!this.organizationId() || !this.scopeId()) { this.error.set('Choisissez une organisation et un périmètre pour continuer.'); return; }
    this.busy.set(true); this.error.set('');
    this.context.switchContext({ organization_id: this.organizationId(), scope_id: this.scopeId() }).subscribe({ next: () => void this.router.navigateByUrl('/dashboard'), error: () => { this.busy.set(false); this.error.set('Ce contexte n’est pas accessible avec votre compte.'); } });
  }

  protected createScope(): void {
    if (this.scopeForm.invalid) { this.scopeForm.markAllAsTouched(); return; }
    const value = this.scopeForm.getRawValue();
    if (!value.name.trim()) { this.scopeForm.controls.name.setErrors({ required: true }); return; }
    this.busy.set(true); this.error.set('');
    this.context.createScope(this.organizationId(), value.name.trim(), value.description.trim()).subscribe({ next: (scope) => { this.scopeId.set(scope.id); this.scopeForm.reset(); this.busy.set(false); }, error: () => { this.busy.set(false); this.error.set('Le périmètre n’a pas pu être créé.'); } });
  }

  protected logout(): void { this.auth.logout(); }
}
