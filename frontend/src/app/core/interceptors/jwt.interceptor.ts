import { HttpBackend, HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, tap, throwError } from 'rxjs';

import { AUTH_ENDPOINTS } from '../config/api.config';
import { AuthTokens } from '../models/auth.models';
import { TokenStorageService } from '../services/token-storage.service';

const PUBLIC_ENDPOINTS = [AUTH_ENDPOINTS.login, AUTH_ENDPOINTS.register, AUTH_ENDPOINTS.refresh];

export const jwtInterceptor: HttpInterceptorFn = (request, next) => {
  const storage = inject(TokenStorageService);
  const router = inject(Router);
  const rawHttp = new HttpClient(inject(HttpBackend));
  const accessToken = storage.accessToken;
  const isPublic = PUBLIC_ENDPOINTS.some((endpoint) => request.url.startsWith(endpoint));
  const authorizedRequest = accessToken && !isPublic
    ? request.clone({ setHeaders: { Authorization: `Bearer ${accessToken}` } })
    : request;

  return next(authorizedRequest).pipe(
    catchError((error: unknown) => {
      const refreshToken = storage.refreshToken;
      if (!(error instanceof HttpErrorResponse) || error.status !== 401 || isPublic || !refreshToken) {
        return throwError(() => error);
      }

      return rawHttp.post<Pick<AuthTokens, 'access'>>(AUTH_ENDPOINTS.refresh, { refresh: refreshToken }).pipe(
        tap(({ access }) => storage.save({ access, refresh: refreshToken })),
        switchMap(({ access }) => next(request.clone({ setHeaders: { Authorization: `Bearer ${access}` } }))),
        catchError((refreshError) => {
          storage.clear();
          void router.navigate(['/login']);
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
