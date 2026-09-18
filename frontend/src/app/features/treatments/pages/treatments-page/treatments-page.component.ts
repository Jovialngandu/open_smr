import { Component, computed, effect, inject, signal } from '@angular/core';
import { LucidePlus, LucideSearch, LucideClock3, LucideFileText, LucideCircleAlert } from '@lucide/angular';

import { TREATMENT_STATUS_LABELS, TreatmentStatus, TreatmentTask } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { AuthService } from '../../../../core/services/auth.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { RisksService } from '../../../risks/services/risks.service';
import { SoaService } from '../../../soa/services/soa.service';
import { UsersService } from '../../../users/services/users.service';
import { TreatmentFormModalComponent } from '../../components/treatment-form-modal/treatment-form-modal.component';
import { EvidenceUploadModalComponent } from '../../../my-tasks/components/evidence-upload-modal/evidence-upload-modal.component';
import { TreatmentsService } from '../../services/treatments.service';

@Component({ selector: 'app-treatments-page', imports: [TopbarComponent, TreatmentFormModalComponent, EvidenceUploadModalComponent, LucidePlus, LucideSearch, LucideClock3, LucideFileText, LucideCircleAlert], templateUrl: './treatments-page.component.html' })
export class TreatmentsPageComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
  protected readonly service = inject(TreatmentsService);
  protected readonly risks = inject(RisksService);
  protected readonly soa = inject(SoaService);
  protected readonly users = inject(UsersService);
  protected readonly modalOpen = signal(false);
  protected readonly evidenceTask = signal<TreatmentTask | null>(null);
  private readonly pendingCompletionId = signal<string | null>(null);
  protected readonly statusFilter = signal<TreatmentStatus | 'ALL'>('ALL');
  protected readonly search = signal('');
  protected readonly assigneeFilter = signal('ALL');
  protected readonly viewMode = signal<'BOARD' | 'TABLE'>('BOARD');
  protected readonly draggingId = signal<string | null>(null);
  protected readonly dropTarget = signal<TreatmentStatus | null>(null);
  protected readonly actionError = signal('');
  protected readonly labels = TREATMENT_STATUS_LABELS;
  protected readonly visible = computed(() => {
    const query = this.search().trim().toLocaleLowerCase('fr');
    return this.service.items().filter((item) =>
      (this.statusFilter() === 'ALL' || item.status === this.statusFilter()) &&
      (this.assigneeFilter() === 'ALL' || item.assignee_id === this.assigneeFilter()) &&
      (!query || [item.title, item.risk_code, item.control_code, item.assignee_name].some((value) => value.toLocaleLowerCase('fr').includes(query))),
    );
  });
  protected readonly completedCount = computed(() => this.service.items().filter((item) => item.status === 'COMPLETED').length);
  protected readonly controls = computed(() => this.soa.entries().map((entry) => entry.control));
  protected readonly assignees = computed(() => Array.from(new Map(this.service.items().map((item) => [item.assignee_id, item.assignee_name])).entries()));
  protected readonly columns: { status: TreatmentStatus; title: string; hint: string }[] = [
    { status: 'TODO', title: 'À faire', hint: 'Actions planifiées' },
    { status: 'IN_PROGRESS', title: 'En cours', hint: 'Travail engagé' },
    { status: 'COMPLETED', title: 'Terminées', hint: 'Actions justifiées' },
  ];

  constructor() { effect(() => { const id = this.context.activeScopeId(); this.evidenceTask.set(null); this.pendingCompletionId.set(null); this.modalOpen.set(false); if (id) { this.service.fetch(id); this.risks.fetchRisks(id); this.soa.fetch(id); this.users.fetch(); } }); }
  protected tasksFor(status: TreatmentStatus): TreatmentTask[] { return this.visible().filter((item) => item.status === status); }
  protected updateStatus(id: string, event: Event): void {
    const select = event.target as HTMLSelectElement;
    this.move(id, select.value as TreatmentStatus);
    select.value = this.service.items().find((item) => item.id === id)?.status ?? select.value;
  }
  protected canUpload(task: TreatmentTask): boolean { return ['ADMIN', 'RSSI'].includes(this.context.activeRole() ?? '') || task.assignee_id === this.auth.user()?.id; }
  protected dragStart(task: TreatmentTask, event: DragEvent): void { this.draggingId.set(task.id); event.dataTransfer?.setData('text/plain', task.id); if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'; }
  protected dragOver(status: TreatmentStatus, event: DragEvent): void { if (!this.draggingId()) return; event.preventDefault(); this.dropTarget.set(status); if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'; }
  protected drop(status: TreatmentStatus, event: DragEvent): void { event.preventDefault(); const id = this.draggingId(); this.draggingId.set(null); this.dropTarget.set(null); if (id) this.move(id, status); }
  protected dragEnd(): void { this.draggingId.set(null); this.dropTarget.set(null); }
  protected isOverdue(task: TreatmentTask): boolean { return task.status !== 'COMPLETED' && new Date(`${task.due_date}T23:59:59`) < new Date(); }
  protected taskSaved(): void { this.search.set(''); this.assigneeFilter.set('ALL'); this.statusFilter.set('ALL'); this.viewMode.set('BOARD'); this.modalOpen.set(false); }
  protected closeEvidence(): void { this.evidenceTask.set(null); this.pendingCompletionId.set(null); }
  protected evidenceUploaded(): void {
    const id = this.pendingCompletionId();
    this.closeEvidence(); this.actionError.set('');
    if (id) this.service.complete(id).subscribe({ error: () => this.actionError.set('La preuve a été déposée, mais le statut n’a pas pu être mis à jour.') });
  }
  private move(id: string, status: TreatmentStatus): void {
    const task = this.service.items().find((item) => item.id === id);
    if (!task || task.status === status) return;
    if (status === 'COMPLETED' && !task.evidences.length) { this.actionError.set('Ajoutez au moins une preuve avant de terminer cette tâche.'); if (this.canUpload(task)) { this.pendingCompletionId.set(id); this.evidenceTask.set(task); } return; }
    this.actionError.set('');
    this.statusFilter.set('ALL');
    this.service.setStatus(id, status).subscribe({ error: () => this.actionError.set('Le déplacement n’a pas pu être enregistré.') });
  }
}
