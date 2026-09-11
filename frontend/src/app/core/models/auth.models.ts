export type UserRole = 'ADMIN' | 'RSSI' | 'RISK_OWNER' | 'AUDITOR';

export interface ScopeSummary {
  id: string;
  name: string;
}

export interface OrganizationRole {
  organization_id: string;
  organization_name: string;
  role: UserRole;
  scopes?: ScopeSummary[];
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  roles: OrganizationRole[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse extends AuthTokens {
  user?: UserProfile;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  email: string;
  first_name: string;
  last_name: string;
  organization_name?: string;
}

export interface JwtClaims {
  exp?: number;
  user_id?: string;
  username?: string;
  email?: string;
  organization_id: string | null;
  scope_id: string | null;
  role: UserRole | null;
}

export interface SwitchContextRequest {
  organization_id: string;
  scope_id: string | null;
}

export interface SwitchContextResponse extends AuthTokens {
  active_organization_id: string;
  active_scope_id: string | null;
}
