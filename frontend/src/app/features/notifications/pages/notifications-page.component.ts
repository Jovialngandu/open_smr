import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TopbarComponent } from '../../../shared/components/topbar/topbar.component';
import { NotificationCenterService } from '../services/notification-center.service';

@Component({
  selector: 'app-notifications-page',
  imports: [DatePipe, RouterLink, TopbarComponent],
  templateUrl: './notifications-page.component.html',
  styleUrl: './notifications-page.component.scss',
})
export class NotificationsPageComponent {
  protected readonly center = inject(NotificationCenterService);
  protected readonly filter = signal<'ALL' | 'UNREAD'>('ALL');
  protected readonly visible = computed(() => this.center.items().filter((item) => this.filter() === 'ALL' || !this.center.isRead(item.id)));
  protected readonly typeLabels: Record<string, string> = {
    OVERDUE_TASK_ALERT: 'Tâche en retard',
    RISK_NOTIFICATION: 'Risque',
    INVITATION: 'Invitation',
    WELCOME: 'Bienvenue',
    RECOVERY: 'Récupération de compte',
    MFA_CODE: 'Sécurité du compte',
  };
}
