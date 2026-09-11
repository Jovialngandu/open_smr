import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, provideRouter, RouterStateSnapshot, UrlTree } from '@angular/router';
import { firstValueFrom, Observable } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { authGuard, guestGuard } from './auth.guard';

describe('authGuard', () => {
  const status = signal<'checking' | 'authenticated' | 'anonymous'>('anonymous');

  beforeEach(() => {
    status.set('anonymous');
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { status: status.asReadonly() } },
      ],
    });
  });

  it('redirige un visiteur et conserve son URL cible', async () => {
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, { url: '/risks' } as RouterStateSnapshot),
    );
    const tree = await firstValueFrom(result as Observable<boolean | UrlTree>);

    expect(tree.toString()).toBe('/login?returnUrl=%2Frisks');
  });

  it('eloigne un utilisateur connecte des pages publiques', async () => {
    status.set('authenticated');
    const result = TestBed.runInInjectionContext(() =>
      guestGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
    const tree = await firstValueFrom(result as Observable<boolean | UrlTree>);

    expect(tree.toString()).toBe('/dashboard');
  });
});
