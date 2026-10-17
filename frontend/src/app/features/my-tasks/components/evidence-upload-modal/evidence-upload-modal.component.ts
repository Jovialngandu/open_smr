import { Component, inject, input, output, signal } from '@angular/core';
import { LucideX, LucideUpload } from '@lucide/angular';
import { FormsModule } from '@angular/forms';

import { TreatmentTask } from '../../../../core/models/governance.models';
import { TreatmentsService } from '../../../treatments/services/treatments.service';

@Component({ selector: 'app-evidence-upload-modal', imports: [FormsModule, LucideX, LucideUpload], templateUrl: './evidence-upload-modal.component.html' })
export class EvidenceUploadModalComponent {
  readonly task = input.required<TreatmentTask>();
  readonly closed = output<void>();
  readonly uploaded = output<void>();
  protected readonly service = inject(TreatmentsService);
  protected readonly selectedFile = signal<File | null>(null);
  protected readonly error = signal('');
  protected description = '';

  protected choose(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    const allowed = file && (file.type === 'application/pdf' || file.type.startsWith('image/'));
    if (!allowed || (file?.size ?? 0) > 10 * 1024 * 1024) { this.selectedFile.set(null); this.error.set('Choisissez un fichier PDF ou une image de 10 Mo maximum.'); return; }
    this.error.set(''); this.selectedFile.set(file);
  }

  protected submit(): void {
    const file = this.selectedFile();
    if (!file) { this.error.set('Sélectionnez une preuve avant de continuer.'); return; }
    this.service.uploadEvidence(this.task().id, file, this.description.trim()).subscribe({ next: () => this.uploaded.emit(), error: () => this.error.set('Le dépôt de la preuve a échoué.') });
  }
}
