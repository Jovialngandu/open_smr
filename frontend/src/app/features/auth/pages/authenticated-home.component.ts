import { Component, inject } from '@angular/core';

import { AuthService } from '../../../core/services/auth.service';
import { ContextService } from '../../../core/services/context.service';
import { TopbarComponent } from '../../../shared/components/topbar/topbar.component';

@Component({
  selector: 'app-authenticated-home',
  imports: [TopbarComponent],
  templateUrl: './authenticated-home.component.html',
})
export class AuthenticatedHomeComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
}
