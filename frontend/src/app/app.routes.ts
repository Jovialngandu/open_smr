import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'login',
    title: 'Connexion | OpenSMR',
    loadComponent: () =>
      import('./features/auth/pages/login/login.component').then((module) => module.LoginComponent),
  },
  {
    path: 'register',
    title: 'Créer un compte | OpenSMR',
    loadComponent: () =>
      import('./features/auth/pages/register/register.component').then(
        (module) => module.RegisterComponent,
      ),
  },
  {
    path: 'dashboard',
    title: 'Tableau de bord | OpenSMR',
    loadComponent: () =>
      import('./features/auth/pages/authenticated-home.component').then(
        (module) => module.AuthenticatedHomeComponent,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: '**', redirectTo: 'login' },
];
