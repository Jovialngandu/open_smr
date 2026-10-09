import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, finalize, map, Observable, tap, throwError } from 'rxjs';

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
    this.http.get<AssetApiResponse[]>(DOMAIN_ENDPOINTS.assets, { params }).pipe(
      map((assets) => assets.map(toAsset)),
      finalize(() => this.loadingState.set(false)),
    ).subscribe({
      next: (assets) => this.assetsState.set(assets),
      error: () => this.errorState.set("Impossible de charger l'inventaire des actifs."),
    });
  }

  createAsset(payload: AssetPayload): Observable<Asset> {
    this.savingState.set(true);
    return this.http.post<AssetApiResponse>(DOMAIN_ENDPOINTS.assets, toCreateBody(payload)).pipe(
      map(toAsset),
      tap((asset) => this.assetsState.update((items) => [asset, ...items])),
      finalize(() => this.savingState.set(false)),
      catchError((error) => throwError(() => this.friendlyError(error))),
    );
  }

  updateAsset(id: string, payload: AssetPayload): Observable<Asset> {
    this.savingState.set(true);
    return this.http.patch<AssetApiResponse>(`${DOMAIN_ENDPOINTS.assets}${id}/`, toUpdateBody(payload)).pipe(
      map(toAsset),
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

interface AssetApiResponse {
  id: string;
  scope: string;
  owner: { id: number; username: string; email: string } | null;
  name: string;
  category: Asset['category'];
  description: string | null;
  confidentiality: Asset['confidentiality'];
  integrity: Asset['integrity'];
  availability: Asset['availability'];
  criticality: number;
  created_at: string;
  updated_at: string;
}

function toAsset(asset: AssetApiResponse | Asset): Asset {
  if ('scope_id' in asset) return asset;
  return {
    ...asset,
    scope_id: asset.scope,
    owner_id: asset.owner ? String(asset.owner.id) : null,
    owner_name: asset.owner?.username || asset.owner?.email || 'Non attribué',
    description: asset.description ?? '',
  };
}

function toCreateBody(payload: AssetPayload) {
  return { ...toUpdateBody(payload), scope_id: payload.scope_id };
}

function toUpdateBody(payload: AssetPayload) {
  const ownerId = payload.owner_id ? Number(payload.owner_id) : null;
  return {
    owner_id: Number.isFinite(ownerId) ? ownerId : null,
    name: payload.name,
    category: payload.category,
    description: payload.description,
    confidentiality: payload.confidentiality,
    integrity: payload.integrity,
    availability: payload.availability,
  };
}
