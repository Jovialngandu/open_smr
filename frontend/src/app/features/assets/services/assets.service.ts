import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, finalize, Observable, tap, throwError } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { Asset, AssetPayload } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class AssetsService {
  private readonly http = inject(HttpClient);
  private readonly assetsState = signal<Asset[]>([]);
  private readonly loadingState = signal(false);
  private readonly savingState = signal(false);
  private readonly errorState = signal('');

  readonly assets = this.assetsState.asReadonly();
  readonly loading = this.loadingState.asReadonly();
  readonly saving = this.savingState.asReadonly();
  readonly error = this.errorState.asReadonly();
  readonly count = computed(() => this.assetsState().length);

  fetchAssets(scopeId: string): void {
    this.loadingState.set(true);
    this.errorState.set('');
    const params = new HttpParams().set('scope_id', scopeId);
    this.http.get<Asset[]>(DOMAIN_ENDPOINTS.assets, { params }).pipe(
      finalize(() => this.loadingState.set(false)),
    ).subscribe({
      next: (assets) => this.assetsState.set(assets),
      error: () => this.errorState.set("Impossible de charger l'inventaire des actifs."),
    });
  }

  createAsset(payload: AssetPayload): Observable<Asset> {
    this.savingState.set(true);
    return this.http.post<Asset>(DOMAIN_ENDPOINTS.assets, payload).pipe(
      tap((asset) => this.assetsState.update((items) => [asset, ...items])),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  updateAsset(id: string, payload: AssetPayload): Observable<Asset> {
    this.savingState.set(true);
    return this.http.put<Asset>(`${DOMAIN_ENDPOINTS.assets}${id}/`, payload).pipe(
      tap((asset) =>
        this.assetsState.update((items) => items.map((item) => item.id === id ? asset : item)),
      ),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  deleteAsset(id: string): Observable<void> {
    return this.http.delete<void>(`${DOMAIN_ENDPOINTS.assets}${id}/`).pipe(
      tap(() => this.assetsState.update((items) => items.filter((item) => item.id !== id))),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  private friendlyError(error: unknown): Error {
    if (error instanceof HttpErrorResponse) {
      return new Error(error.error?.detail ?? "L'opération sur l'actif a échoué.");
    }
    return new Error("L'opération sur l'actif a échoué.");
  }
}
