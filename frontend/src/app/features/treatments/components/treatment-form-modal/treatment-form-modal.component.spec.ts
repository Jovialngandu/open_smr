import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { IsoControl, ManagedUser, Risk } from '../../../../core/models/governance.models';
import { ControlSuggestionsService } from '../../services/control-suggestions.service';
import { TreatmentsService } from '../../services/treatments.service';
import { TreatmentFormModalComponent } from './treatment-form-modal.component';

const risk = { id: 'risk-001', code: 'RSK-001', asset_name: 'Serveur' } as Risk;
const suggested = { id: 'control-1', code: 'A.8.22', title: 'Segmentation des réseaux', theme: 'TECHNOLOGICAL' } as IsoControl;
const alternative = { id: 'control-2', code: 'A.5.1', title: 'Politique de sécurité', theme: 'ORGANIZATIONAL' } as IsoControl;
const member = { id: '1', name: 'Camille Durand', role: 'RISK_OWNER', is_active: true } as ManagedUser;

describe('TreatmentFormModalComponent', () => {
  let fixture: ComponentFixture<TreatmentFormModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TreatmentFormModalComponent],
      providers: [
        { provide: TreatmentsService, useValue: { saving: signal(false) } },
        { provide: ControlSuggestionsService, useValue: { forRisk: () => of([{ ...suggested, description: 'Séparer les réseaux.' }]) } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(TreatmentFormModalComponent);
    fixture.componentRef.setInput('scopeId', 'scope-1');
    fixture.componentRef.setInput('risks', [risk]);
    fixture.componentRef.setInput('controls', [alternative, suggested]);
    fixture.componentRef.setInput('members', [member]);
    fixture.detectChanges();
  });

  it('place la première suggestion en tête et la présélectionne', async () => {
    await new Promise((resolve) => setTimeout(resolve, 400));
    fixture.detectChanges();
    const select = fixture.nativeElement.querySelector('#task-control') as HTMLSelectElement;
    expect(select.value).toBe(suggested.id);
    expect(select.querySelector('optgroup')?.label).toBe('Suggestions pour ce risque');
    expect(fixture.nativeElement.textContent).toContain('Séparer les réseaux.');
  });

  it('respecte une mesure choisie manuellement', async () => {
    await new Promise((resolve) => setTimeout(resolve, 400));
    fixture.detectChanges();
    const select = fixture.nativeElement.querySelector('#task-control') as HTMLSelectElement;
    select.value = alternative.id;
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(select.value).toBe(alternative.id);
  });
});
