import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-risk-score-badge',
  templateUrl: './risk-score-badge.component.html',
})
export class RiskScoreBadgeComponent {
  readonly likelihood = input.required<number>();
  readonly impact = input.required<number>();

  protected readonly score = computed(() => this.likelihood() * this.impact());
  protected readonly severity = computed(() => {
    const score = this.score();
    if (score <= 4) return { key: 'low', label: 'Faible' };
    if (score <= 9) return { key: 'medium', label: 'Modéré' };
    if (score <= 14) return { key: 'high', label: 'Élevé' };
    return { key: 'critical', label: 'Critique' };
  });
}
