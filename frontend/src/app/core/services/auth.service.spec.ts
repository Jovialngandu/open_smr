import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { GOOGLE_OIDC_ENDPOINT } from '../config/oidc.config';
import { UserProfile } from '../models/auth.models';
import { AuthService } from './auth.service';
import { TokenStorageService } from './token-storage.service';

describe('AuthService OIDC', () => {
  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
  });

  it('transmet le jeton Google et conserve les JWT applicatifs', async () => {
    const auth = TestBed.inject(AuthService);
    const http = TestBed.inject(HttpTestingController);
    const tokens = TestBed.inject(TokenStorageService);
    const profile: UserProfile = {
      id: '23', username: 'jovial', email: 'jovial@example.com', first_name: 'Jovial',
      last_name: 'Ngandu', is_active: true, roles: [],
    };

    const result = firstValueFrom(auth.loginWithGoogle('google-credential'));
    const request = http.expectOne(GOOGLE_OIDC_ENDPOINT);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ id_token: 'google-credential', provider: 'google' });
    request.flush({ user: profile, access: 'app-access', refresh: 'app-refresh' });

    expect(await result).toEqual(profile);
    expect(tokens.accessToken).toBe('app-access');
    expect(tokens.refreshToken).toBe('app-refresh');
    expect(auth.status()).toBe('authenticated');
    http.verify();
  });

  it('affiche un refus Google clair sans enregistrer de session', async () => {
    const auth = TestBed.inject(AuthService);
    const http = TestBed.inject(HttpTestingController);
    const result = firstValueFrom(auth.loginWithGoogle('invalid'));
    http.expectOne(GOOGLE_OIDC_ENDPOINT).flush({ detail: 'Authentification OIDC refusée.' }, { status: 401, statusText: 'Unauthorized' });

    await expect(result).rejects.toThrow('Assurez-vous d’avoir une invitation valide ou un compte actif.');
    expect(TestBed.inject(TokenStorageService).accessToken).toBeNull();
    expect(auth.status()).toBe('anonymous');
    http.verify();
  });
});
