import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, finalize, Observable, tap, throwError } from 'rxjs';

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
    this.http.get<Risk[]>(DOMAIN_ENDPOINTS.risks, { params }).pipe(
      finalize(() => this.loadingState.set(false)),
    ).subscribe({
      next: (risks) => this.risksState.set(risks),
      error: () => this.errorState.set('Impossible de charger le registre des risques.'),
    });
  }

  createRisk(payload: RiskPayload): Observable<Risk> {
    this.savingState.set(true);
    return this.http.post<Risk>(DOMAIN_ENDPOINTS.risks, payload).pipe(
      tap((risk) => this.risksState.update((items) => [risk, ...items])),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  updateRisk(id: string, payload: RiskPayload): Observable<Risk> {
    this.savingState.set(true);
    return this.http.put<Risk>(`${DOMAIN_ENDPOINTS.risks}${id}/`, payload).pipe(
      tap((risk) =>
        this.risksState.update((items) => items.map((item) => item.id === id ? risk : item)),
      ),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  deleteRisk(id: string): Observable<void> {
    return this.http.delete<void>(`${DOMAIN_ENDPOINTS.risks}${id}/`).pipe(
      tap(() => this.risksState.update((items) => items.filter((item) => item.id !== id))),
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
