import { Component, effect, HostListener, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import {
  ASSET_CATEGORY_LABELS,
  Asset,
  AssetCategory,
  AssetPayload,
  MemberOption,
} from '../../../../core/models/governance.models';
import { AssetsService } from '../../services/assets.service';

@Component({
  selector: 'app-asset-form-modal',
  imports: [ReactiveFormsModule],
  templateUrl: './asset-form-modal.component.html',
})
export class AssetFormModalComponent {
  readonly asset = input<Asset | null>(null);
  readonly scopeId = input.required<string>();
  readonly members = input<MemberOption[]>([]);
  readonly closed = output<void>();
  readonly saved = output<Asset>();

  protected readonly assetsService = inject(AssetsService);
  private readonly formBuilder = inject(FormBuilder);
  protected readonly submitError = signal('');
  protected readonly categories = Object.entries(ASSET_CATEGORY_LABELS) as [AssetCategory, string][];
  protected readonly scores = [1, 2, 3] as const;

  protected readonly form = this.formBuilder.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    category: ['SOFTWARE' as AssetCategory, Validators.required],
    ownerId: [''],
    description: ['', Validators.maxLength(1000)],
    confidentiality: [1 as 1 | 2 | 3, [Validators.required, Validators.min(1), Validators.max(3)]],
    integrity: [1 as 1 | 2 | 3, [Validators.required, Validators.min(1), Validators.max(3)]],
    availability: [1 as 1 | 2 | 3, [Validators.required, Validators.min(1), Validators.max(3)]],
  });

  constructor() {
    effect(() => {
      const asset = this.asset();
      this.form.reset({
        name: asset?.name ?? '',
        category: asset?.category ?? 'SOFTWARE',
        ownerId: asset?.owner_id ?? '',
        description: asset?.description ?? '',
        confidentiality: asset?.confidentiality ?? 1,
        integrity: asset?.integrity ?? 1,
        availability: asset?.availability ?? 1,
      });
      this.submitError.set('');
    });
  }

  protected invalid(controlName: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.dirty || control.touched);
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitError.set('');
    const value = this.form.getRawValue();
    if (!value.name.trim()) {
      this.form.controls.name.setErrors({ required: true });
      this.form.controls.name.markAsTouched();
      return;
    }
    const payload: AssetPayload = {
      scope_id: this.scopeId(),
      name: value.name.trim(),
      category: value.category,
      owner_id: value.ownerId || null,
      description: value.description.trim(),
      confidentiality: Number(value.confidentiality) as 1 | 2 | 3,
      integrity: Number(value.integrity) as 1 | 2 | 3,
      availability: Number(value.availability) as 1 | 2 | 3,
    };
    const request = this.asset()
      ? this.assetsService.updateAsset(this.asset()!.id, payload)
      : this.assetsService.createAsset(payload);
    request.subscribe({
      next: (asset) => this.saved.emit(asset),
      error: (error: Error) => this.submitError.set(error.message),
    });
  }

  protected close(): void {
    if (!this.assetsService.saving()) this.closed.emit();
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    this.close();
  }
}
