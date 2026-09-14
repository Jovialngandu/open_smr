import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { Asset } from '../../../../core/models/governance.models';
import { AssetsService } from '../../../assets/services/assets.service';
import { RisksService } from '../../services/risks.service';
import { RiskFormModalComponent } from './risk-form-modal.component';

const asset: Asset = { id: 'asset-test', scope_id: 'scope-test', owner_id: null, owner_name: 'Non attribué', name: 'Actif test', category: 'DATA', description: '', confidentiality: 2, integrity: 2, availability: 2, criticality: 2, created_at: '', updated_at: '' };

describe('RiskFormModalComponent', () => {
  let fixture: ComponentFixture<RiskFormModalComponent>;
  const assets = signal<Asset[]>([asset]);

  beforeEach(async () => {
    assets.set([asset]);
    await TestBed.configureTestingModule({
      imports: [RiskFormModalComponent],
      providers: [
        { provide: AssetsService, useValue: { assets, loading: signal(false) } },
        { provide: RisksService, useValue: { saving: signal(false), createRisk: () => of(null) } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(RiskFormModalComponent);
    fixture.detectChanges();
  });

  it('sélectionne le premier actif disponible après son chargement', () => {
    const form = (fixture.componentInstance as unknown as { form: { controls: { assetId: { value: string } } } }).form;
    expect(form.controls.assetId.value).toBe(asset.id);
  });

  it('conserve une sélection faite par l’utilisateur', () => {
    const form = (fixture.componentInstance as unknown as { form: { controls: { assetId: { setValue(value: string): void; value: string } } } }).form;
    form.controls.assetId.setValue('choix-utilisateur');
    assets.set([{ ...asset, id: 'nouvel-actif' }]);
    fixture.detectChanges();
    expect(form.controls.assetId.value).toBe('choix-utilisateur');
  });
});
