import { Component, computed, effect, inject, signal } from '@angular/core';

import { TREATMENT_STATUS_LABELS, TreatmentStatus } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { RisksService } from '../../../risks/services/risks.service';
import { SoaService } from '../../../soa/services/soa.service';
import { TreatmentFormModalComponent } from '../../components/treatment-form-modal/treatment-form-modal.component';
import { TreatmentsService } from '../../services/treatments.service';

@Component({ selector: 'app-treatments-page', imports: [TopbarComponent, TreatmentFormModalComponent], templateUrl: './treatments-page.component.html' })
export class TreatmentsPageComponent {
  protected readonly context = inject(ContextService);
  protected readonly service = inject(TreatmentsService);
  protected readonly risks = inject(RisksService);
  protected readonly soa = inject(SoaService);
  protected readonly modalOpen = signal(false);
  protected readonly statusFilter = signal<TreatmentStatus | 'ALL'>('ALL');
  protected readonly labels = TREATMENT_STATUS_LABELS;
  protected readonly visible = computed(() => this.service.items().filter((item) => this.statusFilter() === 'ALL' || item.status === this.statusFilter()));
  protected readonly completedCount = computed(() => this.service.items().filter((item) => item.status === 'COMPLETED').length);
  protected readonly controls = computed(() => this.soa.entries().map((entry) => entry.control));

  constructor() { effect(() => { const id = this.context.activeScopeId(); if (id) { this.service.fetch(id); this.risks.fetchRisks(id); this.soa.fetch(id); } }); }
  protected updateStatus(id: string, event: Event): void { this.service.setStatus(id, (event.target as HTMLSelectElement).value as TreatmentStatus).subscribe(); }
}
