import { Component, computed, effect, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideBell, LucideCheck, LucideClock3, LucideGlobe2, LucidePalette, LucideUserRound } from '@lucide/angular';
import { Router } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { AppTheme, SettingsService } from '../../services/settings.service';

@Component({
  selector: 'app-settings-page',
  imports: [ReactiveFormsModule, TopbarComponent, LucideBell, LucideCheck, LucideClock3, LucideGlobe2, LucidePalette, LucideUserRound],
  templateUrl: './settings-page.component.html',
})
export class SettingsPageComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
  protected readonly service = inject(SettingsService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  protected readonly feedback = signal('');
  protected readonly submitError = signal('');
  protected readonly organizationConfirmation = signal('');
  protected readonly accountConfirmation = signal('');
  protected readonly deletingOrganization = signal(false);
  protected readonly deletingAccount = signal(false);
  protected readonly deletionError = signal('');
  protected readonly organizationName = computed(() => this.context.activeOrganization()?.organization_name ?? '');
  protected readonly themes: Array<{ value: AppTheme; label: string; description: string }> = [
    { value: 'LIGHT', label: 'Clair', description: 'Fond clair en permanence' },
    { value: 'DARK', label: 'Sombre', description: 'Fond sombre en permanence' },
    { value: 'SYSTEM', label: 'Système', description: 'Suit le réglage de votre appareil' },
  ];
  protected readonly timezones = [
    { value: 'Africa/Kinshasa', label: 'Kinshasa (UTC+1)' },
    { value: 'Europe/Paris', label: 'Paris' },
    { value: 'Africa/Douala', label: 'Douala (UTC+1)' },
    { value: 'Africa/Abidjan', label: 'Abidjan (UTC)' },
    { value: 'UTC', label: 'UTC' },
  ];
  protected readonly form = this.fb.nonNullable.group({
    language: ['fr', Validators.required],
    theme: ['LIGHT' as AppTheme, Validators.required],
    timezone: ['Africa/Kinshasa', Validators.required],
    emailNotifications: [true],
  });

  constructor() {
    effect(() => this.service.loadEmailLogs(this.context.activeOrganizationId()));
    this.form.disable();
    this.service.load().subscribe({
      next: (preferences) => {
        this.form.reset({
          language: preferences.language,
          theme: preferences.theme,
          timezone: preferences.timezone,
          emailNotifications: preferences.email_notifications,
        });
        this.form.enable();
        this.form.markAsPristine();
      },
      error: (error: Error) => this.submitError.set(error.message),
    });
  }

  protected changeTheme(theme: AppTheme): void {
    this.service.applyTheme(theme);
    localStorage.setItem('opensmr.theme', theme);
    this.feedback.set('');
    this.submitError.set('');
    this.service.save({ theme }).subscribe({
      next: () => {
        this.form.controls.theme.markAsPristine();
        this.feedback.set('Le thème a été enregistré.');
      },
      error: (error: Error) => {
        const previousTheme = this.service.preferences()?.theme ?? 'LIGHT';
        this.form.controls.theme.setValue(previousTheme);
        localStorage.setItem('opensmr.theme', previousTheme);
        this.service.applyTheme(previousTheme);
        this.submitError.set(error.message);
      },
    });
  }

  protected submit(): void {
    if (this.form.invalid || this.service.saving()) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.feedback.set('');
    this.submitError.set('');
    this.service.save({
      language: value.language,
      theme: value.theme,
      timezone: value.timezone,
      email_notifications: value.emailNotifications,
    }).subscribe({
      next: () => {
        this.feedback.set('Vos préférences ont été enregistrées.');
        this.form.markAsPristine();
      },
      error: (error: Error) => this.submitError.set(error.message),
    });
  }

  protected deleteOrganization(): void {
    const id = this.context.activeOrganizationId();
    if (!id || this.context.activeRole() !== 'ADMIN' || this.organizationConfirmation() !== this.organizationName() || this.deletingOrganization()) return;
    this.deletionError.set('');
    this.deletingOrganization.set(true);
    this.context.deleteOrganization(id).subscribe({
      next: () => {
        this.deletingOrganization.set(false);
        const next = this.context.organizations()[0];
        if (!next) { void this.router.navigate(['/dashboard'], { queryParams: { organizationDeleted: '1' } }); return; }
        this.context.switchContext({ organization_id: next.organization_id, scope_id: next.scopes[0]?.id ?? null }).subscribe({
          next: () => void this.router.navigate(['/dashboard'], { queryParams: { organizationDeleted: '1' } }),
          error: () => void this.router.navigate(['/select-context']),
        });
      },
      error: (error: unknown) => { this.deletingOrganization.set(false); this.deletionError.set(this.deletionMessage(error)); },
    });
  }

  protected deleteAccount(): void {
    const username = this.auth.user()?.username;
    if (!username || this.accountConfirmation() !== username || this.deletingAccount()) return;
    this.deletionError.set('');
    this.deletingAccount.set(true);
    this.auth.deleteAccount().subscribe({
      next: () => void this.router.navigate(['/login'], { queryParams: { accountDeleted: '1' } }),
      error: (error: unknown) => { this.deletingAccount.set(false); this.deletionError.set(this.deletionMessage(error)); },
    });
  }

  private deletionMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const detail = error.error?.detail;
      if (typeof detail === 'string') return detail;
    }
    return error instanceof Error ? error.message : 'La suppression a échoué. Réessayez.';
  }
}
