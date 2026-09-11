import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { jwtInterceptor } from './core/interceptors/jwt.interceptor';
import { mockAuthInterceptor } from './core/interceptors/mock-auth.interceptor';
import { mockGovernanceInterceptor } from './core/interceptors/mock-governance.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([
      jwtInterceptor,
      mockAuthInterceptor,
      mockGovernanceInterceptor,
    ])),
  ],
};
