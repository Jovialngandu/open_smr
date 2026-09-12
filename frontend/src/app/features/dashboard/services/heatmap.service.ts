import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { finalize, map } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { HeatmapApiResponse, HeatmapCell } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class HeatmapService {
  private readonly http = inject(HttpClient);
  private readonly cellsState = signal<HeatmapCell[]>([]);
  private readonly loadingState = signal(false);
  readonly cells = this.cellsState.asReadonly();
  readonly loading = this.loadingState.asReadonly();

  fetch(scopeId: string): void {
    this.loadingState.set(true);
    this.http.get<HeatmapApiResponse>(DOMAIN_ENDPOINTS.heatmap, { params: new HttpParams().set('scope_id', scopeId) }).pipe(
      map((response) => response.matrix.map((cell) => ({ likelihood: cell.likelihood as HeatmapCell['likelihood'], impact: cell.impact as HeatmapCell['impact'], risk_count: cell.count, risk_ids: [] }))),
      finalize(() => this.loadingState.set(false)),
    ).subscribe((cells) => this.cellsState.set(cells));
  }
}
