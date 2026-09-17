import { Component, computed, effect, inject, signal } from '@angular/core';
import { LucidePlus, LucidePackage, LucideCheck, LucideSearch } from '@lucide/angular';

import { ASSET_CATEGORY_LABELS, Asset, AssetCategory, MemberOption } from '../../../../core/models/governance.models';
import { ContextService } from '../../../../core/services/context.service';
import { TopbarComponent } from '../../../../shared/components/topbar/topbar.component';
import { DicBadgeComponent } from '../../../../shared/components/dic-badge/dic-badge.component';
import { AssetFormModalComponent } from '../../components/asset-form-modal/asset-form-modal.component';
import { AssetsService } from '../../services/assets.service';
import { UsersService } from '../../../users/services/users.service';

@Component({
  selector: 'app-assets-page',
  imports: [TopbarComponent, DicBadgeComponent, AssetFormModalComponent, LucidePlus, LucidePackage, LucideCheck, LucideSearch],
  templateUrl: './assets-page.component.html',
})
export class AssetsPageComponent {
  protected readonly assetsService = inject(AssetsService);
  protected readonly context = inject(ContextService);
  protected readonly usersService = inject(UsersService);
  protected readonly search = signal('');
  protected readonly category = signal<AssetCategory | 'ALL'>('ALL');
  protected readonly modalOpen = signal(false);
  protected readonly selectedAsset = signal<Asset | null>(null);
  protected readonly actionError = signal('');
  protected readonly successMessage = signal('');
  protected readonly categoryLabels = ASSET_CATEGORY_LABELS;
  protected readonly categories = Object.entries(ASSET_CATEGORY_LABELS) as [AssetCategory, string][];
  protected readonly members = computed<MemberOption[]>(() => this.usersService.users()
    .filter((user) => user.is_active)
    .map((user) => ({ id: user.id, name: user.name })));

  protected readonly filteredAssets = computed(() => {
    const query = this.search().trim().toLocaleLowerCase('fr');
    const category = this.category();
    return this.assetsService.assets().filter((asset) => {
      const matchesCategory = category === 'ALL' || asset.category === category;
      const matchesSearch = !query || [asset.name, asset.owner_name, asset.description]
        .some((value) => value.toLocaleLowerCase('fr').includes(query));
      return matchesCategory && matchesSearch;
    });
  });
  protected readonly highCriticalityCount = computed(() =>
    this.assetsService.assets().filter((asset) => asset.criticality === 3).length,
  );
  protected readonly activeScopeName = computed(() => {
    const scopeId = this.context.activeScopeId();
    return this.context.activeOrganization()?.scopes?.find((scope) => scope.id === scopeId)?.name ?? '—';
  });

  constructor() {
    effect(() => {
      const scopeId = this.context.activeScopeId();
      if (scopeId) {
        this.assetsService.fetchAssets(scopeId);
        this.usersService.fetch();
      }
    });
  }

  protected openCreate(): void {
    this.successMessage.set('');
    this.selectedAsset.set(null);
    this.modalOpen.set(true);
  }

  protected openEdit(asset: Asset): void {
    this.selectedAsset.set(asset);
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
    this.selectedAsset.set(null);
  }

  protected assetSaved(asset: Asset): void {
    this.search.set('');
    this.category.set('ALL');
    this.successMessage.set(`L’actif « ${asset.name} » a bien été enregistré.`);
    this.closeModal();
  }

  protected deleteAsset(asset: Asset): void {
    if (!confirm(`Supprimer l'actif « ${asset.name} » et les risques qui lui sont rattachés ?`)) return;
    this.actionError.set('');
    this.assetsService.deleteAsset(asset.id).subscribe({
      error: (error: Error) => this.actionError.set(error.message),
    });
  }
}
