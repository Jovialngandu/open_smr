import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { TopbarComponent } from '../../components/topbar/topbar.component';

@Component({
  selector: 'app-feature-placeholder',
  imports: [TopbarComponent],
  templateUrl: './feature-placeholder.component.html',
})
export class FeaturePlaceholderComponent {
  private readonly route = inject(ActivatedRoute);

  protected readonly title = this.route.snapshot.data['featureTitle'] as string;
  protected readonly description = this.route.snapshot.data['featureDescription'] as string;
}
