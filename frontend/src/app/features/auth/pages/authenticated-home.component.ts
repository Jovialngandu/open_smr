import { Component, computed, effect, inject, signal } from '@angular/core';
import { LucideClipboardList, LucideClock3, LucideCheck, LucidePackage, LucideTriangleAlert, LucideHourglass } from '@lucide/angular';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { ContextService } from '../../../core/services/context.service';
import { TopbarComponent } from '../../../shared/components/topbar/topbar.component';
import { RiskScoreBadgeComponent } from '../../../shared/components/risk-score-badge/risk-score-badge.component';
import { AssetsService } from '../../assets/services/assets.service';
import { HeatmapComponent } from '../../dashboard/components/heatmap/heatmap.component';
import { HeatmapService } from '../../dashboard/services/heatmap.service';
import { DashboardService } from '../../dashboard/services/dashboard.service';
import { RisksService } from '../../risks/services/risks.service';
import { SoaService } from '../../soa/services/soa.service';
import { TreatmentsService } from '../../treatments/services/treatments.service';

@Component({
  selector: 'app-authenticated-home',
  imports: [TopbarComponent, HeatmapComponent, RiskScoreBadgeComponent, RouterLink, LucideClipboardList, LucideClock3, LucideCheck, LucidePackage, LucideTriangleAlert, LucideHourglass],
  templateUrl: './authenticated-home.component.html',
})
export class AuthenticatedHomeComponent {
  protected readonly auth = inject(AuthService);
  protected readonly context = inject(ContextService);
  protected readonly assets = inject(AssetsService);
  protected readonly risks = inject(RisksService);
  protected readonly heatmap = inject(HeatmapService);
  protected readonly dashboard = inject(DashboardService);
  protected readonly treatments = inject(TreatmentsService);
  protected readonly soa = inject(SoaService);
  protected readonly selectedCell = signal<{ likelihood: number; impact: number } | null>(null);
  protected readonly visibleRisks = computed(() => {
    const selected = this.selectedCell();
    return selected ? this.risks.risks().filter((risk) => risk.likelihood === selected.likelihood && risk.impact === selected.impact) : this.risks.risks().filter((risk) => risk.score >= 12);
  });
  protected readonly urgentTasks = computed(() => this.treatments.items().filter((task) => task.status !== 'COMPLETED').sort((a, b) => a.due_date.localeCompare(b.due_date)).slice(0, 4));
  protected readonly personalTasks = computed(() => this.treatments.items().filter((task) => task.assignee_id === this.auth.user()?.id));
  protected readonly personalOpenCount = computed(() => this.personalTasks().filter((task) => task.status !== 'COMPLETED').length);
  protected readonly personalEvidenceCount = computed(() => this.personalTasks().reduce((sum, task) => sum + task.evidences.length, 0));
  protected isOverdue(dueDate: string): boolean { return Boolean(dueDate) && new Date(`${dueDate}T23:59:59`) < new Date(); }

  constructor() {
    effect(() => {
      const scopeId = this.context.activeScopeId();
      if (!scopeId) return;
      this.selectedCell.set(null);
      this.treatments.fetch(scopeId);
      this.dashboard.fetch(scopeId);
      if (this.context.activeRole() === 'RISK_OWNER') {
        this.assets.fetchAssets(scopeId);
        return;
      }
      this.risks.fetchRisks(scopeId);
      this.heatmap.fetch(scopeId);
      this.soa.fetch(scopeId);
      if (this.context.activeRole() !== 'AUDITOR') this.assets.fetchAssets(scopeId);
    });
  }
}
