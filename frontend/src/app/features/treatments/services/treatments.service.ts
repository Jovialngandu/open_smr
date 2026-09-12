import { HttpClient, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { finalize, Observable, tap } from 'rxjs';

import { DOMAIN_ENDPOINTS } from '../../../core/config/api.config';
import { Evidence, TreatmentPayload, TreatmentStatus, TreatmentTask } from '../../../core/models/governance.models';

@Injectable({ providedIn: 'root' })
export class TreatmentsService {
  private readonly http = inject(HttpClient);
  private readonly itemsState = signal<TreatmentTask[]>([]);
  private readonly loadingState = signal(false);
  private readonly savingState = signal(false);
  readonly items = this.itemsState.asReadonly();
  readonly loading = this.loadingState.asReadonly();
  readonly saving = this.savingState.asReadonly();
  readonly overdueCount = computed(() => this.itemsState().filter((item) => item.status !== 'COMPLETED' && new Date(item.due_date) < new Date()).length);

  fetch(scopeId: string): void {
    this.loadingState.set(true);
    this.http.get<TreatmentTask[]>(DOMAIN_ENDPOINTS.treatments, { params: new HttpParams().set('scope_id', scopeId) }).pipe(finalize(() => this.loadingState.set(false))).subscribe((items) => this.itemsState.set(items));
  }

  create(scopeId: string, riskCode: string, payload: TreatmentPayload): Observable<TreatmentTask> {
    this.savingState.set(true);
    const params = new HttpParams().set('scope_id', scopeId).set('risk_code', riskCode);
    const body = { title: payload.title, description: payload.description, risk: payload.risk_id, iso_control: payload.iso_control_id, assignee: payload.assignee_id, due_date: payload.due_date };
    return this.http.post<TreatmentTask>(DOMAIN_ENDPOINTS.treatments, body, { params }).pipe(tap((created) => this.itemsState.update((items) => [created, ...items])), finalize(() => this.savingState.set(false)));
  }

  setStatus(id: string, status: TreatmentStatus): Observable<TreatmentTask> {
    const previous = this.itemsState();
    this.itemsState.update((items) => items.map((item) => item.id === id ? { ...item, status } : item));
    return this.http.patch<TreatmentTask>(`${DOMAIN_ENDPOINTS.treatments}${id}/status/`, { status }).pipe(
      tap({ next: (updated) => this.replace(updated), error: () => this.itemsState.set(previous) }),
    );
  }

  complete(id: string): Observable<TreatmentTask> {
    return this.setStatus(id, 'COMPLETED');
  }

  uploadEvidence(taskId: string, file: File, description: string): Observable<Evidence> {
    this.savingState.set(true);
    const form = new FormData();
    form.append('task_id', taskId);
    form.append('file_path', file);
    form.append('description', description);
    return this.http.post<Evidence>(DOMAIN_ENDPOINTS.evidences, form).pipe(tap((evidence) => this.itemsState.update((items) => items.map((item) => item.id === taskId ? { ...item, evidences: [...item.evidences, evidence] } : item))), finalize(() => this.savingState.set(false)));
  }

  private replace(updated: TreatmentTask): void {
    this.itemsState.update((items) => items.map((item) => item.id === updated.id ? updated : item));
  }
}
