import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  host: { class: 'auth-page' },
  templateUrl: './login.component.html',
})
export class LoginComponent {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly formBuilder = inject(FormBuilder);
  protected readonly passwordVisible = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly form = this.formBuilder.nonNullable.group({
    identity: ['', Validators.required],
    password: ['', Validators.required],
    remember: [true],
  });

  protected showError(controlName: 'identity' | 'password'): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.dirty || control.touched);
  }

  protected submit(): void {
    this.errorMessage.set('');
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { identity, password, remember } = this.form.getRawValue();
    if (remember) localStorage.setItem('opensmr.saved_identity', identity.trim());
    else localStorage.removeItem('opensmr.saved_identity');

    this.auth.login({ username: identity.trim(), password }).subscribe({
      next: () => void this.router.navigate(['/dashboard']),
      error: (error: Error) => this.errorMessage.set(error.message),
    });
  }

  protected showRecoveryMessage(): void {
    this.errorMessage.set('La rÃ©initialisation sera disponible avec le prochain endpoint du backend.');
  }

  constructor() {
    const savedIdentity = localStorage.getItem('opensmr.saved_identity');
    if (savedIdentity) this.form.controls.identity.setValue(savedIdentity);
  }
}


