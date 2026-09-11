import { Component, computed, effect, inject, signal } from '@angular/core';

import { TreatmentTask } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { EvidenceUploadModalComponent } from '../../components/evidence-upload-modal/evidence-upload-modal.component';
import { TreatmentsService } from '../../../treatments/services/treatments.service';

@Component({ selector: 'app-my-tasks-page', imports: [TopbarComponent, EvidenceUploadModalComponent], templateUrl: './my-tasks-page.component.html' })
export class MyTasksPageComponent {
  protected readonly context = inject(ContextService);
  protected readonly service = inject(TreatmentsService);
  protected readonly selectedTask = signal<TreatmentTask | null>(null);
  protected readonly tasks = computed(() => this.service.items().filter((task) => task.assignee_id === 'member-001'));
  constructor() { effect(() => { const scope = this.context.activeScopeId(); if (scope) this.service.fetch(scope); }); }
  protected complete(task: TreatmentTask): void { this.service.complete(task.id).subscribe(); }
}
