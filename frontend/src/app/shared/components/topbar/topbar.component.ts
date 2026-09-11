import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../../core/services/auth.service';
import { ContextService } from '../../../core/services/context.service';

@Component({
  selector: 'app-topbar',
  imports: [RouterLink],
  templateUrl: './topbar.component.html',
})
export class TopbarComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
  protected readonly switching = signal(false);
  protected readonly contextError = signal('');
  protected readonly menuOpen = signal(false);
  protected readonly initials = computed(() => {
    const user = this.auth.user();
    return `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? user?.username?.[0] ?? ''}`.toUpperCase();
  });

  protected changeOrganization(event: Event): void {
    const organizationId = (event.target as HTMLSelectElement).value;
    const organization = this.context.organizations().find(
      (item) => item.organization_id === organizationId,
    );
    this.applyContext(organizationId, organization?.scopes?.[0]?.id ?? null);
  }

  protected changeScope(event: Event): void {
    const scopeId = (event.target as HTMLSelectElement).value || null;
    const organizationId = this.context.activeOrganizationId();
    if (organizationId) this.applyContext(organizationId, scopeId);
  }

  protected logout(): void {
    this.menuOpen.set(false);
    this.auth.logout();
  }

  private applyContext(organizationId: string, scopeId: string | null): void {
    this.contextError.set('');
    this.switching.set(true);
    this.context.switchContext({ organization_id: organizationId, scope_id: scopeId }).pipe(
      finalize(() => this.switching.set(false)),
    ).subscribe({
      error: () => this.contextError.set('Le changement de contexte a échoué. Réessayez.'),
    });
  }
}
