import { HttpClient, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { finalize, tap } from 'rxjs';

import { DOMAIN_ENDPOINTS, soaExportEndpoint } from '../../../core/config/api.config';
import { SoaEntry, SoaVersion } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class SoaService {
  private readonly http = inject(HttpClient);
  private readonly entriesState = signal<SoaEntry[]>([]);
  private readonly loadingState = signal(false);
  private readonly savingIdsState = signal<Set<string>>(new Set());
  private readonly versionsState = signal<SoaVersion[]>([]);
  readonly entries = this.entriesState.asReadonly();
  readonly loading = this.loadingState.asReadonly();
  readonly savingIds = this.savingIdsState.asReadonly();
  readonly versions = this.versionsState.asReadonly();
  readonly compliance = computed(() => {
    const applicable = this.entriesState().filter((entry) => entry.is_applicable);
    return applicable.length ? Math.round(applicable.filter((entry) => entry.implementation_status === 'IMPLEMENTED').length / applicable.length * 100) : 0;
  });

  fetch(scopeId: string): void {
    this.loadingState.set(true);
    this.http.get<SoaEntry[]>(DOMAIN_ENDPOINTS.soaEntries, { params: new HttpParams().set('scope_id', scopeId) }).pipe(finalize(() => this.loadingState.set(false))).subscribe((entries) => this.entriesState.set(entries));
    this.http.get<SoaVersion[]>(DOMAIN_ENDPOINTS.soaVersions, { params: new HttpParams().set('scope_id', scopeId) }).subscribe((versions) => this.versionsState.set(versions));
  }

  createVersion(scopeId: string, title: string): void {
    this.http.post<SoaVersion>(DOMAIN_ENDPOINTS.soaVersions, { scope_id: scopeId, title }).subscribe((version) => this.versionsState.update((versions) => [version, ...versions]));
  }

  update(id: string, changes: Pick<SoaEntry, 'is_applicable' | 'justification'>): void {
    this.savingIdsState.update((ids) => new Set(ids).add(id));
    this.http.patch<SoaEntry>(`${DOMAIN_ENDPOINTS.soa}${id}/`, changes).pipe(finalize(() => this.savingIdsState.update((ids) => { const next = new Set(ids); next.delete(id); return next; }))).subscribe((updated) => this.entriesState.update((entries) => entries.map((entry) => entry.id === id ? updated : entry)));
  }

//   export(scopeId: string, format: 'pdf' | 'csv'): void {
//     const params = new HttpParams().set('format', format);
//     this.http.get(soaExportEndpoint(scopeId, format), { params, responseType: 'blob' }).subscribe((blob) => {
//       const url = URL.createObjectURL(blob);
//       const anchor = document.createElement('a');
//       anchor.href = url;
//       anchor.download = `soa-${scopeId}.${format}`;
//       anchor.click();
//       URL.revokeObjectURL(url);
//     });
//   }
export(scopeId: string, format: 'pdf' | 'xlsx' = 'pdf'): void {
  // Utilisez un nom de paramètre distinct pour éviter le conflit avec le 'format' interne de DRF
  const params = new HttpParams().set('file_type', format);

  this.http.get(soaExportEndpoint(scopeId), { 
    params, 
    responseType: 'blob' 
  }).subscribe({
    next: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `soa-${scopeId}.${format}`;
      anchor.click();
      window.URL.revokeObjectURL(url);
    },
    error: (err) => {
      console.error("Erreur lors de l'export SoA :", err);
    }
  });
}
}
