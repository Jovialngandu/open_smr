import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';

import { UserProfile } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { ContextService } from '../../../core/services/context.service';
import { EmailLog, SettingsService } from '../../settings/services/settings.service';
import { NotificationCenterService } from './notification-center.service';

const log = (id: string): EmailLog => ({ id, email_type: 'OVERDUE_TASK_ALERT', recipient: 'demo@example.com', subject: 'Rappel', sent_at: '2026-10-15T08:00:00Z', status: true, error_message: null });

describe('NotificationCenterService', () => {
  beforeEach(() => localStorage.clear());

  it('conserve la lecture localement et l’isole par organisation', () => {
    const user = signal({ id: 'user-1' } as UserProfile);
    const organization = signal<string | null>('org-a');
    const items = signal([log('message-a')]);
    const loadEmailLogs = vi.fn();
    TestBed.configureTestingModule({ providers: [
      { provide: AuthService, useValue: { user } },
      { provide: ContextService, useValue: { activeOrganizationId: organization } },
      { provide: SettingsService, useValue: { emailLogs: items, emailLogsLoading: signal(false), emailLogsError: signal(''), loadEmailLogs } },
    ] });
    const center = TestBed.inject(NotificationCenterService);
    TestBed.flushEffects();
    expect(loadEmailLogs).toHaveBeenCalledWith('org-a');
    expect(center.unreadCount()).toBe(1);

    center.markRead('message-a');
    expect(center.unreadCount()).toBe(0);
    expect(localStorage.getItem('opensmr.read_email_logs.user-1.org-a')).toContain('message-a');

    organization.set('org-b');
    items.set([log('message-b')]);
    TestBed.flushEffects();
    expect(center.unreadCount()).toBe(1);

    organization.set('org-a');
    items.set([log('message-a')]);
    TestBed.flushEffects();
    expect(center.isRead('message-a')).toBe(true);
  });
});
