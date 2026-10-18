import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { LucideSearch } from '@lucide/angular';

import { CONTROL_THEME_LABELS, ControlTheme } from '../../../core/models/governance.models';
import { TopbarComponent } from '../../../shared/components/topbar/topbar.component';

interface IsoControlReference {
  code: string;
  title: string;
  theme: ControlTheme;
  description: string;
  keywords: string;
}

@Component({
  selector: 'app-controls-catalog-page',
  imports: [TopbarComponent, LucideSearch],
  templateUrl: './controls-catalog-page.component.html',
  styleUrl: './controls-catalog-page.component.scss',
})
export class ControlsCatalogPageComponent {
  private readonly http = inject(HttpClient);
  private readonly controlsState = signal<IsoControlReference[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly search = signal('');
  protected readonly theme = signal<ControlTheme | 'ALL'>('ALL');
  protected readonly controls = this.controlsState.asReadonly();
  protected readonly themeLabels = CONTROL_THEME_LABELS;
  protected readonly themes = Object.entries(CONTROL_THEME_LABELS) as [ControlTheme, string][];
  protected readonly visible = computed(() => {
    const query = this.search().trim().toLocaleLowerCase('fr');
    return this.controlsState().filter((control) =>
      (this.theme() === 'ALL' || control.theme === this.theme()) &&
      (!query || [control.code, control.title, control.description, control.keywords]
        .some((value) => value.toLocaleLowerCase('fr').includes(query))),
    );
  });

  constructor() { this.load(); }

  protected load(): void {
    this.loading.set(true);
    this.error.set('');
    this.http.get<IsoControlReference[]>('/data/iso-controls.json').subscribe({
      next: (controls) => {
        this.controlsState.set(controls);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Impossible de charger le référentiel des mesures. Réessayez.');
        this.loading.set(false);
      },
    });
  }
}
