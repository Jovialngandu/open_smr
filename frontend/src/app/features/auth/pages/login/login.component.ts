import { AfterViewInit, Component, ElementRef, inject, NgZone, OnDestroy, signal, viewChild } from '@angular/core';
import { LucideShieldCheck, LucideCheck, LucideCircleAlert, LucideArrowRight, LucideSparkles } from '@lucide/angular';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';
import { ContextService } from '../../../../core/services/context.service';
import { GOOGLE_CLIENT_ID } from '../../../../core/config/oidc.config';
import { UserProfile } from '../../../../core/models/auth.models';

interface GoogleCredentialResponse { credential?: string }
interface GoogleIdentityApi {
  accounts: { id: {
    initialize(config: { client_id: string; callback: (response: GoogleCredentialResponse) => void }): void;
    renderButton(element: HTMLElement, options: { theme: string; size: string; width: number; locale: string }): void;
  } };
}
declare global { interface Window { google?: GoogleIdentityApi } }

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, LucideShieldCheck, LucideCheck, LucideCircleAlert, LucideArrowRight, LucideSparkles],
  host: { class: 'auth-page' },
  templateUrl: './login.component.html',
})
export class LoginComponent implements AfterViewInit, OnDestroy {
  protected readonly auth = inject(AuthService);
  private readonly context = inject(ContextService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly formBuilder = inject(FormBuilder);
  private readonly zone = inject(NgZone);
  private readonly googleButton = viewChild<ElementRef<HTMLElement>>('googleButton');
  private googleScript: HTMLScriptElement | null = null;
  private googleTimeout: ReturnType<typeof setTimeout> | null = null;
  protected readonly googleConfigured = !!GOOGLE_CLIENT_ID;
  protected readonly googleError = signal('');
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
      next: (profile) => this.completeLogin(profile),
      error: (error: Error) => this.errorMessage.set(error.message),
    });
  }

  ngAfterViewInit(): void {
    if (!GOOGLE_CLIENT_ID) return;
    if (window.google) { this.renderGoogleButton(); return; }
    this.googleScript = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]');
    if (!this.googleScript) { this.googleError.set('Le module de connexion Google est indisponible.'); return; }
    this.googleScript.addEventListener('load', this.onGoogleLoad);
    this.googleScript.addEventListener('error', this.onGoogleError);
    this.googleTimeout = setTimeout(() => {
      if (!window.google) this.googleError.set('Le bouton Google ne répond pas. Vérifiez votre connexion et réessayez.');
    }, 10000);
  }

  ngOnDestroy(): void {
    this.googleScript?.removeEventListener('load', this.onGoogleLoad);
    this.googleScript?.removeEventListener('error', this.onGoogleError);
    if (this.googleTimeout) clearTimeout(this.googleTimeout);
  }

  private readonly onGoogleLoad = (): void => this.renderGoogleButton();
  private readonly onGoogleError = (): void => this.googleError.set('Impossible de charger la connexion Google.');

  private renderGoogleButton(): void {
    const target = this.googleButton()?.nativeElement;
    if (!target || !window.google || !GOOGLE_CLIENT_ID) return;
    if (this.googleTimeout) clearTimeout(this.googleTimeout);
    this.googleError.set('');
    target.replaceChildren();
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: ({ credential }) => this.zone.run(() => {
        if (!credential || this.auth.busy()) return;
        this.errorMessage.set('');
        this.auth.loginWithGoogle(credential).subscribe({
          next: (profile) => this.completeLogin(profile),
          error: (error: Error) => this.errorMessage.set(error.message),
        });
      }),
    });
    window.google.accounts.id.renderButton(target, { theme: 'outline', size: 'large', width: 320, locale: 'fr' });
  }

  private completeLogin(profile: UserProfile): void {
    const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
    const target = returnUrl?.startsWith('/invitations?') || returnUrl?.startsWith('/invitations/accept?')
      ? returnUrl
      : profile.roles.length && !this.context.hasValidActiveContext(profile) ? '/select-context' : '/dashboard';
    void this.router.navigateByUrl(target);
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
