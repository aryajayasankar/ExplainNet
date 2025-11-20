import { Component, OnInit, OnDestroy, PLATFORM_ID, Inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ThemeService } from '../../services/theme.service';

interface LogMessage {
  id: number;
  text: string;
  type: 'info' | 'success' | 'error' | 'progress' | 'emoji' | 'transcription';
  timestamp: Date;
  visible: boolean;
  isTranscriptionLog?: boolean;
}

interface TranscriptionState {
  isActive: boolean;
  startTime: number | null;
  elapsedTime: string;
  logs: LogMessage[];
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
  
  // Timer tracking
  analysisStartTime: number | null = null;
  analysisEndTime: number | null = null;
  elapsedTime = '0:00';
  private timerInterval: any = null;
  
  // Transcription state
  transcriptionState: TranscriptionState = {
    isActive: false,
    startTime: null,
    elapsedTime: '0:00',
    logs: []
  };
  private transcriptionTimerInterval: any = null;

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
      // Check if sessionStorage has any state
      const savedState = sessionStorage.getItem('terminalState');
      
      if (savedState) {
        // Restore state from sessionStorage (page refresh scenario)
        this.restoreStateFromStorage();
      } else {
        // No saved state - ensure clean slate for new analysis
        console.log('🆕 No saved state found - starting fresh');
        this.currentState = 'chat';
        this.topicInput = '';
        this.logs = [];
        this.createdTopicId = null;
        this.isProcessing = false;
        this.transcriptionState = {
          isActive: false,
          startTime: null,
          elapsedTime: '0:00',
          logs: []
        };
        this.cdr.detectChanges();
      }
      
