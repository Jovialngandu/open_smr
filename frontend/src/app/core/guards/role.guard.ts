import { inject } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { CanActivateFn, Router } from '@angular/router';
import { filter, map, take } from 'rxjs';

import { UserRole } from '../models/auth.models';
import { AuthService } from '../services/auth.service';
import { ContextService } from '../services/context.service';

export const roleGuard: CanActivateFn = (route) => {
  const context = inject(ContextService);
  const auth = inject(AuthService);
  const router = inject(Router);
  const allowedRoles = (route.data['roles'] as UserRole[] | undefined) ?? [];

  return toObservable(auth.status).pipe(
    filter((status) => status !== 'checking'),
    take(1),
    map(() => {
      const activeRole = context.activeRole();
      return activeRole && allowedRoles.includes(activeRole)
        ? true
        : router.createUrlTree(['/access-denied']);
    }),
  );
};
