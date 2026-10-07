import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideBell, LucideCheck, LucideClock3, LucideGlobe2, LucidePalette, LucideUserRound } from '@lucide/angular';

import { AuthService } from '../../../../core/services/auth.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { AppTheme, SettingsService } from '../../services/settings.service';

@Component({
  selector: 'app-settings-page',
  imports: [ReactiveFormsModule, TopbarComponent, LucideBell, LucideCheck, LucideClock3, LucideGlobe2, LucidePalette, LucideUserRound],
  templateUrl: './settings-page.component.html',
})
export class SettingsPageComponent {
  protected readonly auth = inject(AuthService);
  protected readonly service = inject(SettingsService);
  private readonly fb = inject(FormBuilder);
  protected readonly feedback = signal('');
  protected readonly submitError = signal('');
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
}
