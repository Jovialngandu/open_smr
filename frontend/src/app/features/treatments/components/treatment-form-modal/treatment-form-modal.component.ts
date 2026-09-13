import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { IsoControl, ManagedUser, Risk, TreatmentTask } from '../../../../core/models/governance.models';
import { TreatmentsService } from '../../services/treatments.service';

@Component({ selector: 'app-treatment-form-modal', imports: [ReactiveFormsModule], templateUrl: './treatment-form-modal.component.html' })
export class TreatmentFormModalComponent {
  readonly scopeId = input.required<string>();
  readonly risks = input.required<Risk[]>();
  readonly controls = input.required<IsoControl[]>();
  readonly members = input.required<ManagedUser[]>();
  readonly closed = output<void>();
  readonly saved = output<TreatmentTask>();
  protected readonly service = inject(TreatmentsService);
  private readonly fb = inject(FormBuilder);
  protected readonly error = signal('');
  protected readonly form = this.fb.nonNullable.group({ riskId: ['', Validators.required], controlId: ['', Validators.required], assigneeId: ['', Validators.required], title: ['', [Validators.required, Validators.maxLength(255)]], description: [''], dueDate: ['', Validators.required] });

  constructor() {
    effect(() => { const risk = this.risks()[0]; if (risk && !this.form.controls.riskId.value) this.form.controls.riskId.setValue(risk.id); });
    effect(() => { const control = this.controls()[0]; if (control && !this.form.controls.controlId.value) this.form.controls.controlId.setValue(control.id); });
    effect(() => { const member = this.members().find((item) => item.is_active); if (member && !this.form.controls.assigneeId.value) this.form.controls.assigneeId.setValue(member.id); });
  }

  protected submit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue();
    if (!value.title.trim()) { this.form.controls.title.setErrors({ required: true }); this.form.controls.title.markAsTouched(); return; }
    const risk = this.risks().find((item) => item.id === value.riskId);
    if (!risk) { this.error.set('Sélectionnez un risque valide.'); return; }
    this.service.create(this.scopeId(), risk.code, { risk_id: value.riskId, iso_control_id: value.controlId, assignee_id: value.assigneeId, title: value.title.trim(), description: value.description.trim(), due_date: value.dueDate }).subscribe({ next: (task) => this.saved.emit(task), error: () => this.error.set('La tâche n’a pas pu être créée.') });
  }
}
