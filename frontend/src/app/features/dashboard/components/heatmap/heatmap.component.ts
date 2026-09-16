import { Component, computed, input, output } from '@angular/core';

import { HeatmapCell } from '../../../../core/models/governance.models';

@Component({ selector: 'app-heatmap', templateUrl: './heatmap.component.html' })
export class HeatmapComponent {
  readonly cells = input.required<HeatmapCell[]>();
  readonly selected = input<{ likelihood: number; impact: number } | null>(null);
  readonly cellSelected = output<{ likelihood: number; impact: number } | null>();
  protected readonly rows = [5, 4, 3, 2, 1] as const;
  protected readonly columns = [1, 2, 3, 4, 5] as const;
  protected readonly total = computed(() => this.cells().reduce((sum, cell) => sum + cell.risk_count, 0));

  protected cell(likelihood: number, impact: number): HeatmapCell | undefined {
    return this.cells().find((cell) => cell.likelihood === likelihood && cell.impact === impact);
  }

  protected severity(likelihood: number, impact: number): string {
    const score = likelihood * impact;
    return score <= 4 ? 'low' : score <= 9 ? 'medium' : score <= 14 ? 'high' : 'critical';
  }

  protected select(likelihood: number, impact: number): void {
    const current = this.selected();
    this.cellSelected.emit(current?.likelihood === likelihood && current.impact === impact ? null : { likelihood, impact });
  }
}
