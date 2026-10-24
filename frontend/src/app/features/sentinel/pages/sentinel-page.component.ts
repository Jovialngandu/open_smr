import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LucideMessageCircle, LucidePlus, LucideSend, LucideSparkles } from '@lucide/angular';
import { ActivatedRoute, Router } from '@angular/router';

import { TopbarComponent } from '../../../shared/components/topbar/topbar.component';
import {
  SentinelConversation, SentinelConversationDetail, SentinelMessage,
  SentinelRequestError, SentinelService,
} from '../services/sentinel.service';

@Component({
  selector: 'app-sentinel-page',
  imports: [DatePipe, TopbarComponent, LucideMessageCircle, LucidePlus, LucideSend, LucideSparkles],
  templateUrl: './sentinel-page.component.html',
  styleUrl: './sentinel-page.component.scss',
})
export class SentinelPageComponent {
  private readonly service = inject(SentinelService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private detailVersion = 0;

  protected readonly conversations = signal<SentinelConversation[]>([]);
  protected readonly detail = signal<SentinelConversationDetail | null>(null);
  protected readonly selectedId = signal<string | null>(null);
  protected readonly draft = signal('');
  protected readonly loadingList = signal(false);
  protected readonly loadingDetail = signal(false);
  protected readonly creating = signal(false);
  protected readonly sending = signal(false);
  protected readonly listError = signal('');
  protected readonly detailError = signal('');
  protected readonly sendError = signal('');
  protected readonly sidebarOpen = signal(false);
  protected readonly title = computed(() => this.detail()?.title ?? this.conversations().find((item) => item.id === this.selectedId())?.title ?? 'Nouvelle conversation');
  protected readonly messages = computed(() => this.detail()?.messages ?? []);

  constructor() {
    this.loadConversations();
    this.route.queryParamMap.pipe(takeUntilDestroyed()).subscribe((params) => {
      const id = params.get('conversation');
      if (id === this.selectedId()) return;
      this.selectedId.set(id);
      this.detail.set(null);
      this.detailError.set('');
      this.sendError.set('');
      this.sidebarOpen.set(false);
      if (id) this.loadDetail(id);
      else { ++this.detailVersion; this.loadingDetail.set(false); }
    });
  }

  protected loadConversations(): void {
    this.loadingList.set(true);
    this.listError.set('');
    this.service.list().subscribe({
      next: (items) => { this.conversations.set(items); this.loadingList.set(false); },
      error: (error: Error) => { this.listError.set(error.message); this.loadingList.set(false); },
    });
  }

  protected selectConversation(id: string): void {
    if (id === this.selectedId()) { this.sidebarOpen.set(false); return; }
    void this.router.navigate([], { relativeTo: this.route, queryParams: { conversation: id }, queryParamsHandling: 'merge' });
  }

  protected createConversation(): void {
    if (this.creating() || this.sending()) return;
    this.creating.set(true);
    this.listError.set('');
    this.service.create().subscribe({
      next: (conversation) => {
        this.creating.set(false);
        this.conversations.update((items) => [conversation, ...items]);
        this.selectConversation(conversation.id);
      },
      error: (error: Error) => { this.creating.set(false); this.listError.set(error.message); },
    });
  }

  protected send(): void {
    const id = this.selectedId();
    const message = this.draft().trim();
    if (!id || !this.detail() || !message || message.length > 2000 || this.sending()) return;
    this.sending.set(true);
    this.sendError.set('');
    this.service.send(id, message).subscribe({
      next: (response) => {
        if (this.selectedId() === id) {
          this.appendMessages(id, [response.user_message, response.assistant_message].filter((item): item is SentinelMessage => !!item));
          this.draft.set('');
        }
        this.sending.set(false);
        this.loadConversations();
      },
      error: (error: SentinelRequestError) => {
        if (this.selectedId() === id) {
          if (error.savedUserMessage) {
            this.appendMessages(id, [error.savedUserMessage]);
            this.draft.set('');
            this.loadConversations();
          }
          this.sendError.set(error.message);
        }
        this.sending.set(false);
      },
    });
  }

  private loadDetail(id: string): void {
    const version = ++this.detailVersion;
    this.loadingDetail.set(true);
    this.service.get(id).subscribe({
      next: (detail) => {
        if (version !== this.detailVersion || this.selectedId() !== id) return;
        this.detail.set(detail);
        this.loadingDetail.set(false);
      },
      error: (error: Error) => {
        if (version !== this.detailVersion || this.selectedId() !== id) return;
        this.detailError.set(error.message);
        this.loadingDetail.set(false);
      },
    });
  }

  protected retryDetail(): void {
    const id = this.selectedId();
    if (id) { this.detailError.set(''); this.loadDetail(id); }
  }

  private appendMessages(id: string, incoming: SentinelMessage[]): void {
    this.detail.update((detail) => detail?.id === id ? {
      ...detail,
      title: detail.title === 'Nouvelle conversation' ? incoming.find((item) => item.role === 'user')?.content.slice(0, 80) ?? detail.title : detail.title,
      messages: [...detail.messages, ...incoming.filter((item) => !detail.messages.some((existing) => existing.id === item.id))],
    } : detail);
  }
}
