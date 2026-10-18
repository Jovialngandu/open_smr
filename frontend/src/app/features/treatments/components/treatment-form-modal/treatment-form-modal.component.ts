import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LucideX } from '@lucide/angular';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { catchError, combineLatest, debounceTime, distinctUntilChanged, finalize, of, startWith, switchMap } from 'rxjs';

import { IsoControl, ManagedUser, Risk, TreatmentTask } from '../../../../core/models/governance.models';
import { TreatmentsService } from '../../services/treatments.service';
import { ControlSuggestion, ControlSuggestionsService } from '../../services/control-suggestions.service';

@Component({ selector: 'app-treatment-form-modal', imports: [ReactiveFormsModule, LucideX], templateUrl: './treatment-form-modal.component.html' })
export class TreatmentFormModalComponent {
  readonly scopeId = input.required<string>();
  readonly risks = input.required<Risk[]>();
  readonly controls = input.required<IsoControl[]>();
  readonly members = input.required<ManagedUser[]>();
  readonly closed = output<void>();
  readonly saved = output<TreatmentTask>();
  protected readonly service = inject(TreatmentsService);
  private readonly suggestionService = inject(ControlSuggestionsService);
  private readonly fb = inject(FormBuilder);
  protected readonly error = signal('');
  protected readonly suggestions = signal<ControlSuggestion[]>([]);
  protected readonly suggestionsLoading = signal(false);
  protected readonly suggestionsUnavailable = signal(false);
  protected readonly selectedSuggestion = signal<ControlSuggestion | null>(null);
  private userSelectedControl = false;
  protected readonly form = this.fb.nonNullable.group({ riskId: ['', Validators.required], controlId: ['', Validators.required], assigneeId: ['', Validators.required], title: ['', [Validators.required, Validators.maxLength(255)]], description: [''], dueDate: ['', Validators.required] });
  protected readonly suggestedControls = computed(() => this.suggestions().flatMap((suggestion) => {
    const control = this.controls().find((item) => item.code === suggestion.code);
    return control ? [{ control, suggestion }] : [];
  }));
  protected readonly otherControls = computed(() => {
    const suggestedIds = new Set(this.suggestedControls().map((item) => item.control.id));
    return this.controls().filter((control) => !suggestedIds.has(control.id));
  });

  constructor() {
    effect(() => { const risk = this.risks()[0]; if (risk && !this.form.controls.riskId.value) this.form.controls.riskId.setValue(risk.id); });
    effect(() => {
      const control = this.suggestedControls()[0]?.control ?? this.controls()[0];
      if (control && !this.userSelectedControl) this.form.controls.controlId.setValue(control.id, { emitEvent: false });
      this.syncSelectedSuggestion();
    });
    effect(() => { const member = this.members().find((item) => item.is_active); if (member && !this.form.controls.assigneeId.value) this.form.controls.assigneeId.setValue(member.id); });

    this.form.controls.riskId.valueChanges.pipe(takeUntilDestroyed()).subscribe(() => {
      this.userSelectedControl = false;
      this.suggestions.set([]);
    });
    combineLatest([
      this.form.controls.riskId.valueChanges.pipe(startWith(this.form.controls.riskId.value)),
      this.form.controls.title.valueChanges.pipe(startWith(this.form.controls.title.value)),
    ]).pipe(
      debounceTime(350),
      distinctUntilChanged(([riskA, titleA], [riskB, titleB]) => riskA === riskB && titleA.trim() === titleB.trim()),
      switchMap(([riskId, title]) => {
        this.suggestions.set([]);
        this.suggestionsUnavailable.set(false);
        if (!riskId) return of([] as ControlSuggestion[]);
        this.suggestionsLoading.set(true);
        return this.suggestionService.forRisk(riskId, title).pipe(
          catchError(() => {
            this.suggestionsUnavailable.set(true);
            return of([] as ControlSuggestion[]);
          }),
          finalize(() => this.suggestionsLoading.set(false)),
        );
      }),
      takeUntilDestroyed(),
    ).subscribe((response) => this.suggestions.set(Array.isArray(response) ? response : []));
  }

  protected controlChanged(): void {
    this.userSelectedControl = true;
    this.syncSelectedSuggestion();
  }

  private syncSelectedSuggestion(): void {
    this.selectedSuggestion.set(this.suggestedControls().find((item) => item.control.id === this.form.controls.controlId.value)?.suggestion ?? null);
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
