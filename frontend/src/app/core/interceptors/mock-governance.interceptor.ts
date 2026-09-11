import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG, DOMAIN_ENDPOINTS } from '../config/api.config';
import { Asset, AssetPayload, Risk, RiskPayload } from '../models/governance.models';

const SCOPE_DIGITAL = '8f4b8400-e29b-41d4-a716-446655440101';
const SCOPE_DATACENTER = '8f4b8400-e29b-41d4-a716-446655440102';
const NOW = '2026-09-10T08:30:00Z';

const OWNER_NAMES: Record<string, string> = {
  'member-001': 'Camille Durand',
  'member-002': 'Nadia Bernard',
  'member-003': 'Thomas Leroy',
};

let assets: Asset[] = [
  asset('asset-001', SCOPE_DIGITAL, 'Plateforme de paiement', 'SOFTWARE', 'member-001', 3, 3, 3),
  asset('asset-002', SCOPE_DIGITAL, 'Base clients', 'DATA', 'member-002', 3, 3, 2),
  asset('asset-003', SCOPE_DIGITAL, 'API partenaires', 'SERVICE', 'member-003', 2, 3, 2),
  asset('asset-004', SCOPE_DIGITAL, 'Postes des analystes', 'HARDWARE', 'member-003', 2, 2, 2),
  asset('asset-005', SCOPE_DATACENTER, 'Cluster de virtualisation', 'HARDWARE', 'member-001', 2, 3, 3),
];

let risks: Risk[] = [
  risk('risk-001', 'asset-001', 'RSK-PAY-001', 'Indisponibilité du service lors d’une attaque par déni de service.', 4, 5, 'OPEN'),
  risk('risk-002', 'asset-002', 'RSK-DAT-002', 'Accès non autorisé aux données personnelles des clients.', 3, 5, 'IN_MITIGATION'),
  risk('risk-003', 'asset-003', 'RSK-API-003', 'Exploitation d’une vulnérabilité exposée par une API partenaire.', 3, 4, 'OPEN'),
  risk('risk-004', 'asset-004', 'RSK-END-004', 'Compromission d’un poste par hameçonnage.', 4, 3, 'ACCEPTED'),
  risk('risk-005', 'asset-005', 'RSK-INF-005', 'Panne matérielle simultanée de plusieurs hôtes.', 2, 5, 'CLOSED'),
];

export const mockGovernanceInterceptor: HttpInterceptorFn = (request, next) => {
  if (!API_CONFIG.useMocks) return next(request);

  if (request.url === DOMAIN_ENDPOINTS.assets && request.method === 'GET') {
    const scopeId = request.params.get('scope_id');
    return mockOk(assets.filter((item) => !scopeId || item.scope_id === scopeId));
  }

  if (request.url === DOMAIN_ENDPOINTS.assets && request.method === 'POST') {
    const created = buildAsset(request.body as AssetPayload);
    assets = [created, ...assets];
    return mockOk(created, 201);
  }

  const assetId = resourceId(request.url, DOMAIN_ENDPOINTS.assets);
  if (assetId && request.method === 'PUT') {
    const index = assets.findIndex((item) => item.id === assetId);
    if (index < 0) return mockError(404, 'Actif introuvable.');
    const updated = buildAsset(request.body as AssetPayload, assets[index]);
    assets = assets.map((item) => item.id === assetId ? updated : item);
    return mockOk(updated);
  }
  if (assetId && request.method === 'DELETE') {
    if (!assets.some((item) => item.id === assetId)) return mockError(404, 'Actif introuvable.');
    assets = assets.filter((item) => item.id !== assetId);
    risks = risks.filter((item) => item.asset_id !== assetId);
    return mockOk(null, 204);
  }

  if (request.url === DOMAIN_ENDPOINTS.risks && request.method === 'GET') {
    const scopeId = request.params.get('scope_id');
    return mockOk(risks.filter((item) => !scopeId || item.scope_id === scopeId));
  }

  if (request.url === DOMAIN_ENDPOINTS.risks && request.method === 'POST') {
    const payload = request.body as RiskPayload;
    if (!assets.some((item) => item.id === payload.asset_id)) {
      return mockError(400, 'Sélectionnez un actif valide.');
    }
    const created = buildRisk(payload);
    risks = [created, ...risks];
    return mockOk(created, 201);
  }

  const riskId = resourceId(request.url, DOMAIN_ENDPOINTS.risks);
  if (riskId && request.method === 'PUT') {
    const index = risks.findIndex((item) => item.id === riskId);
    if (index < 0) return mockError(404, 'Risque introuvable.');
    const updated = buildRisk(request.body as RiskPayload, risks[index]);
    risks = risks.map((item) => item.id === riskId ? updated : item);
    return mockOk(updated);
  }
  if (riskId && request.method === 'DELETE') {
    if (!risks.some((item) => item.id === riskId)) return mockError(404, 'Risque introuvable.');
    risks = risks.filter((item) => item.id !== riskId);
    return mockOk(null, 204);
  }

  return next(request);
};

function asset(
  id: string,
  scopeId: string,
  name: string,
  category: Asset['category'],
  ownerId: string,
  confidentiality: Asset['confidentiality'],
  integrity: Asset['integrity'],
  availability: Asset['availability'],
): Asset {
  return {
    id, scope_id: scopeId, name, category, owner_id: ownerId,
    owner_name: OWNER_NAMES[ownerId], description: '', confidentiality, integrity, availability,
    criticality: Math.max(confidentiality, integrity, availability), created_at: NOW, updated_at: NOW,
  };
}

function risk(
  id: string,
  assetId: string,
  code: string,
  threat: string,
  likelihood: Risk['likelihood'],
  impact: Risk['impact'],
  status: Risk['status'],
): Risk {
  const linkedAsset = assets.find((item) => item.id === assetId)!;
  return {
    id, asset_id: assetId, asset_name: linkedAsset.name, scope_id: linkedAsset.scope_id,
    code, threat_description: threat, likelihood, impact, score: likelihood * impact,
    status, created_at: NOW, updated_at: NOW,
  };
}

function buildAsset(payload: AssetPayload, current?: Asset): Asset {
  return {
    ...payload,
    id: current?.id ?? crypto.randomUUID(),
    owner_name: payload.owner_id ? OWNER_NAMES[payload.owner_id] ?? 'Utilisateur inconnu' : 'Non attribué',
    criticality: Math.max(payload.confidentiality, payload.integrity, payload.availability),
    created_at: current?.created_at ?? new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

function buildRisk(payload: RiskPayload, current?: Risk): Risk {
  const linkedAsset = assets.find((item) => item.id === payload.asset_id)!;
  return {
    ...payload,
    id: current?.id ?? crypto.randomUUID(),
    asset_name: linkedAsset.name,
    scope_id: linkedAsset.scope_id,
    score: payload.likelihood * payload.impact,
    created_at: current?.created_at ?? new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

function resourceId(url: string, collectionUrl: string): string | null {
  if (!url.startsWith(collectionUrl)) return null;
  const remainder = url.slice(collectionUrl.length);
  return remainder ? remainder.replace(/\/$/, '') : null;
}

function mockOk<T>(body: T, status = 200) {
  return of(new HttpResponse({ body, status })).pipe(delay(API_CONFIG.mockDelayMs));
}

function mockError(status: number, detail: string) {
  return throwError(() => new HttpErrorResponse({ status, error: { detail } }));
}
