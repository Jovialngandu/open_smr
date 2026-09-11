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
    path: 'assets',
    title: 'Inventaire des actifs | OpenSMR',
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['ADMIN', 'RSSI', 'RISK_OWNER'],
      featureTitle: 'Inventaire des actifs',
      featureDescription: 'Recensement et suivi de la criticité DIC des actifs du périmètre actif.',
    },
    loadComponent: () =>
      import('./features/assets/pages/assets-page/assets-page.component').then(
        (module) => module.AssetsPageComponent,
      ),
  },
  {
    path: 'risks',
    title: 'Registre des risques | OpenSMR',
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['ADMIN', 'RSSI', 'AUDITOR'],
      featureTitle: 'Registre des risques',
      featureDescription: 'Identification, évaluation et suivi des scénarios de risque du périmètre actif.',
    },
    loadComponent: () =>
      import('./features/risks/pages/risks-page/risks-page.component').then(
        (module) => module.RisksPageComponent,
      ),
  },
  {
    path: 'treatments',
    title: 'Plans de traitement | OpenSMR',
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['ADMIN', 'RSSI', 'RISK_OWNER'],
      featureTitle: 'Plans de traitement',
      featureDescription: 'Planification et suivi des actions destinées à réduire les risques.',
    },
    loadComponent: () => import('./features/treatments/pages/treatments-page/treatments-page.component').then((module) => module.TreatmentsPageComponent),
  },
  {
    path: 'soa',
    title: "Déclaration d'applicabilité | OpenSMR",
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['ADMIN', 'RSSI', 'RISK_OWNER', 'AUDITOR'],
      featureTitle: "Déclaration d'applicabilité",
      featureDescription: 'Suivi de l\'applicabilité et de la mise en œuvre des 93 mesures ISO 27001:2022.',
    },
    loadComponent: () => import('./features/soa/pages/soa-page/soa-page.component').then((module) => module.SoaPageComponent),
  },
  {
    path: 'users',
    title: 'Utilisateurs et auditeurs | OpenSMR',
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['ADMIN', 'RSSI'],
      featureTitle: 'Utilisateurs et auditeurs',
      featureDescription: 'Gestion des comptes, des rôles et des habilitations par périmètre.',
    },
    loadComponent: () => import('./features/users/pages/users-page/users-page.component').then((module) => module.UsersPageComponent),
  },
  {
    path: 'my-tasks',
    title: 'Mes tâches | OpenSMR',
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['RISK_OWNER'],
      featureTitle: 'Mes tâches',
      featureDescription: 'Suivi des actions assignées et dépôt des preuves de réalisation.',
    },
    loadComponent: () => import('./features/my-tasks/pages/my-tasks-page/my-tasks-page.component').then((module) => module.MyTasksPageComponent),
  },
  {
    path: 'audit-view',
    title: "Portail d'audit | OpenSMR",
    canActivate: [authGuard, roleGuard],
    data: {
      roles: ['AUDITOR'],
      featureTitle: "Portail d'audit externe",
      featureDescription: 'Consultation en lecture seule des risques, de la SoA et des preuves.',
    },
    loadComponent: () => import('./features/audit/pages/audit-view-page/audit-view-page.component').then((module) => module.AuditViewPageComponent),
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
