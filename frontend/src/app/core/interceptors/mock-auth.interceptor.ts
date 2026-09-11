import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG, AUTH_ENDPOINTS } from '../config/api.config';
import {
  AuthResponse,
  JwtClaims,
  RegisterRequest,
  SwitchContextRequest,
  UserProfile,
  UserRole,
} from '../models/auth.models';

const ORGANIZATIONS = [
  {
    organization_id: '8f4b8400-e29b-41d4-a716-446655440001',
    organization_name: 'Asteria Finance',
    role: 'RSSI' as UserRole,
    scopes: [
      { id: '8f4b8400-e29b-41d4-a716-446655440101', name: 'Services numériques' },
      { id: '8f4b8400-e29b-41d4-a716-446655440102', name: 'Datacenter Europe' },
    ],
  },
  {
    organization_id: '8f4b8400-e29b-41d4-a716-446655440002',
    organization_name: 'Novacare Groupe',
    role: 'AUDITOR' as UserRole,
    scopes: [{ id: '8f4b8400-e29b-41d4-a716-446655440201', name: 'SI clinique' }],
  },
];

const DEMO_PROFILE: UserProfile = {
  id: '8f4b8400-e29b-41d4-a716-446655440000',
  username: 'demo.rssi',
  email: 'demo@opensmr.fr',
  first_name: 'Camille',
  last_name: 'Durand',
  is_active: true,
  roles: ORGANIZATIONS,
};

let currentProfile = DEMO_PROFILE;
let activeOrganizationId = ORGANIZATIONS[0].organization_id;
let activeScopeId = ORGANIZATIONS[0].scopes[0].id;

export const mockAuthInterceptor: HttpInterceptorFn = (request, next) => {
  if (!API_CONFIG.useMocks || !request.url.startsWith(`${API_CONFIG.baseUrl}/auth/`)) {
    return next(request);
  }

  if (request.url === AUTH_ENDPOINTS.login && request.method === 'POST') {
    const body = request.body as { username?: string; password?: string };
    const validIdentity = ['demo@opensmr.fr', 'demo.rssi'].includes(body.username ?? '');
    if (!validIdentity || body.password !== 'Demo1234!') {
      return mockError(401, 'Identifiant ou mot de passe incorrect.');
    }
    return mockOk(tokensFor(currentProfile));
  }

  if (request.url === AUTH_ENDPOINTS.register && request.method === 'POST') {
    const body = request.body as RegisterRequest;
    if (body.email === DEMO_PROFILE.email || body.username === DEMO_PROFILE.username) {
      return mockError(400, 'Un compte utilise déjà cet email ou cet identifiant.');
    }
    const organizationId = '8f4b8400-e29b-41d4-a716-446655440099';
    currentProfile = {
      id: '8f4b8400-e29b-41d4-a716-446655440098',
      username: body.username,
      email: body.email,
      first_name: body.first_name,
      last_name: body.last_name,
      is_active: true,
      roles: body.organization_name
        ? [{
            organization_id: organizationId,
            organization_name: body.organization_name,
            role: 'ADMIN',
            scopes: [],
          }]
        : [],
    };
    activeOrganizationId = body.organization_name ? organizationId : '';
    activeScopeId = '';
    return mockOk({ ...tokensFor(currentProfile), user: currentProfile }, 201);
  }

  if (request.url === AUTH_ENDPOINTS.profile && request.method === 'GET') {
    return mockOk(currentProfile);
  }

  if (request.url === AUTH_ENDPOINTS.switchContext && request.method === 'POST') {
    const body = request.body as SwitchContextRequest;
    const organization = currentProfile.roles.find(
      (item) => item.organization_id === body.organization_id,
    );
    const validScope = !body.scope_id || organization?.scopes?.some((scope) => scope.id === body.scope_id);
    if (!organization || !validScope) return mockError(403, "Vous n'avez pas accès à ce contexte.");

    activeOrganizationId = body.organization_id;
    activeScopeId = body.scope_id ?? '';
    return mockOk({
      ...tokensFor(currentProfile),
      active_organization_id: activeOrganizationId,
      active_scope_id: activeScopeId || null,
    });
  }

  if (request.url === AUTH_ENDPOINTS.refresh && request.method === 'POST') {
    return mockOk({ access: tokensFor(currentProfile).access });
  }

  return next(request);
};

function tokensFor(profile: UserProfile): AuthResponse {
  const organization = profile.roles.find((item) => item.organization_id === activeOrganizationId);
  const claims: JwtClaims = {
    exp: Math.floor(Date.now() / 1000) + 3600,
    user_id: profile.id,
    username: profile.username,
    email: profile.email,
    organization_id: organization?.organization_id ?? null,
    scope_id: activeScopeId || null,
    role: organization?.role ?? null,
  };
  return { access: encodeToken(claims), refresh: encodeToken({ ...claims, exp: claims.exp! + 86400 }) };
}

function encodeToken(payload: object): string {
  const encode = (value: object) =>
    btoa(unescape(encodeURIComponent(JSON.stringify(value))))
      .replace(/=/g, '')
      .replace(/\+/g, '-')
      .replace(/\//g, '_');
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode(payload)}.mock-signature`;
}

function mockOk<T>(body: T, status = 200) {
  return of(new HttpResponse({ status, body })).pipe(delay(API_CONFIG.mockDelayMs));
}

function mockError(status: number, detail: string) {
  return throwError(() => new HttpErrorResponse({ status, error: { detail } })).pipe(
    delay(API_CONFIG.mockDelayMs),
  );
}
