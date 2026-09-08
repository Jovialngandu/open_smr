import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, map, Observable, switchMap, tap, throwError } from 'rxjs';

import { AUTH_ENDPOINTS } from '../config/api.config';
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  UserProfile,
} from '../models/auth.models';
import { ContextService } from './context.service';
import { TokenStorageService } from './token-storage.service';

type AuthStatus = 'checking' | 'authenticated' | 'anonymous';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly tokens = inject(TokenStorageService);
  private readonly context = inject(ContextService);
  private readonly statusState = signal<AuthStatus>('checking');
  private readonly busyState = signal(false);

  readonly status = this.statusState.asReadonly();
  readonly busy = this.busyState.asReadonly();
  readonly isAuthenticated = computed(() => this.statusState() === 'authenticated');
  readonly user = this.context.profile;

  constructor() {
    if (this.tokens.isAccessTokenValid()) {
      this.loadProfile().subscribe({ error: () => this.endSession(false) });
    } else {
      this.endSession(false);
    }
  }

  login(credentials: LoginRequest): Observable<UserProfile> {
    this.busyState.set(true);
    return this.http.post<AuthResponse>(AUTH_ENDPOINTS.login, credentials).pipe(
      tap((response) => this.tokens.save(response)),
      switchMap(() => this.loadProfile()),
      finalize(() => this.busyState.set(false)),
      catchError((error) => throwError(() => this.toFriendlyError(error))),
    );
  }

  register(payload: RegisterRequest): Observable<UserProfile> {
    this.busyState.set(true);
    return this.http.post<AuthResponse>(AUTH_ENDPOINTS.register, payload).pipe(
      tap((response) => this.tokens.save(response)),
      switchMap((response) =>
        response.user ? this.acceptProfile(response.user) : this.loadProfile(),
      ),
      finalize(() => this.busyState.set(false)),
      catchError((error) => throwError(() => this.toFriendlyError(error))),
    );
  }

  loadProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(AUTH_ENDPOINTS.profile).pipe(
      tap((profile) => {
        this.context.setProfile(profile);
        this.context.syncClaims();
        this.statusState.set('authenticated');
      }),
    );
  }

  logout(redirect = true): void {
    this.endSession(redirect);
  }

  private acceptProfile(profile: UserProfile): Observable<UserProfile> {
    this.context.setProfile(profile);
    this.context.syncClaims();
    this.statusState.set('authenticated');
    return new Observable((subscriber) => {
      subscriber.next(profile);
      subscriber.complete();
    });
  }

  private endSession(redirect: boolean): void {
    this.tokens.clear();
    this.context.reset();
    this.statusState.set('anonymous');
    if (redirect) void this.router.navigate(['/login']);
  }

  private toFriendlyError(error: unknown): Error {
    if (error instanceof HttpErrorResponse) {
      const apiMessage = error.error?.detail ?? Object.values(error.error ?? {})[0];
      if (typeof apiMessage === 'string') return new Error(apiMessage);
      if (Array.isArray(apiMessage) && apiMessage[0]) return new Error(String(apiMessage[0]));
      if (error.status === 0) return new Error("Le service est indisponible. Réessayez dans un instant.");
      if (error.status === 401) return new Error('Identifiant ou mot de passe incorrect.');
    }
    return error instanceof Error ? error : new Error('Une erreur inattendue est survenue.');
  }
}
