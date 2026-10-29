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

  it('conserve la lecture par compte lors du changement d’organisation', () => {
    const user = signal<UserProfile | null>({ id: 'user-1' } as UserProfile);
    const organization = signal<string | null>('org-a');
    const items = signal([log('message-a')]);
    const loadEmailLogs = vi.fn();
    const clearEmailLogs = vi.fn(() => items.set([]));
    TestBed.configureTestingModule({ providers: [
      { provide: AuthService, useValue: { user } },
      { provide: ContextService, useValue: { activeOrganizationId: organization } },
      { provide: SettingsService, useValue: { emailLogs: items, emailLogsLoading: signal(false), emailLogsError: signal(''), loadEmailLogs, clearEmailLogs } },
    ] });
    const center = TestBed.inject(NotificationCenterService);
    TestBed.flushEffects();
    expect(loadEmailLogs).toHaveBeenCalledWith();
    expect(center.unreadCount()).toBe(1);

    center.markRead('message-a');
    expect(center.unreadCount()).toBe(0);
    expect(localStorage.getItem('opensmr.read_email_logs.user-1')).toContain('message-a');

    organization.set('org-b');
    items.set([log('message-a'), log('message-b')]);
    TestBed.flushEffects();
    expect(loadEmailLogs).toHaveBeenCalledTimes(1);
    expect(center.unreadCount()).toBe(1);

    organization.set('org-a');
    items.set([log('message-a')]);
    TestBed.flushEffects();
    expect(center.isRead('message-a')).toBe(true);

    user.set(null);
    TestBed.flushEffects();
    expect(clearEmailLogs).toHaveBeenCalledOnce();
    expect(center.items()).toEqual([]);
    expect(center.unreadCount()).toBe(0);
  });
});
