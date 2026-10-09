import { HttpClient, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { finalize, map } from 'rxjs';

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
    this.http.get<BackendSoaEntry[]>(DOMAIN_ENDPOINTS.soaEntries, { params: new HttpParams().set('scope_id', scopeId) }).pipe(map((entries) => entries.map(toSoaEntry)), finalize(() => this.loadingState.set(false))).subscribe((entries) => this.entriesState.set(entries));
    this.http.get<BackendSoaVersion[]>(DOMAIN_ENDPOINTS.soaVersions, { params: new HttpParams().set('scope_id', scopeId) }).pipe(map((versions) => versions.map(toSoaVersion))).subscribe((versions) => this.versionsState.set(versions));
  }

  createVersion(scopeId: string, title: string): void {
    this.http.post<BackendSoaVersion>(DOMAIN_ENDPOINTS.soaVersions, { scope_id: scopeId, title }).pipe(map(toSoaVersion)).subscribe((version) => this.versionsState.update((versions) => [version, ...versions]));
  }

  update(id: string, changes: Pick<SoaEntry, 'is_applicable' | 'justification'>): void {
    this.savingIdsState.update((ids) => new Set(ids).add(id));
    this.http.patch<BackendSoaEntry>(`${DOMAIN_ENDPOINTS.soaEntries}${id}/`, changes).pipe(map(toSoaEntry), finalize(() => this.savingIdsState.update((ids) => { const next = new Set(ids); next.delete(id); return next; }))).subscribe((updated) => this.entriesState.update((entries) => entries.map((entry) => entry.id === id ? updated : entry)));
  }

  export(scopeId: string, format: 'pdf' | 'xlsx' = 'pdf'): void {
    const params = new HttpParams().set('file_type', format);
    this.http.get(soaExportEndpoint(scopeId), { params, responseType: 'blob' }).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `soa-${scopeId}.${format}`;
        anchor.click();
        URL.revokeObjectURL(url);
      },
      error: () => undefined,
    });
  }
}

type BackendSoaEntry = SoaEntry & { scope?: string; scope_id?: string; updated_by_name?: string };
type BackendSoaVersion = SoaVersion & { scope?: string; scope_id?: string; approved_by?: { username: string; email: string } | null; approved_by_name?: string | null };

function toSoaEntry(entry: BackendSoaEntry): SoaEntry {
  return { ...entry, scope_id: entry.scope_id ?? entry.scope ?? '', updated_by_name: entry.updated_by_name ?? 'Non renseigné' };
}

function toSoaVersion(version: BackendSoaVersion): SoaVersion {
  return { ...version, scope_id: version.scope_id ?? version.scope ?? '', approved_by_name: version.approved_by_name ?? version.approved_by?.username ?? null };
}
