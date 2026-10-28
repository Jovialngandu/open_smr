import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { EMAIL_LOGS_ENDPOINT, EmailLog, SettingsService } from './settings.service';

describe('SettingsService notifications', () => {
  it('ignore une réponse tardive après la fermeture de session', () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    const service = TestBed.inject(SettingsService);
    const http = TestBed.inject(HttpTestingController);
    const log: EmailLog = {
      id: 'mail-1', email_type: 'WELCOME', recipient: 'user@example.com',
      subject: 'Bienvenue', sent_at: '2026-10-22T08:00:00Z', status: true, error_message: null,
    };

    service.loadEmailLogs();
    const request = http.expectOne((item) => item.url === EMAIL_LOGS_ENDPOINT);
    expect(request.request.params.has('organization_id')).toBe(false);
    expect(service.emailLogsLoading()).toBe(true);

    service.clearEmailLogs();
    request.flush([log]);

    expect(service.emailLogs()).toEqual([]);
    expect(service.emailLogsLoading()).toBe(false);
    expect(service.emailLogsError()).toBe('');
    http.verify();
  });

  it('récupère les e-mails personnels sans filtrer par organisation', () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    const service = TestBed.inject(SettingsService);
    const http = TestBed.inject(HttpTestingController);
    service.loadEmailLogs();
    const request = http.expectOne(EMAIL_LOGS_ENDPOINT);
    expect(request.request.params.keys()).toEqual([]);
    request.flush([
      { id: 'mail-a', email_type: 'WELCOME', recipient: 'user@example.com', subject: 'Organisation A', sent_at: '2026-10-22T08:00:00Z', status: true, error_message: null },
      { id: 'mail-b', email_type: 'WELCOME', recipient: 'user@example.com', subject: 'Organisation B', sent_at: '2026-10-23T08:00:00Z', status: true, error_message: null },
    ] satisfies EmailLog[]);
    expect(service.emailLogs().map((log) => log.id)).toEqual(['mail-a', 'mail-b']);
    http.verify();
  });
});
