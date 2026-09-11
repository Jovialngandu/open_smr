import { Component, computed, effect, inject } from '@angular/core';

import { CONTROL_THEME_LABELS, IMPLEMENTATION_STATUS_LABELS, Evidence } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { RiskScoreBadgeComponent } from '../../../../shared/components/risk-score-badge/risk-score-badge.component';
import { RisksService } from '../../../risks/services/risks.service';
import { SoaService } from '../../../soa/services/soa.service';
import { TreatmentsService } from '../../../treatments/services/treatments.service';

@Component({ selector: 'app-audit-view-page', imports: [TopbarComponent, RiskScoreBadgeComponent], templateUrl: './audit-view-page.component.html' })
export class AuditViewPageComponent {
  protected readonly context = inject(ContextService);
  protected readonly risks = inject(RisksService);
  protected readonly soa = inject(SoaService);
  protected readonly treatments = inject(TreatmentsService);
  protected readonly themes = CONTROL_THEME_LABELS;
  protected readonly statuses = IMPLEMENTATION_STATUS_LABELS;
  protected readonly evidences = computed(() => this.treatments.items().flatMap((task) => task.evidences.map((evidence) => ({ ...evidence, taskTitle: task.title, controlCode: task.control_code }))));
  constructor() { effect(() => { const scope = this.context.activeScopeId(); if (scope) { this.risks.fetchRisks(scope); this.soa.fetch(scope); this.treatments.fetch(scope); } }); }
  protected download(evidence: Evidence): void { const blob = new Blob([`Preuve simulée : ${evidence.file_name}`], { type: evidence.file_type || 'text/plain' }); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = evidence.file_name; anchor.click(); URL.revokeObjectURL(url); }
}
