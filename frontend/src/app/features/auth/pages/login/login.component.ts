import { Component, inject, signal } from '@angular/core';
import { LucideShieldCheck, LucideCheck, LucideCircleAlert, LucideArrowRight, LucideSparkles } from '@lucide/angular';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';
import { ContextService } from '../../../../core/services/context.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, LucideShieldCheck, LucideCheck, LucideCircleAlert, LucideArrowRight, LucideSparkles],
  host: { class: 'auth-page' },
  templateUrl: './login.component.html',
})
export class LoginComponent {
  protected readonly auth = inject(AuthService);
  private readonly context = inject(ContextService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly formBuilder = inject(FormBuilder);
  protected readonly passwordVisible = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly accountDeleted = this.route.snapshot.queryParamMap.get('accountDeleted') === '1';
  protected readonly form = this.formBuilder.nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
    remember: [true],
  });

  protected showError(controlName: 'username' | 'password'): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.dirty || control.touched);
  }

  protected submit(): void {
    this.errorMessage.set('');
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { username, password, remember } = this.form.getRawValue();
    if (remember) localStorage.setItem('opensmr.saved_username', username.trim());
    else localStorage.removeItem('opensmr.saved_username');

    this.auth.login({ username: username.trim(), password }).subscribe({
      next: (profile) => {
        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
        const target = returnUrl?.startsWith('/invitations?') || returnUrl?.startsWith('/invitations/accept?')
          ? returnUrl
          : profile.roles.length && !this.context.hasValidActiveContext(profile) ? '/select-context' : '/dashboard';
        void this.router.navigateByUrl(target);
      },
      error: (error: Error) => this.errorMessage.set(error.message),
    });
  }

  protected showRecoveryMessage(): void {
    this.errorMessage.set('La réinitialisation du mot de passe n’est pas encore disponible. Contactez un administrateur si vous ne pouvez plus accéder à votre compte.');
  }

  constructor() {
    const savedUsername = localStorage.getItem('opensmr.saved_username') ?? localStorage.getItem('opensmr.saved_identity');
    if (savedUsername) this.form.controls.username.setValue(savedUsername);
    localStorage.removeItem('opensmr.saved_identity');
  }
}
