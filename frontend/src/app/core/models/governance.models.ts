export type AssetCategory = 'HARDWARE' | 'SOFTWARE' | 'DATA' | 'PEOPLE' | 'SERVICE';
export type RiskStatus = 'OPEN' | 'IN_MITIGATION' | 'ACCEPTED' | 'CLOSED';

export interface Asset {
  id: string;
  scope_id: string;
  owner_id: string | null;
  owner_name: string;
  name: string;
  category: AssetCategory;
  description: string;
  confidentiality: 1 | 2 | 3;
  integrity: 1 | 2 | 3;
  availability: 1 | 2 | 3;
  criticality: number;
  created_at: string;
  updated_at: string;
}

export type AssetPayload = Omit<
  Asset,
  'id' | 'owner_name' | 'criticality' | 'created_at' | 'updated_at'
>;

export interface Risk {
  id: string;
  asset_id: string;
  asset_name: string;
  scope_id: string;
  code: string;
  threat_description: string;
  likelihood: 1 | 2 | 3 | 4 | 5;
  impact: 1 | 2 | 3 | 4 | 5;
  score: number;
  status: RiskStatus;
  created_at: string;
  updated_at: string;
}

export type RiskPayload = Omit<
  Risk,
  'id' | 'asset_name' | 'scope_id' | 'score' | 'created_at' | 'updated_at'
>;

export interface MemberOption {
  id: string;
  name: string;
}

export const ASSET_CATEGORY_LABELS: Record<AssetCategory, string> = {
  HARDWARE: 'Matériel',
  SOFTWARE: 'Logiciel',
  DATA: 'Données',
  PEOPLE: 'Ressources humaines',
  SERVICE: 'Service',
};

export const RISK_STATUS_LABELS: Record<RiskStatus, string> = {
  OPEN: 'Ouvert',
  IN_MITIGATION: 'En traitement',
  ACCEPTED: 'Accepté',
  CLOSED: 'Clôturé',
};
