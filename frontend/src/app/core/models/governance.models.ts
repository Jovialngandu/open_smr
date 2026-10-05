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

export type TreatmentStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED';
export type ImplementationStatus = 'NOT_IMPLEMENTED' | 'IN_PROGRESS' | 'IMPLEMENTED';
export type ControlTheme = 'ORGANIZATIONAL' | 'PEOPLE' | 'PHYSICAL' | 'TECHNOLOGICAL';

export interface IsoControl {
  id: string;
  code: string;
  title: string;
  theme: ControlTheme;
}

export interface Evidence {
  id: string;
  task_id: string;
  file_name: string;
  file_type: string;
  description: string;
  uploaded_by_name: string;
  uploaded_at: string;
  download_url?: string;
}

export interface TreatmentTask {
  id: string;
  scope_id: string;
  risk_id: string;
  risk_code: string;
  iso_control_id: string;
  control_code: string;
  assignee_id: string;
  assignee_name: string;
  title: string;
  description: string;
  due_date: string;
  status: TreatmentStatus;
  completed_at: string | null;
  evidences: Evidence[];
}

export type TreatmentPayload = Pick<TreatmentTask, 'risk_id' | 'iso_control_id' | 'assignee_id' | 'title' | 'description' | 'due_date'>;

export interface SoaEntry {
  id: string;
  scope_id: string;
  iso_control: IsoControl;
  is_applicable: boolean;
  justification: string;
  implementation_status: ImplementationStatus;
  updated_at: string;
  updated_by_name: string;
}

export interface SoaVersion {
  id: string;
  scope_id: string;
  version_number: string;
  title: string;
  status: 'DRAFT' | 'APPROVED';
  created_at: string;
  approved_by_name: string | null;
}

export interface DashboardSummary {
  asset_count: number;
  critical_risk_count: number;
  soa_compliance_percent: number;
  overdue_tasks: TreatmentTask[];
}

export interface HeatmapCell {
  likelihood: 1 | 2 | 3 | 4 | 5;
  impact: 1 | 2 | 3 | 4 | 5;
  risk_count: number;
  risk_ids: string[];
}

export interface HeatmapApiCell {
  likelihood: number;
  impact: number;
  score: number;
  count: number;
}

export interface HeatmapApiResponse {
  scope_id: string;
  total_risks: number;
  matrix: HeatmapApiCell[];
}

export interface ManagedUser {
  id: string;
  role_assignment_id?: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'RSSI' | 'RISK_OWNER' | 'AUDITOR';
  is_active: boolean;
  scope_ids: string[];
}

export interface ScopeDashboardMetrics {
  risks_by_level: { high: number; medium: number; low: number };
  soa_completion: { total_applicable: number; implemented: number; percentage: number };
  overdue_tasks_count: number;
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

export const TREATMENT_STATUS_LABELS: Record<TreatmentStatus, string> = {
  TODO: 'À faire',
  IN_PROGRESS: 'En cours',
  COMPLETED: 'Terminée',
};

export const IMPLEMENTATION_STATUS_LABELS: Record<ImplementationStatus, string> = {
  NOT_IMPLEMENTED: 'Non mise en œuvre',
  IN_PROGRESS: 'En cours',
  IMPLEMENTED: 'Mise en œuvre',
};

export const CONTROL_THEME_LABELS: Record<ControlTheme, string> = {
  ORGANIZATIONAL: 'Organisationnel',
  PEOPLE: 'Personnel',
  PHYSICAL: 'Physique',
  TECHNOLOGICAL: 'Technologique',
};
