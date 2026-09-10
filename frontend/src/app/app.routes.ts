import { Routes } from '@angular/router';

import { authGuard, guestGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    title: 'Connexion | OpenSMR',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/pages/login/login.component').then((module) => module.LoginComponent),
  },
  {
    path: 'register',
    title: 'Créer un compte | OpenSMR',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/pages/register/register.component').then(
        (module) => module.RegisterComponent,
      ),
  },
  {
    path: 'dashboard',
    title: 'Tableau de bord | OpenSMR',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN', 'RSSI', 'RISK_OWNER', 'AUDITOR'] },
    loadComponent: () =>
      import('./features/auth/pages/authenticated-home.component').then(
        (module) => module.AuthenticatedHomeComponent,
      ),
  },
  {
    path: 'access-denied',
    title: 'Accès refusé | OpenSMR',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./shared/pages/access-denied/access-denied.component').then(
        (module) => module.AccessDeniedComponent,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: '**', redirectTo: 'login' },
];
