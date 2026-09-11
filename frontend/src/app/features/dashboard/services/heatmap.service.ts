import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { finalize } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { HeatmapCell } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class HeatmapService {
  private readonly http = inject(HttpClient);
  private readonly cellsState = signal<HeatmapCell[]>([]);
  private readonly loadingState = signal(false);
  readonly cells = this.cellsState.asReadonly();
  readonly loading = this.loadingState.asReadonly();

  fetch(scopeId: string): void {
    this.loadingState.set(true);
    this.http.get<HeatmapCell[]>(DOMAIN_ENDPOINTS.heatmap, { params: new HttpParams().set('scope_id', scopeId) }).pipe(finalize(() => this.loadingState.set(false))).subscribe((cells) => this.cellsState.set(cells));
  }
}
