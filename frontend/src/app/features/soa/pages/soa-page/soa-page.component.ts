import { Component, computed, effect, inject, signal } from '@angular/core';
import { LucideSearch } from '@lucide/angular';

import { CONTROL_THEME_LABELS, ControlTheme, IMPLEMENTATION_STATUS_LABELS, SoaEntry, SoaVersion } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { SoaService } from '../../services/soa.service';

@Component({ selector: 'app-soa-page', imports: [TopbarComponent, LucideSearch], templateUrl: './soa-page.component.html', styleUrl: './soa-page.component.scss' })
export class SoaPageComponent {
  protected readonly context = inject(ContextService);
  protected readonly service = inject(SoaService);
  protected readonly search = signal('');
  protected readonly theme = signal<ControlTheme | 'ALL'>('ALL');
  protected readonly selectedVersion = signal<SoaVersion | null>(null);
  protected readonly snapshotSearch = signal('');
  protected readonly snapshotEntries = computed(() => {
    const query = this.snapshotSearch().trim().toLocaleLowerCase('fr');
    return (this.selectedVersion()?.snapshot_data ?? []).filter((entry) => !query || `${entry.control_code} ${entry.control_title} ${entry.justification}`.toLocaleLowerCase('fr').includes(query));
  });
  protected readonly versionTitle = signal('Revue de la déclaration d’applicabilité');
  protected readonly themeLabels = CONTROL_THEME_LABELS;
  protected readonly implementationLabels = IMPLEMENTATION_STATUS_LABELS;
  protected readonly editable = computed(() => this.context.activeRole() === 'ADMIN' || this.context.activeRole() === 'RSSI');
  protected readonly visible = computed(() => { const query = this.search().toLowerCase(); return this.service.entries().filter((entry) => (this.theme() === 'ALL' || entry.iso_control.theme === this.theme()) && (!query || `${entry.iso_control.code} ${entry.iso_control.title} ${entry.justification}`.toLowerCase().includes(query))); });
  constructor() { effect(() => { const scope = this.context.activeScopeId(); this.selectedVersion.set(null); if (scope) this.service.fetch(scope); }); }
  protected openVersion(version: SoaVersion): void { this.snapshotSearch.set(''); this.selectedVersion.set(version); }
  protected closeVersion(): void { this.selectedVersion.set(null); }
  protected toggle(entry: SoaEntry, event: Event): void { this.service.update(entry.id, { is_applicable: (event.target as HTMLInputElement).checked, justification: entry.justification }); }
  protected saveJustification(entry: SoaEntry, event: Event): void { const justification = (event.target as HTMLTextAreaElement).value.trim(); if (justification !== entry.justification) this.service.update(entry.id, { is_applicable: entry.is_applicable, justification }); }
  protected export(format: 'pdf' | 'xlsx'): void { const scope = this.context.activeScopeId(); if (scope) this.service.export(scope, format); }
  protected createVersion(): void { const scope = this.context.activeScopeId(); const title = this.versionTitle().trim(); if (scope && title) this.service.createVersion(scope, title); }
}
