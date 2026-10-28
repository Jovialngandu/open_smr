import { Component, effect, HostListener, inject, input, output, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { LucideMessageCircle, LucidePlus, LucideSend, LucideSparkles, LucideX } from '@lucide/angular';

import { SentinelConversation, SentinelConversationDetail, SentinelMessage, SentinelRequestError, SentinelService } from '../services/sentinel.service';

@Component({
  selector: 'app-sentinel-drawer',
  imports: [DatePipe, LucideMessageCircle, LucidePlus, LucideSend, LucideSparkles, LucideX],
  templateUrl: './sentinel-drawer.component.html',
  styleUrl: './sentinel-drawer.component.scss',
})
export class SentinelDrawerComponent {
  private readonly service = inject(SentinelService);
  readonly open = input(false);
  readonly closed = output<void>();
  protected readonly conversations = signal<SentinelConversation[]>([]);
  protected readonly detail = signal<SentinelConversationDetail | null>(null);
  protected readonly draft = signal('');
  protected readonly loading = signal(false);
  protected readonly sending = signal(false);
  protected readonly error = signal('');
  protected readonly historyOpen = signal(false);
  private detailVersion = 0;

  constructor() {
    effect(() => {
      if (this.open()) {
        this.loadConversations();
        setTimeout(() => document.getElementById('sentinel-drawer-message')?.focus());
      }
    });
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void { if (this.open()) this.close(); }

  protected close(): void { this.closed.emit(); }

  protected loadConversations(): void {
    this.service.list().subscribe({
      next: (items) => this.conversations.set(items),
      error: (error: Error) => this.error.set(error.message),
    });
  }

  protected startNew(): void {
    ++this.detailVersion;
    this.detail.set(null);
    this.draft.set('');
    this.error.set('');
    this.historyOpen.set(false);
  }

  protected selectConversation(id: string): void {
    const version = ++this.detailVersion;
    this.loading.set(true);
    this.error.set('');
    this.historyOpen.set(false);
    this.service.get(id).subscribe({
      next: (detail) => { if (version === this.detailVersion) { this.detail.set(detail); this.loading.set(false); } },
      error: (error: Error) => { if (version === this.detailVersion) { this.error.set(error.message); this.loading.set(false); } },
    });
  }

  protected send(): void {
    const message = this.draft().trim();
    if (!message || message.length > 2000 || this.sending() || this.loading()) return;
    this.sending.set(true);
    this.error.set('');
    const current = this.detail();
    if (current) { this.sendTo(current.id, message); return; }
    this.service.create().subscribe({
      next: (conversation) => {
        this.detail.set({ ...conversation, messages: [] });
        this.conversations.update((items) => [conversation, ...items]);
        this.sendTo(conversation.id, message);
      },
      error: (error: Error) => { this.sending.set(false); this.error.set(error.message); },
    });
  }

  protected suggest(question: string): void { this.draft.set(question); this.send(); }

  private sendTo(id: string, message: string): void {
    this.service.send(id, message).subscribe({
      next: (response) => {
        this.append(id, [response.user_message, response.assistant_message].filter((item): item is SentinelMessage => !!item));
        this.draft.set('');
        this.sending.set(false);
        this.loadConversations();
      },
      error: (error: SentinelRequestError) => {
        if (error.savedUserMessage) { this.append(id, [error.savedUserMessage]); this.draft.set(''); this.loadConversations(); }
        this.error.set(error.message);
        this.sending.set(false);
      },
    });
  }

  private append(id: string, messages: SentinelMessage[]): void {
    this.detail.update((detail) => detail?.id === id ? {
      ...detail,
      title: detail.title === 'Nouvelle conversation' ? messages.find((item) => item.role === 'user')?.content.slice(0, 80) ?? detail.title : detail.title,
      messages: [...detail.messages, ...messages.filter((message) => !detail.messages.some((existing) => existing.id === message.id))],
    } : detail);
  }
}
