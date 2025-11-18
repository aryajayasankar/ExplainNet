import { Component, OnInit, OnDestroy, PLATFORM_ID, Inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ThemeService } from '../../services/theme.service';

interface LogMessage {
  id: number;
  text: string;
  type: 'info' | 'success' | 'error' | 'progress' | 'emoji';
  timestamp: Date;
  visible: boolean;
}

type AppState = 'chat' | 'processing' | 'complete' | 'error';

@Component({
  selector: 'app-terminal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './terminal.component.html',
  styleUrls: ['./terminal.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TerminalComponent implements OnInit, OnDestroy {
  isDarkMode$: any;
  
  // State management
  currentState: AppState = 'chat';
  topicInput = '';
  logs: LogMessage[] = [];
  createdTopicId: number | null = null;
  
  // Animation control
  private logIdCounter = 0;
  private eventSource: EventSource | null = null;
  isProcessing = false;

  constructor(
    private router: Router,
    private apiService: ApiService,
    private themeService: ThemeService,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isDarkMode$ = this.themeService.isDarkMode$;
  }

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      setTimeout(() => {
        document.querySelector('.chat-container')?.classList.add('visible');
      }, 100);
    }
  }

  ngOnDestroy(): void {
    this.closeEventSource();
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  onTopicKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && this.topicInput.trim() && !this.isProcessing) {
      this.startAnalysis();
    }
  }

  startAnalysis(): void {
    if (!this.topicInput.trim() || this.isProcessing) return;

    this.isProcessing = true;
    this.currentState = 'processing';
    this.logs = [];
    this.cdr.markForCheck();

    // Add initial greeting
    this.addLog(`🎯 Starting analysis for: "${this.topicInput}"`, 'info');
    this.addLog('🔄 Initializing ExplainNet AI...', 'info');

    // Start streaming
    this.connectToStream();
  }

  private connectToStream(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const topic = encodeURIComponent(this.topicInput);
    const url = `http://localhost:8000/api/topics/create-streaming?topic=${topic}`;

    this.eventSource = new EventSource(url);

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.status === 'complete') {
          this.createdTopicId = data.topic_id;
          this.handleCompletion();
          this.closeEventSource();
        } else if (data.status === 'error') {
          this.addLog(`❌ Error: ${data.message}`, 'error');
          this.currentState = 'error';
          this.isProcessing = false;
          this.closeEventSource();
          this.cdr.markForCheck();
        } else if (data.message) {
          this.addLog(data.message, data.type || 'info');
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      if (this.currentState !== 'complete') {
        this.addLog('❌ Connection error. Please try again.', 'error');
        this.currentState = 'error';
        this.isProcessing = false;
      }
      this.closeEventSource();
      this.cdr.markForCheck();
    };
  }

  private addLog(text: string, type: LogMessage['type'] = 'info'): void {
    const log: LogMessage = {
      id: this.logIdCounter++,
      text,
      type,
      timestamp: new Date(),
      visible: false
    };

    this.logs.push(log);
    this.cdr.markForCheck();

    // Animate in with slight delay
    setTimeout(() => {
      log.visible = true;
      this.cdr.markForCheck();
      this.scrollToBottom();
    }, 100);
  }

  private handleCompletion(): void {
    setTimeout(() => {
      this.addLog('', 'info');
      this.addLog('✅ Analysis Complete!', 'success');
      this.addLog(`📊 Your insights are ready to explore!`, 'success');
      
      setTimeout(() => {
        this.currentState = 'complete';
        this.isProcessing = false;
        this.cdr.markForCheck();
      }, 500);
    }, 300);
  }

  private scrollToBottom(): void {
    if (isPlatformBrowser(this.platformId)) {
      setTimeout(() => {
        const terminal = document.querySelector('.terminal-logs');
        if (terminal) {
          terminal.scrollTop = terminal.scrollHeight;
        }
      }, 50);
    }
  }

  private closeEventSource(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  cancelAnalysis(): void {
    if (this.eventSource) {
      this.closeEventSource();
      
      // Call backend to cancel
      if (this.createdTopicId) {
        this.apiService.deleteTopic(this.createdTopicId).subscribe({
          next: () => console.log('Analysis cancelled'),
          error: (err) => console.error('Error cancelling:', err)
        });
      }
      
      this.addLog('⚠️ Analysis cancelled by user', 'error');
      setTimeout(() => {
        this.resetToChat();
      }, 1000);
    }
  }

  resetToChat(): void {
    this.currentState = 'chat';
    this.topicInput = '';
    this.logs = [];
    this.createdTopicId = null;
    this.isProcessing = false;
    this.closeEventSource();
    this.cdr.markForCheck();
  }

  viewAnalytics(): void {
    if (this.createdTopicId) {
      this.router.navigate(['/analysis', this.createdTopicId]);
    }
  }

  goToLocker(): void {
    this.router.navigate(['/locker']);
  }

  getLogIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'info': '•',
      'success': '✓',
      'error': '✗',
      'progress': '→',
      'emoji': ''
    };
    return icons[type] || '•';
  }
}
