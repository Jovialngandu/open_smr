import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  host: { class: 'auth-page' },
  template: `
    <main class="auth-shell">
      <section class="auth-story" aria-labelledby="story-title">
        <a class="brand brand--light" routerLink="/login" aria-label="OpenSMR, accueil">
          <span class="brand__mark" aria-hidden="true">
            <svg viewBox="0 0 32 32"><path d="M16 3 27 8v7c0 7.1-4.6 11.7-11 14-6.4-2.3-11-6.9-11-14V8l11-5Z"/><path d="m11.5 16 3 3 6.5-7"/></svg>
          </span>
          <span>OpenSMR</span>
        </a>

        <div class="auth-story__content">
          <p class="eyebrow eyebrow--light">Sécurité de l'information, maîtrisée</p>
          <h1 id="story-title">Pilotez vos risques.<br />Démontrez votre conformité.</h1>
          <p>Un espace unique pour transformer ISO 27001 en actions claires, suivies et auditables.</p>
          <ul class="value-list" aria-label="Fonctionnalités principales">
            <li><span>✓</span> Vue consolidée de vos risques et actifs</li>
            <li><span>✓</span> Suivi des actions et preuves en temps réel</li>
            <li><span>✓</span> Données isolées par organisation et périmètre</li>
          </ul>
        </div>

        <p class="auth-story__foot">Conçu pour les équipes RSSI exigeantes.</p>
      </section>

      <section class="auth-panel" aria-labelledby="login-title">
        <div class="auth-card">
          <div class="mobile-brand">
            <span class="brand__mark" aria-hidden="true">
              <svg viewBox="0 0 32 32"><path d="M16 3 27 8v7c0 7.1-4.6 11.7-11 14-6.4-2.3-11-6.9-11-14V8l11-5Z"/><path d="m11.5 16 3 3 6.5-7"/></svg>
            </span>
            OpenSMR
          </div>
          <p class="eyebrow">Ravi de vous revoir</p>
          <h2 id="login-title">Connectez-vous à votre espace</h2>
          <p class="auth-intro">Retrouvez le pilotage de votre SMSI en toute sécurité.</p>

          @if (errorMessage()) {
            <div class="alert alert--error" role="alert">
              <span aria-hidden="true">!</span>
              <p>{{ errorMessage() }}</p>
            </div>
          }

          <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
            <div class="field">
              <label for="identity">Email ou identifiant</label>
              <input
                id="identity"
                type="text"
                formControlName="identity"
                autocomplete="username"
                placeholder="vous@entreprise.com"
                [attr.aria-invalid]="showError('identity')"
                aria-describedby="identity-hint"
              />
              @if (showError('identity')) {
                <small id="identity-hint" class="field__error">Saisissez votre email ou identifiant.</small>
              }
            </div>

            <div class="field">
              <div class="field__label-row">
                <label for="password">Mot de passe</label>
                <button class="text-button" type="button" (click)="showRecoveryMessage()">Mot de passe oublié ?</button>
              </div>
              <div class="password-input">
                <input
                  id="password"
                  [type]="passwordVisible() ? 'text' : 'password'"
                  formControlName="password"
                  autocomplete="current-password"
                  placeholder="Votre mot de passe"
                  [attr.aria-invalid]="showError('password')"
                />
                <button type="button" (click)="passwordVisible.set(!passwordVisible())" [attr.aria-label]="passwordVisible() ? 'Masquer le mot de passe' : 'Afficher le mot de passe'">
                  {{ passwordVisible() ? 'Masquer' : 'Afficher' }}
                </button>
              </div>
              @if (showError('password')) {
                <small class="field__error">Le mot de passe est obligatoire.</small>
              }
            </div>

            <label class="checkbox">
              <input type="checkbox" formControlName="remember" />
              <span>Se souvenir de mon identifiant</span>
            </label>

            <button class="button button--primary button--full" type="submit" [disabled]="auth.busy()">
              @if (auth.busy()) { <span class="spinner" aria-hidden="true"></span> Connexion en cours… }
              @else { Se connecter <span aria-hidden="true">→</span> }
            </button>
          </form>

          <div class="demo-note">
            <span class="demo-note__icon" aria-hidden="true">✦</span>
            <div><strong>Mode démonstration</strong><br /><code>demo&#64;opensmr.fr</code> · <code>Demo1234!</code></div>
          </div>

          <p class="auth-switch">Première visite ? <a routerLink="/register">Créer un compte</a></p>
        </div>
      </section>
    </main>
  `,
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
    this.errorMessage.set('La réinitialisation sera disponible avec le prochain endpoint du backend.');
  }

  constructor() {
    const savedIdentity = localStorage.getItem('opensmr.saved_identity');
    if (savedIdentity) this.form.controls.identity.setValue(savedIdentity);
  }
}
