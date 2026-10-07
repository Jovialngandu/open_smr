import { Component, computed, inject, signal } from '@angular/core';
import { LucideShieldCheck, LucideChevronDown, LucidePlus, LucideSettings, LucideX } from '@lucide/angular';
import { HttpErrorResponse } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { finalize, switchMap } from 'rxjs';

import { AuthService } from '../../../core/services/auth.service';
import { ContextService } from '../../../core/services/context.service';

@Component({
  selector: 'app-topbar',
  imports: [RouterLink, RouterLinkActive, ReactiveFormsModule, LucideShieldCheck, LucideChevronDown, LucidePlus, LucideSettings, LucideX],
  templateUrl: './topbar.component.html',
})
export class TopbarComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
  private readonly fb = inject(FormBuilder);
  protected readonly switching = signal(false);
  protected readonly creatingScope = signal(false);
  protected readonly creatingOrganization = signal(false);
  protected readonly scopeModalOpen = signal(false);
  protected readonly organizationModalOpen = signal(false);
  protected readonly scopeError = signal('');
  protected readonly organizationError = signal('');
  protected readonly canCreateScope = computed(() => ['ADMIN', 'RSSI'].includes(this.context.activeRole() ?? ''));
  protected readonly scopeForm = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    description: [''],
  });
  protected readonly organizationForm = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    description: [''],
    scopeName: ['', [Validators.required, Validators.maxLength(255)]],
    scopeDescription: [''],
  });
  protected readonly contextError = signal('');
  protected readonly menuOpen = signal(false);
  protected readonly initials = computed(() => {
    const user = this.auth.user();
    return `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? user?.username?.[0] ?? ''}`.toUpperCase();
  });

  protected changeOrganization(event: Event): void {
    const organizationId = (event.target as HTMLSelectElement).value;
    const organization = this.context.organizations().find(
      (item) => item.organization_id === organizationId,
    );
    this.applyContext(organizationId, organization?.scopes?.[0]?.id ?? null);
  }

  protected changeScope(event: Event): void {
    const scopeId = (event.target as HTMLSelectElement).value || null;
    const organizationId = this.context.activeOrganizationId();
    if (organizationId) this.applyContext(organizationId, scopeId);
  }

  protected logout(): void {
    this.menuOpen.set(false);
    this.auth.logout();
  }

  protected closeScopeModal(): void {
    if (this.creatingScope()) return;
    this.scopeModalOpen.set(false);
    this.scopeError.set('');
    this.scopeForm.reset();
  }

  protected openOrganizationModal(): void {
    this.menuOpen.set(false);
    this.organizationError.set('');
    this.organizationModalOpen.set(true);
  }

  protected closeOrganizationModal(): void {
    if (this.creatingOrganization()) return;
    this.organizationModalOpen.set(false);
    this.organizationError.set('');
    this.organizationForm.reset();
  }

  protected createOrganization(): void {
    if (this.creatingOrganization()) return;
    const controls = this.organizationForm.controls;
    if (this.organizationForm.invalid || !controls.name.value.trim() || !controls.scopeName.value.trim()) {
      if (!controls.name.value.trim()) controls.name.setErrors({ required: true });
      if (!controls.scopeName.value.trim()) controls.scopeName.setErrors({ required: true });
      this.organizationForm.markAllAsTouched();
      return;
    }

    const value = this.organizationForm.getRawValue();
    this.organizationError.set('');
    this.creatingOrganization.set(true);
    this.context.createOrganization(value.name.trim(), value.description.trim()).pipe(
      switchMap((organization) => this.context.switchContext({ organization_id: organization.id, scope_id: null }).pipe(
        switchMap(() => this.context.createScope(organization.id, value.scopeName.trim(), value.scopeDescription.trim())),
        switchMap((scope) => this.context.switchContext({ organization_id: organization.id, scope_id: scope.id })),
      )),
      finalize(() => this.creatingOrganization.set(false)),
    ).subscribe({
      next: () => {
        this.organizationModalOpen.set(false);
        this.organizationForm.reset();
      },
      error: (error: unknown) => {
        const message = error instanceof HttpErrorResponse
          ? error.error?.name ?? error.error?.detail
          : null;
        this.organizationError.set(typeof message === 'string'
          ? message
          : Array.isArray(message) ? String(message[0]) : "La création de l'organisation a échoué. Réessayez.");
      },
    });
  }

  protected createScope(): void {
    const organizationId = this.context.activeOrganizationId();
    if (!organizationId || !this.canCreateScope() || this.creatingScope()) return;
    if (this.scopeForm.invalid || !this.scopeForm.controls.name.value.trim()) {
      this.scopeForm.controls.name.setErrors({ required: true });
      this.scopeForm.markAllAsTouched();
      return;
    }
    const { name, description } = this.scopeForm.getRawValue();
    this.scopeError.set('');
    this.creatingScope.set(true);
    this.context.createScope(organizationId, name.trim(), description.trim()).pipe(
      finalize(() => this.creatingScope.set(false)),
    ).subscribe({
      next: (scope) => {
        this.scopeModalOpen.set(false);
        this.scopeForm.reset();
        this.switching.set(true);
        this.context.switchContext({ organization_id: organizationId, scope_id: scope.id }).pipe(
          finalize(() => this.switching.set(false)),
        ).subscribe({ error: () => this.contextError.set('Le périmètre a été créé, mais la bascule a échoué. Sélectionnez-le dans la liste.') });
      },
      error: (error: unknown) => {
        const message = error instanceof HttpErrorResponse ? error.error?.name ?? error.error?.detail : null;
        this.scopeError.set(typeof message === 'string' ? message : Array.isArray(message) ? String(message[0]) : 'La création du périmètre a échoué. Réessayez.');
      },
    });
  }

  private applyContext(organizationId: string, scopeId: string | null): void {
    this.contextError.set('');
    this.switching.set(true);
    this.context.switchContext({ organization_id: organizationId, scope_id: scopeId }).pipe(
      finalize(() => this.switching.set(false)),
    ).subscribe({
      error: () => this.contextError.set('Le changement de contexte a échoué. Réessayez.'),
    });
  }
}
