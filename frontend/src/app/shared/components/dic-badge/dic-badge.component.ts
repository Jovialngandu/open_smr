import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-dic-badge',
  templateUrl: './dic-badge.component.html',
})
export class DicBadgeComponent {
  readonly confidentiality = input.required<number>();
  readonly integrity = input.required<number>();
  readonly availability = input.required<number>();
  readonly compact = input(false);

  protected readonly criticality = computed(() =>
    Math.max(this.confidentiality(), this.integrity(), this.availability()),
  );
  protected readonly levelLabel = computed(() =>
    ({ 1: 'Faible', 2: 'Modérée', 3: 'Élevée' })[this.criticality()] ?? 'Inconnue',
  );
}
