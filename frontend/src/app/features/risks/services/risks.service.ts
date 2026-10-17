import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, finalize, map, Observable, tap, throwError } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { Risk, RiskPayload } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class RisksService {
  private readonly http = inject(HttpClient);
  private readonly risksState = signal<Risk[]>([]);
  private readonly loadingState = signal(false);
  private readonly savingState = signal(false);
  private readonly errorState = signal('');

  readonly risks = this.risksState.asReadonly();
  readonly loading = this.loadingState.asReadonly();
  readonly saving = this.savingState.asReadonly();
  readonly error = this.errorState.asReadonly();
  readonly count = computed(() => this.risksState().length);
  readonly criticalCount = computed(() => this.risksState().filter((risk) => risk.score >= 15).length);

  fetchRisks(scopeId: string): void {
    this.loadingState.set(true);
    this.errorState.set('');
    const params = new HttpParams().set('scope_id', scopeId);
    this.http.get<RiskApiResponse[]>(DOMAIN_ENDPOINTS.risks, { params }).pipe(
      map((risks) => risks.map(toRisk)),
      finalize(() => this.loadingState.set(false)),
    ).subscribe({
      next: (risks) => this.risksState.set(risks),
      error: () => this.errorState.set('Impossible de charger le registre des risques.'),
    });
  }

  createRisk(payload: RiskPayload): Observable<Risk> {
    this.savingState.set(true);
    return this.http.post<RiskApiResponse>(DOMAIN_ENDPOINTS.risks, payload).pipe(
      map(toRisk),
      tap((risk) => this.risksState.update((items) => [risk, ...items])),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  updateRisk(id: string, payload: RiskPayload): Observable<Risk> {
    this.savingState.set(true);
    const { asset_id: _assetId, ...updateBody } = payload;
    return this.http.patch<RiskApiResponse>(`${DOMAIN_ENDPOINTS.risks}${id}/`, updateBody).pipe(
      map(toRisk),
      tap((risk) =>
        this.risksState.update((items) => items.map((item) => item.id === id ? risk : item)),
      ),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  private friendlyError(error: unknown): Error {
    if (error instanceof HttpErrorResponse) {
      return new Error(error.error?.detail ?? "L'opération sur le risque a échoué.");
    }
    return new Error("L'opération sur le risque a échoué.");
  }
}

interface RiskApiResponse {
  id: string;
  asset: { id: string; name: string; category: string; scope_id: string };
  code: string;
  threat_description: string;
  likelihood: Risk['likelihood'];
  impact: Risk['impact'];
  score: number;
  status: Risk['status'];
  created_at: string;
  updated_at: string;
}

function toRisk(risk: RiskApiResponse | Risk): Risk {
  if ('asset_id' in risk) return risk;
  return {
    ...risk,
    asset_id: risk.asset.id,
    asset_name: risk.asset.name,
    scope_id: risk.asset.scope_id,
  };
}
