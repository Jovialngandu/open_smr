import { computed, effect, inject, Injectable, signal } from '@angular/core';

import { AuthService } from '../../../core/services/auth.service';
import { SettingsService } from '../../settings/services/settings.service';

@Injectable({ providedIn: 'root' })
export class NotificationCenterService {
  private readonly auth = inject(AuthService);
  private readonly settings = inject(SettingsService);
  private readonly readIdsState = signal<Set<string>>(new Set());

  readonly items = this.settings.emailLogs;
  readonly loading = this.settings.emailLogsLoading;
  readonly error = this.settings.emailLogsError;
  readonly unreadCount = computed(() => this.items().filter((item) => !this.readIdsState().has(item.id)).length);

  constructor() {
    effect(() => {
      const userId = this.auth.user()?.id;
      this.readIdsState.set(this.restoreReadIds(userId));
      if (userId) this.settings.loadEmailLogs();
      else this.settings.clearEmailLogs();
    });
  }

  isRead(id: string): boolean { return this.readIdsState().has(id); }

  markRead(id: string): void {
    if (!this.items().some((item) => item.id === id)) return;
    this.saveReadIds(new Set([...this.readIdsState(), id]));
  }

  markAllRead(): void {
    this.saveReadIds(new Set([...this.readIdsState(), ...this.items().map((item) => item.id)]));
  }

  refresh(): void {
    if (this.auth.user()) this.settings.loadEmailLogs();
  }

  private saveReadIds(ids: Set<string>): void {
    this.readIdsState.set(ids);
    const key = this.storageKey(this.auth.user()?.id);
    if (key) localStorage.setItem(key, JSON.stringify([...ids]));
  }

  private restoreReadIds(userId: string | undefined): Set<string> {
    const key = this.storageKey(userId);
    if (!key) return new Set();
    try {
      const stored = JSON.parse(localStorage.getItem(key) ?? '[]') as unknown;
      return new Set(Array.isArray(stored) ? stored.filter((id): id is string => typeof id === 'string') : []);
    } catch { return new Set(); }
  }

  private storageKey(userId: string | undefined): string | null {
    return userId ? `opensmr.read_email_logs.${userId}` : null;
  }
}
