import { Component, effect, HostListener, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { RISK_STATUS_LABELS, Risk, RiskPayload, RiskStatus } from '../../../../core/models/governance.models';
import { AssetsService } from '../../../assets/services/assets.service';
import { RisksService } from '../../services/risks.service';

@Component({
  selector: 'app-risk-form-modal',
  imports: [ReactiveFormsModule],
  templateUrl: './risk-form-modal.component.html',
})
export class RiskFormModalComponent {
  readonly risk = input<Risk | null>(null);
  readonly closed = output<void>();
  readonly saved = output<Risk>();

  protected readonly risksService = inject(RisksService);
  protected readonly assetsService = inject(AssetsService);
  private readonly formBuilder = inject(FormBuilder);
  protected readonly submitError = signal('');
  protected readonly scores = [1, 2, 3, 4, 5] as const;
  protected readonly statuses = Object.entries(RISK_STATUS_LABELS) as [RiskStatus, string][];

  protected readonly form = this.formBuilder.nonNullable.group({
    code: ['', [Validators.required, Validators.maxLength(50)]],
    assetId: ['', Validators.required],
    threatDescription: ['', [Validators.required, Validators.maxLength(1500)]],
    likelihood: [1 as 1 | 2 | 3 | 4 | 5, [Validators.required, Validators.min(1), Validators.max(5)]],
    impact: [1 as 1 | 2 | 3 | 4 | 5, [Validators.required, Validators.min(1), Validators.max(5)]],
    status: ['OPEN' as RiskStatus, Validators.required],
  });

  constructor() {
    effect(() => {
      const risk = this.risk();
      this.form.reset({
        code: risk?.code ?? '',
        assetId: risk?.asset_id ?? '',
        threatDescription: risk?.threat_description ?? '',
        likelihood: risk?.likelihood ?? 1,
        impact: risk?.impact ?? 1,
        status: risk?.status ?? 'OPEN',
      });
      this.submitError.set('');
    });
    effect(() => {
      const firstAsset = this.assetsService.assets()[0];
      if (!this.risk() && firstAsset && !this.form.controls.assetId.value) {
        this.form.controls.assetId.setValue(firstAsset.id);
      }
    });
  }

  protected invalid(controlName: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.dirty || control.touched);
  }

  protected currentScore(): number {
    return Number(this.form.controls.likelihood.value) * Number(this.form.controls.impact.value);
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitError.set('');
    const value = this.form.getRawValue();
    if (!value.code.trim() || !value.threatDescription.trim()) {
      if (!value.code.trim()) this.form.controls.code.setErrors({ required: true });
      if (!value.threatDescription.trim()) this.form.controls.threatDescription.setErrors({ required: true });
      this.form.markAllAsTouched();
      return;
    }
    const payload: RiskPayload = {
      code: value.code.trim().toUpperCase(),
      asset_id: value.assetId,
      threat_description: value.threatDescription.trim(),
      likelihood: Number(value.likelihood) as 1 | 2 | 3 | 4 | 5,
      impact: Number(value.impact) as 1 | 2 | 3 | 4 | 5,
      status: value.status,
    };
    const request = this.risk()
      ? this.risksService.updateRisk(this.risk()!.id, payload)
      : this.risksService.createRisk(payload);
    request.subscribe({
      next: (risk) => this.saved.emit(risk),
      error: (error: Error) => this.submitError.set(error.message),
    });
  }

  protected close(): void {
    if (!this.risksService.saving()) this.closed.emit();
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    this.close();
  }
}
