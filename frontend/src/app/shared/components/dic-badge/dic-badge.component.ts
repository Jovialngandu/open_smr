import { Component, computed, input } from '@angular/core';
import { assessmentLevel, DIC_LEVELS } from '../../../core/models/assessment-scale';

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
    assessmentLevel(DIC_LEVELS, this.criticality()).label,
  );
  protected readonly description = computed(() =>
    `Confidentialité : ${assessmentLevel(DIC_LEVELS, this.confidentiality()).label}. ` +
    `Intégrité : ${assessmentLevel(DIC_LEVELS, this.integrity()).label}. ` +
    `Disponibilité : ${assessmentLevel(DIC_LEVELS, this.availability()).label}.`,
  );
}
