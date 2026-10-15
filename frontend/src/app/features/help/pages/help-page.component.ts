import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ContextService } from '../../../core/services/context.service';
import { TopbarComponent } from '../../../shared/components/topbar/topbar.component';

@Component({
  selector: 'app-help-page',
  imports: [RouterLink, TopbarComponent],
  templateUrl: './help-page.component.html',
  styleUrl: './help-page.component.scss',
})
export class HelpPageComponent {
  protected readonly context = inject(ContextService);
}
