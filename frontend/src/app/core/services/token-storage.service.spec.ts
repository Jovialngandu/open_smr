import { TestBed } from '@angular/core/testing';

import { TokenStorageService } from './token-storage.service';

describe('TokenStorageService', () => {
  let service: TokenStorageService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TokenStorageService);
    sessionStorage.clear();
  });

  it('conserve les jetons uniquement dans la session', () => {
    service.save({ access: 'access-token', refresh: 'refresh-token' });

    expect(service.accessToken).toBe('access-token');
    expect(service.refreshToken).toBe('refresh-token');

    service.clear();
    expect(service.accessToken).toBeNull();
  });

  it('lit les claims du JWT', () => {
    const payload = btoa(JSON.stringify({ organization_id: 'org-1', scope_id: 'scope-1', role: 'RSSI' }));
    service.save({ access: `header.${payload}.signature`, refresh: 'refresh' });

    expect(service.claims()?.organization_id).toBe('org-1');
    expect(service.claims()?.role).toBe('RSSI');
  });
});
