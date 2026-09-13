import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { finalize } from 'rxjs';

import { scopeDashboardEndpoint } from '../../../core/config/api.config';
import { ScopeDashboardMetrics } from '../../../core/models/governance.models';

const EMPTY_METRICS: ScopeDashboardMetrics = {
  risks_by_level: { high: 0, medium: 0, low: 0 },
  soa_completion: { total_applicable: 0, implemented: 0, percentage: 0 },
  overdue_tasks_count: 0,
};

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly metricsState = signal<ScopeDashboardMetrics>(EMPTY_METRICS);
  private readonly loadingState = signal(false);
  readonly metrics = this.metricsState.asReadonly();
  readonly loading = this.loadingState.asReadonly();

  fetch(scopeId: string): void {
    this.loadingState.set(true);
    this.http.get<ScopeDashboardMetrics>(scopeDashboardEndpoint(scopeId)).pipe(
      finalize(() => this.loadingState.set(false)),
    ).subscribe({
      next: (metrics) => this.metricsState.set(metrics),
      error: () => this.metricsState.set(EMPTY_METRICS),
    });
  }
}
