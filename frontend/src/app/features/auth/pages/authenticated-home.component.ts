import { Component, inject } from '@angular/core';

import { AuthService } from '../../../core/services/auth.service';
import { ContextService } from '../../../core/services/context.service';

@Component({
  selector: 'app-authenticated-home',
  template: `
    <main class="welcome-page">
      <nav class="welcome-nav">
        <span class="brand">
          <span class="brand__mark" aria-hidden="true">
            <svg viewBox="0 0 32 32"><path d="M16 3 27 8v7c0 7.1-4.6 11.7-11 14-6.4-2.3-11-6.9-11-14V8l11-5Z"/><path d="m11.5 16 3 3 6.5-7"/></svg>
          </span>
          OpenSMR
        </span>
        <button class="button button--ghost" type="button" (click)="auth.logout()">Se déconnecter</button>
      </nav>
      <section class="welcome-card">
        <span class="status-pill"><i></i> Session sécurisée</span>
        <p class="eyebrow">Authentification opérationnelle</p>
        <h1>Bienvenue, {{ auth.user()?.first_name || auth.user()?.username }}.</h1>
        <p>Votre socle Angular est prêt. Les prochains modules viendront enrichir cet espace de pilotage.</p>
        <dl class="context-summary">
          <div><dt>Organisation active</dt><dd>{{ context.activeOrganization()?.organization_name || 'Non définie' }}</dd></div>
          <div><dt>Rôle</dt><dd>{{ context.activeRole() || 'Aucun rôle' }}</dd></div>
          <div><dt>Périmètre</dt><dd>{{ context.activeScopeId() || 'Non défini' }}</dd></div>
        </dl>
      </section>
    </main>
  `,
})
export class AuthenticatedHomeComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
}
