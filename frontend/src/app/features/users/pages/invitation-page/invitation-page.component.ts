import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { catchError, of, switchMap } from 'rxjs';

import { AuthService } from '../../../../core/services/auth.service';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { InvitationsService } from '../../services/invitations.service';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

@Component({
  selector: 'app-invitation-page',
  imports: [TopbarComponent, RouterLink],
  templateUrl: './invitation-page.component.html',
})
export class InvitationPageComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly invitations = inject(InvitationsService);
  private readonly context = inject(ContextService);
  protected readonly auth = inject(AuthService);
  protected readonly token = this.route.snapshot.queryParamMap.get('token') ?? '';
  protected readonly validToken = UUID.test(this.token);
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly declined = signal(false);

  protected accept(): void {
    if (!this.validToken || this.busy()) return;
    this.error.set(''); this.busy.set(true);
    this.invitations.accept(this.token).pipe(
      switchMap(({ invitation }) => this.auth.loadProfile().pipe(
        switchMap(() => this.context.switchContext({ organization_id: invitation.organization.id, scope_id: null }).pipe(
          catchError(() => of(null)),
        )),
        catchError(() => of(null)),
      )),
    ).subscribe({
      next: () => { this.busy.set(false); void this.router.navigate(['/dashboard'], { queryParams: { invitation: 'accepted' } }); },
      error: (error: Error) => { this.busy.set(false); this.error.set(error.message); },
    });
  }

  protected decline(): void {
    if (!this.validToken || this.busy()) return;
    this.error.set(''); this.busy.set(true);
    this.invitations.decline(this.token).subscribe({
      next: () => { this.busy.set(false); this.declined.set(true); },
      error: (error: Error) => { this.busy.set(false); this.error.set(error.message); },
    });
  }
}
