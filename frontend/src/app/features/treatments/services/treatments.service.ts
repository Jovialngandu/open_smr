import { HttpClient, HttpParams } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { finalize, map, Observable, tap } from 'rxjs';

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
    this.http.get<BackendTreatmentTask[]>(DOMAIN_ENDPOINTS.treatments, { params: new HttpParams().set('scope_id', scopeId) }).pipe(
      map((items) => items.map((item) => this.fromBackend(item, scopeId))),
      finalize(() => this.loadingState.set(false)),
    ).subscribe((items) => this.itemsState.set(items));
  }

  create(scopeId: string, riskCode: string, payload: TreatmentPayload): Observable<TreatmentTask> {
    this.savingState.set(true);
    const params = new HttpParams().set('scope_id', scopeId).set('risk_code', riskCode);
    const body = { title: payload.title, description: payload.description, risk: payload.risk_id, iso_control: payload.iso_control_id, assignee: payload.assignee_id, due_date: payload.due_date };
    return this.http.post<BackendTreatmentTask>(DOMAIN_ENDPOINTS.treatments, body, { params }).pipe(
      map((created) => this.fromBackend(created, scopeId)),
      tap((created) => this.itemsState.update((items) => [created, ...items])),
      finalize(() => this.savingState.set(false)),
    );
  }

  setStatus(id: string, status: TreatmentStatus): Observable<TreatmentTask> {
    const previous = this.itemsState();
    this.itemsState.update((items) => items.map((item) => item.id === id ? { ...item, status } : item));
    const current = previous.find((item) => item.id === id);
    return this.http.patch<BackendTreatmentTask>(`${DOMAIN_ENDPOINTS.treatments}${id}/status/`, { status }).pipe(
      map((updated) => this.fromBackend(updated, current?.scope_id ?? '')),
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
    return this.http.post<BackendEvidence>(DOMAIN_ENDPOINTS.evidences, form).pipe(
      map((evidence) => this.evidenceFromBackend(evidence)),
      tap((evidence) => this.itemsState.update((items) => items.map((item) => item.id === taskId ? { ...item, evidences: [...item.evidences, evidence] } : item))),
      finalize(() => this.savingState.set(false)),
    );
  }

  private replace(updated: TreatmentTask): void {
    this.itemsState.update((items) => items.map((item) => item.id === updated.id ? updated : item));
  }

  private fromBackend(task: BackendTreatmentTask, scopeId: string): TreatmentTask {
    return {
      id: task.id,
      scope_id: task.scope_id ?? scopeId,
      risk_id: task.risk_id ?? task.risk,
      risk_code: task.risk_code,
      iso_control_id: task.iso_control_id ?? task.iso_control,
      control_code: task.control_code ?? task.iso_control_code,
      assignee_id: task.assignee_id ?? task.assignee ?? '',
      assignee_name: task.assignee_name ?? task.assignee_email ?? 'Non attribué',
      title: task.title,
      description: task.description ?? '',
      due_date: task.due_date ?? '',
      status: task.status,
      completed_at: task.completed_at,
      evidences: (task.evidences ?? []).map((evidence) => this.evidenceFromBackend(evidence)),
    };
  }

  private evidenceFromBackend(evidence: BackendEvidence): Evidence {
    const filePath = evidence.file_path ?? evidence.download_url ?? '';
    return {
      id: evidence.id,
      task_id: evidence.task_id ?? evidence.task,
      file_name: evidence.file_name ?? filePath.split('/').pop() ?? 'preuve',
      file_type: evidence.file_type ?? '',
      description: evidence.description ?? '',
      uploaded_by_name: evidence.uploaded_by_name ?? evidence.uploaded_by_email ?? 'Utilisateur',
      uploaded_at: evidence.uploaded_at ?? evidence.created_at,
      download_url: evidence.download_url ?? filePath,
    };
  }
}

interface BackendEvidence {
  id: string;
  task: string;
  task_id?: string;
  file_path?: string;
  file_name?: string;
  file_type?: string;
  description?: string;
  uploaded_by_name?: string;
  uploaded_by_email?: string;
  uploaded_at?: string;
  download_url?: string;
  created_at: string;
}

interface BackendTreatmentTask {
  id: string;
  scope_id?: string;
  risk: string;
  risk_id?: string;
  risk_code: string;
  iso_control: string;
  iso_control_id?: string;
  iso_control_code: string;
  control_code?: string;
  assignee: string | null;
  assignee_id?: string;
  assignee_name?: string;
  assignee_email?: string;
  title: string;
  description: string;
  due_date: string | null;
  status: TreatmentStatus;
  completed_at: string | null;
  evidences: BackendEvidence[];
}
