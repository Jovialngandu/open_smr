import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { ControlTheme } from '../../../core/models/governance.models';

export interface ControlSuggestion {
  id?: string;
  code: string;
  title: string;
  theme: ControlTheme;
  description: string;
  score?: number;
  score_type?: string;
}

export function riskControlSuggestionsEndpoint(riskId: string): string {
  return `${DOMAIN_ENDPOINTS.risks}${riskId}/iso-control-suggestions/`;
}

@Injectable({ providedIn: 'root' })
export class ControlSuggestionsService {
  private readonly http = inject(HttpClient);

  forRisk(riskId: string, actionTitle: string): Observable<ControlSuggestion[]> {
    const context = actionTitle.trim();
    const params = context ? new HttpParams().set('context', context) : new HttpParams();
    return this.http.get<ControlSuggestion[] | { results: ControlSuggestion[] }>(riskControlSuggestionsEndpoint(riskId), { params }).pipe(
      map((response) => Array.isArray(response) ? response : response.results),
    );
  }
}
