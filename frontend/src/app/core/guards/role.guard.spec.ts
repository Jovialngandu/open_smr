import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, provideRouter, RouterStateSnapshot, UrlTree } from '@angular/router';
import { firstValueFrom, Observable } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { ContextService } from '../services/context.service';
import { roleGuard } from './role.guard';

describe('roleGuard', () => {
  const status = signal<'checking' | 'authenticated' | 'anonymous'>('authenticated');
  const role = signal<'ADMIN' | 'AUDITOR'>('AUDITOR');

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { status: status.asReadonly() } },
        { provide: ContextService, useValue: { activeRole: role.asReadonly() } },
      ],
    });
  });

  it('autorise un role declare sur la route', async () => {
    const route = { data: { roles: ['AUDITOR'] } } as unknown as ActivatedRouteSnapshot;
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as RouterStateSnapshot));

    expect(await firstValueFrom(result as Observable<boolean | UrlTree>)).toBe(true);
  });

  it('redirige un role non autorise', async () => {
    const route = { data: { roles: ['ADMIN'] } } as unknown as ActivatedRouteSnapshot;
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as RouterStateSnapshot));
    const tree = await firstValueFrom(result as Observable<boolean | UrlTree>);

    expect(tree.toString()).toBe('/access-denied');
  });
});
