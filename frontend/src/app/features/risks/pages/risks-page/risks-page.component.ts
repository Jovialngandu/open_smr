import { Component, computed, effect, inject, signal } from '@angular/core';
import { LucidePlus, LucideShieldAlert, LucideCheck, LucideSearch } from '@lucide/angular';

import { RISK_STATUS_LABELS, Risk, RiskStatus } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { RiskScoreBadgeComponent } from '../../../../shared/components/risk-score-badge/risk-score-badge.component';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { AssetsService } from '../../../assets/services/assets.service';
import { RiskFormModalComponent } from '../../components/risk-form-modal/risk-form-modal.component';
import { RisksService } from '../../services/risks.service';

@Component({
  selector: 'app-risks-page',
  imports: [TopbarComponent, RiskScoreBadgeComponent, RiskFormModalComponent, LucidePlus, LucideShieldAlert, LucideCheck, LucideSearch],
  templateUrl: './risks-page.component.html',
})
export class RisksPageComponent {
  protected readonly risksService = inject(RisksService);
  protected readonly assetsService = inject(AssetsService);
  protected readonly context = inject(ContextService);
  protected readonly search = signal('');
  protected readonly status = signal<RiskStatus | 'ALL'>('ALL');
  protected readonly modalOpen = signal(false);
  protected readonly selectedRisk = signal<Risk | null>(null);
  protected readonly actionError = signal('');
  protected readonly successMessage = signal('');
  protected readonly statusLabels = RISK_STATUS_LABELS;
  protected readonly statuses = Object.entries(RISK_STATUS_LABELS) as [RiskStatus, string][];
  protected readonly editable = computed(() => ['ADMIN', 'RSSI'].includes(this.context.activeRole() ?? ''));

  protected readonly filteredRisks = computed(() => {
    const query = this.search().trim().toLocaleLowerCase('fr');
    const status = this.status();
    return this.risksService.risks().filter((risk) => {
      const matchesStatus = status === 'ALL' || risk.status === status;
      const matchesSearch = !query || [risk.code, risk.asset_name, risk.threat_description]
        .some((value) => value.toLocaleLowerCase('fr').includes(query));
      return matchesStatus && matchesSearch;
    });
  });

  protected readonly activeScopeName = computed(() => {
    const scopeId = this.context.activeScopeId();
    return this.context.activeOrganization()?.scopes?.find((scope) => scope.id === scopeId)?.name ?? '—';
  });

  constructor() {
    effect(() => {
      const scopeId = this.context.activeScopeId();
      if (scopeId) {
        this.risksService.fetchRisks(scopeId);
        if (this.editable()) this.assetsService.fetchAssets(scopeId);
      }
    });
  }

  protected openCreate(): void {
    this.successMessage.set('');
    this.selectedRisk.set(null);
    this.modalOpen.set(true);
  }

  protected openEdit(risk: Risk): void {
    this.selectedRisk.set(risk);
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
    this.selectedRisk.set(null);
  }

  protected riskSaved(risk: Risk): void {
    this.search.set('');
    this.status.set('ALL');
    this.successMessage.set(`Le risque « ${risk.code} » a bien été enregistré.`);
    this.closeModal();
  }

  protected deleteRisk(risk: Risk): void {
    if (!confirm(`Supprimer le risque « ${risk.code} » ?`)) return;
    this.actionError.set('');
    this.risksService.deleteRisk(risk.id).subscribe({
      error: (error: Error) => this.actionError.set(error.message),
    });
  }
}