      setTimeout(() => {
        document.querySelector('.chat-container')?.classList.add('visible');
      }, 100);
    }
  }

  ngOnDestroy(): void {
    this.closeEventSource();
    this.stopTimer();
    if (this.transcriptionTimerInterval) {
      clearInterval(this.transcriptionTimerInterval);
      this.transcriptionTimerInterval = null;
    }
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

    // Start timer
    this.startTimer();

    // Add initial greeting
    this.addLog(`🎯 Starting analysis for: "${this.topicInput}"`, 'info');
    this.addLog('🔄 Initializing ExplainNet AI...', 'info');

    // Save initial state to sessionStorage
    this.saveStateToStorage();

    // Start streaming
    this.connectToStream();
  }

  private connectToStream(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const topic = encodeURIComponent(this.topicInput);
    const url = `${this.apiService['baseUrl']}/topics/create-streaming?topic=${topic}`;

    this.eventSource = new EventSource(url);

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // DEBUG: Log all messages to console
        console.log('SSE Message received:', data);
        
        // Capture topic_id as soon as it's available
        if (data.topic_id && !this.createdTopicId) {
          this.createdTopicId = data.topic_id;
          this.saveStateToStorage();
        }
        
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
          // Check for transcription special markers
          if (data.message.includes('[TRANSCRIPTION_START]')) {
            console.log('🎯 [TRANSCRIPTION_START] detected! Calling startTranscriptionSubProcess()');
            this.startTranscriptionSubProcess();
            // Don't add to main logs, only to transcription terminal
          } else if (data.message.includes('[TRANSCRIPTION_END]')) {
            console.log('🎯 [TRANSCRIPTION_END] detected! Calling endTranscriptionSubProcess()');
            this.endTranscriptionSubProcess();
            // Don't add to main logs, only to transcription terminal
          } else if (data.message.includes('[TRANSCRIPTION_LOG]')) {
            // Extract the actual message after the marker
            const cleanMessage = data.message.replace('[TRANSCRIPTION_LOG]', '').trim();
            console.log('🎯 [TRANSCRIPTION_LOG] detected! Message:', cleanMessage);
            this.addTranscriptionLog(cleanMessage);
            // Don't add to main logs, only to transcription terminal
          } else {
            // Regular progress message - add to main terminal logs
            console.log('📝 Adding regular log to main terminal:', data.message);
            this.addLog(data.message, data.type || 'info');
          }
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
    console.log(`📋 addLog called - text: "${text}", type: ${type}`);
    console.log(`📋 Current logs count before push: ${this.logs.length}`);
    
    const log: LogMessage = {
      id: this.logIdCounter++,
      text,
      type,
      timestamp: new Date(),
      visible: false
    };

    this.logs.push(log);
    console.log(`📋 Logs count after push: ${this.logs.length}`);
    console.log(`📋 Logs array:`, this.logs.map(l => l.text));
    
    this.cdr.detectChanges(); // Force immediate change detection
    
    // Save state after each log update
    this.saveStateToStorage();

    // Animate in with slight delay
    setTimeout(() => {
      log.visible = true;
      console.log(`📋 Log ${log.id} set to visible: true`);
      this.cdr.detectChanges(); // Force change detection again
      this.scrollToBottom();
    }, 100);
  }

  private handleCompletion(): void {
    // Stop timer and record end time
    this.stopTimer();
    this.analysisEndTime = Date.now();
    
    const totalSeconds = Math.floor((this.analysisEndTime - (this.analysisStartTime || 0)) / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    // Save processing time to backend
    if (this.createdTopicId && totalSeconds > 0) {
      this.apiService.updateTopic(this.createdTopicId, { 
        processing_time_seconds: totalSeconds 
      }).subscribe({
        next: () => console.log('Processing time saved'),
        error: (err) => console.error('Error saving processing time:', err)
      });
    }
    
    setTimeout(() => {
      this.addLog('', 'info');
      this.addLog('✅ Analysis Complete!', 'success');
      this.addLog(`⏱️ Total time: ${timeStr}`, 'success');
      this.addLog(`📊 Your insights are ready to explore!`, 'success');
      
      setTimeout(() => {
        // Hide yellow transcription terminal now that everything is done
        this.transcriptionState.isActive = false;
        this.transcriptionState.logs = [];
        if (this.transcriptionTimerInterval) {
          clearInterval(this.transcriptionTimerInterval);
          this.transcriptionTimerInterval = null;
        }
        
        this.currentState = 'complete';
        this.isProcessing = false;
        this.saveStateToStorage(); // Save complete state
        
        console.log('🎉 Setting currentState to complete');
        console.log('🎉 currentState:', this.currentState);
        
        this.cdr.detectChanges(); // Force immediate change detection
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

  // State persistence methods
  private saveStateToStorage(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const state = {
      currentState: this.currentState,
      topicInput: this.topicInput,
      logs: this.logs,
      createdTopicId: this.createdTopicId,
      isProcessing: this.isProcessing,
      analysisStartTime: this.analysisStartTime,
      elapsedTime: this.elapsedTime
    };

    try {
      sessionStorage.setItem('terminalState', JSON.stringify(state));
    } catch (error) {
      console.error('Failed to save state:', error);
    }
  }

  private restoreStateFromStorage(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    try {
      const savedState = sessionStorage.getItem('terminalState');
      if (!savedState) return;

      const state = JSON.parse(savedState);
      
      // Restore state
      this.currentState = state.currentState || 'chat';
      this.topicInput = state.topicInput || '';
      this.logs = state.logs || [];
      this.createdTopicId = state.createdTopicId || null;
      this.isProcessing = state.isProcessing || false;
      this.analysisStartTime = state.analysisStartTime || null;
      this.elapsedTime = state.elapsedTime || '0:00';

      // If was processing and not complete/error, reconnect to stream
      if (this.isProcessing && this.createdTopicId && 
          this.currentState === 'processing') {
        this.addLog('🔄 Reconnected after page refresh', 'info');
        this.connectToStream();
        this.startTimer();
      }
      
      // If state is complete or error, don't reconnect - just display saved logs
      // This allows users to refresh on complete page and see results

      // Mark all logs as visible immediately on restore
      this.logs.forEach(log => log.visible = true);
      
      this.cdr.markForCheck();
    } catch (error) {
      console.error('Failed to restore state:', error);
      sessionStorage.removeItem('terminalState');
    }
  }



  resetToChat(): void {
    // Clear sessionStorage
    if (isPlatformBrowser(this.platformId)) {
      sessionStorage.removeItem('terminalState');
    }
    
    // Reset component state completely
    this.currentState = 'chat';
    this.topicInput = '';
    this.logs = [];
    this.createdTopicId = null;
    this.isProcessing = false;
    this.closeEventSource();
    this.stopTimer();
    this.resetTimer();
    
    // Reset transcription state
    this.transcriptionState = {
      isActive: false,
      startTime: null,
      elapsedTime: '0:00',
      logs: []
    };
    
    if (this.transcriptionTimerInterval) {
      clearInterval(this.transcriptionTimerInterval);
      this.transcriptionTimerInterval = null;
    }
    
    // Force change detection
    this.cdr.markForCheck();
    
    // Navigate to create-analysis (will reuse component but state is now reset)
    this.router.navigate(['/create-analysis'], { 
      queryParams: { refresh: Date.now() } // Force Angular to recognize route change
    });
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
      'emoji': '',
      'transcription': '🎙️'
    };
    return icons[type] || '•';
  }
  
  // Transcription subprocess management
  private startTranscriptionSubProcess(): void {
    console.log('🔧 startTranscriptionSubProcess() EXECUTING');
    console.log('🔧 currentState:', this.currentState);
    this.transcriptionState = {
      isActive: true,
      startTime: Date.now(),
      elapsedTime: '0:00',
      logs: []
    };
    console.log('🔧 transcriptionState set to:', this.transcriptionState);
    console.log('🔧 transcriptionState.isActive:', this.transcriptionState.isActive);
    
    // Start transcription timer
    this.transcriptionTimerInterval = setInterval(() => {
      if (this.transcriptionState.startTime) {
        const elapsed = Math.floor((Date.now() - this.transcriptionState.startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        this.transcriptionState.elapsedTime = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        this.cdr.markForCheck();
      }
    }, 1000);
    
    console.log('🔧 Calling cdr.markForCheck()');
    this.cdr.markForCheck();
    console.log('🔧 startTranscriptionSubProcess() COMPLETE');
  }
  
  private endTranscriptionSubProcess(): void {
    // Don't hide the terminal immediately - keep it visible for all videos
    // Just add a completion message to show this video is done
    const completionLog: LogMessage = {
      id: this.logIdCounter++,
      text: '✅ Video transcription complete',
      type: 'transcription',
      timestamp: new Date(),
      visible: true,
      isTranscriptionLog: true
    };
    
    this.transcriptionState.logs.push(completionLog);
    this.cdr.detectChanges();
    this.scrollTranscriptionToBottom();
    
    // Terminal will stay visible until analysis completes
  }
  
  private addTranscriptionLog(text: string): void {
    const log: LogMessage = {
      id: this.logIdCounter++,
      text,
      type: 'transcription',
      timestamp: new Date(),
      visible: false,
      isTranscriptionLog: true
    };
    
    this.transcriptionState.logs.push(log);
    this.cdr.markForCheck();
    
    // Animate in
    setTimeout(() => {
      log.visible = true;
      this.cdr.markForCheck();
      this.scrollTranscriptionToBottom();
    }, 50);
  }
  
  private scrollTranscriptionToBottom(): void {
    if (isPlatformBrowser(this.platformId)) {
      setTimeout(() => {
        const transcriptionLogs = document.querySelector('.transcription-logs');
        if (transcriptionLogs) {
          transcriptionLogs.scrollTop = transcriptionLogs.scrollHeight;
        }
      }, 100);
    }
  }
  
  // Timer management methods
  private startTimer(): void {
    this.analysisStartTime = Date.now();
    this.analysisEndTime = null;
    this.elapsedTime = '0:00';
    
    // Update timer every second
    this.timerInterval = setInterval(() => {
      if (this.analysisStartTime) {
        const elapsed = Math.floor((Date.now() - this.analysisStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        this.elapsedTime = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        this.cdr.markForCheck();
      }
    }, 1000);
  }
  
  private stopTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }
  
  private resetTimer(): void {
    this.analysisStartTime = null;
    this.analysisEndTime = null;
    this.elapsedTime = '0:00';
  }
  
  getFormattedDuration(): string {
    if (!this.analysisStartTime) return '0:00';
    
    const endTime = this.analysisEndTime || Date.now();
    const totalSeconds = Math.floor((endTime - this.analysisStartTime) / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
}
