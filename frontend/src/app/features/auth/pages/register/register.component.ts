import { Component, inject, signal } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink],
  host: { class: 'auth-page' },
  template: `
    <main class="auth-shell auth-shell--register">
      <section class="auth-story" aria-labelledby="story-title">
        <a class="brand brand--light" routerLink="/login" aria-label="OpenSMR, accueil">
          <span class="brand__mark" aria-hidden="true">
            <svg viewBox="0 0 32 32"><path d="M16 3 27 8v7c0 7.1-4.6 11.7-11 14-6.4-2.3-11-6.9-11-14V8l11-5Z"/><path d="m11.5 16 3 3 6.5-7"/></svg>
          </span>
          <span>OpenSMR</span>
        </a>
        <div class="auth-story__content">
          <p class="eyebrow eyebrow--light">Démarrez sur de bonnes bases</p>
          <h1 id="story-title">Votre SMSI,<br />simplement structuré.</h1>
          <p>Créez votre espace de travail et posez les fondations d'une gouvernance durable.</p>
          <div class="trust-card">
            <span aria-hidden="true">“</span>
            <p>La conformité devient plus simple lorsqu'elle est reliée au travail quotidien.</p>
          </div>
        </div>
        <p class="auth-story__foot">Isolation multi-tenant · Contrôle d'accès par rôle</p>
      </section>

      <section class="auth-panel" aria-labelledby="register-title">
        <div class="auth-card auth-card--wide">
          <div class="mobile-brand">
            <span class="brand__mark" aria-hidden="true">
              <svg viewBox="0 0 32 32"><path d="M16 3 27 8v7c0 7.1-4.6 11.7-11 14-6.4-2.3-11-6.9-11-14V8l11-5Z"/><path d="m11.5 16 3 3 6.5-7"/></svg>
            </span>
            OpenSMR
          </div>
          <p class="eyebrow">Créer votre espace</p>
          <h2 id="register-title">Commencez votre parcours de conformité</h2>
          <p class="auth-intro">Quelques informations suffisent. Vous pourrez inviter votre équipe ensuite.</p>

          @if (errorMessage()) {
            <div class="alert alert--error" role="alert"><span aria-hidden="true">!</span><p>{{ errorMessage() }}</p></div>
          }

          <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
            <div class="form-grid">
              <div class="field">
                <label for="firstName">Prénom</label>
                <input id="firstName" formControlName="firstName" autocomplete="given-name" placeholder="Camille" />
              </div>
              <div class="field">
                <label for="lastName">Nom</label>
                <input id="lastName" formControlName="lastName" autocomplete="family-name" placeholder="Durand" />
              </div>
            </div>

            <div class="field">
              <label for="email">Email professionnel</label>
              <input id="email" type="email" formControlName="email" autocomplete="email" placeholder="vous@entreprise.com" [attr.aria-invalid]="invalid('email')" />
              @if (invalid('email')) { <small class="field__error">Saisissez une adresse email valide.</small> }
            </div>

            <div class="form-grid">
              <div class="field">
                <label for="username">Identifiant</label>
                <input id="username" formControlName="username" autocomplete="username" placeholder="camille.durand" [attr.aria-invalid]="invalid('username')" />
                @if (invalid('username')) { <small class="field__error">3 caractères minimum.</small> }
              </div>
              <div class="field">
                <label for="organization">Organisation <span>(facultatif)</span></label>
                <input id="organization" formControlName="organization" autocomplete="organization" placeholder="Asteria Finance" />
              </div>
            </div>

            <div class="field">
              <label for="password">Mot de passe</label>
              <div class="password-input">
                <input id="password" [type]="passwordVisible() ? 'text' : 'password'" formControlName="password" autocomplete="new-password" placeholder="12 caractères minimum" [attr.aria-invalid]="invalid('password')" />
                <button type="button" (click)="passwordVisible.set(!passwordVisible())">{{ passwordVisible() ? 'Masquer' : 'Afficher' }}</button>
              </div>
              <div class="password-meter" [attr.data-strength]="passwordStrength()">
                <span></span><span></span><span></span><span></span>
              </div>
              <small class="field__hint">12 caractères, avec majuscule, minuscule et chiffre.</small>
            </div>

            <div class="field">
              <label for="confirmation">Confirmer le mot de passe</label>
              <input id="confirmation" type="password" formControlName="confirmation" autocomplete="new-password" placeholder="Répétez votre mot de passe" [attr.aria-invalid]="invalid('confirmation') || form.hasError('passwordMismatch')" />
              @if ((form.controls.confirmation.touched || form.controls.confirmation.dirty) && form.hasError('passwordMismatch')) {
                <small class="field__error">Les mots de passe ne correspondent pas.</small>
              }
            </div>

            <label class="checkbox checkbox--top">
              <input type="checkbox" formControlName="terms" />
              <span>J'accepte les conditions d'utilisation et la politique de confidentialité.</span>
            </label>
            @if (invalid('terms')) { <small class="field__error field__error--standalone">Votre accord est requis.</small> }

            <button class="button button--primary button--full" type="submit" [disabled]="auth.busy()">
              @if (auth.busy()) { <span class="spinner" aria-hidden="true"></span> Création en cours… }
              @else { Créer mon espace <span aria-hidden="true">→</span> }
            </button>
          </form>
          <p class="auth-switch">Déjà inscrit ? <a routerLink="/login">Se connecter</a></p>
        </div>
      </section>
    </main>
  `,
})
export class RegisterComponent {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly formBuilder = inject(FormBuilder);
  protected readonly passwordVisible = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly form = this.formBuilder.nonNullable.group(
    {
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      username: ['', [Validators.required, Validators.minLength(3)]],
      organization: [''],
      password: ['', [Validators.required, Validators.minLength(12), Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/)]],
      confirmation: ['', Validators.required],
      terms: [false, Validators.requiredTrue],
    },
    { validators: passwordMatchValidator },
  );
  protected passwordStrength(): number {
    const value = this.form.controls.password.value;
    return [value.length >= 12, /[a-z]/.test(value) && /[A-Z]/.test(value), /\d/.test(value), /[^\w]/.test(value)].filter(Boolean).length;
  }

  protected invalid(controlName: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.touched || control.dirty);
  }

  protected submit(): void {
    this.errorMessage.set('');
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.auth.register({
      first_name: value.firstName.trim(),
      last_name: value.lastName.trim(),
      email: value.email.trim().toLowerCase(),
      username: value.username.trim(),
      password: value.password,
      organization_name: value.organization.trim() || undefined,
    }).subscribe({
      next: () => void this.router.navigate(['/dashboard']),
      error: (error: Error) => this.errorMessage.set(error.message),
    });
  }
}

function passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
  return control.get('password')?.value === control.get('confirmation')?.value
    ? null
    : { passwordMismatch: true };
}
