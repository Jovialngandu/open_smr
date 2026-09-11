import { Component, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { IsoControl, MemberOption, Risk, TreatmentTask } from '../../../../core/models/governance.models';
import { TreatmentsService } from '../../services/treatments.service';

@Component({ selector: 'app-treatment-form-modal', imports: [ReactiveFormsModule], templateUrl: './treatment-form-modal.component.html' })
export class TreatmentFormModalComponent {
  readonly scopeId = input.required<string>();
  readonly risks = input.required<Risk[]>();
  readonly controls = input.required<IsoControl[]>();
  readonly closed = output<void>();
  readonly saved = output<TreatmentTask>();
  protected readonly service = inject(TreatmentsService);
  private readonly fb = inject(FormBuilder);
  protected readonly error = signal('');
  protected readonly members: MemberOption[] = [{ id: 'member-001', name: 'Camille Durand' }, { id: 'member-002', name: 'Nadia Bernard' }, { id: 'member-003', name: 'Thomas Leroy' }];
  protected readonly form = this.fb.nonNullable.group({ riskId: ['', Validators.required], controlId: ['', Validators.required], assigneeId: ['', Validators.required], title: ['', [Validators.required, Validators.maxLength(160)]], description: [''], dueDate: ['', Validators.required] });

  protected submit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue();
    const risk = this.risks().find((item) => item.id === value.riskId)!;
    this.service.create(this.scopeId(), risk.code, { risk_id: value.riskId, iso_control_id: value.controlId, assignee_id: value.assigneeId, title: value.title.trim(), description: value.description.trim(), due_date: value.dueDate }).subscribe({ next: (task) => this.saved.emit(task), error: () => this.error.set('La tâche n’a pas pu être créée.') });
  }
}
