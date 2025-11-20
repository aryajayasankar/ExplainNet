import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ThemeService } from '../../services/theme.service';
import { Topic, TopicCreate } from '../../models/topic.model';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-locker',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './locker.component.html',
  styleUrls: ['./locker.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LockerComponent implements OnInit, OnDestroy {
  topics: Topic[] = [];
  loading = true;
  showCreateModal = false;
  newTopicName = '';
  creating = false;
  private pollingSubscription?: Subscription;
  private analyzedVideoCounts: Map<number, number> = new Map();
  private analyzedArticleCounts: Map<number, number> = new Map();

  constructor(
    private apiService: ApiService,
    public themeService: ThemeService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadTopics();
    this.startPolling();
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  startPolling() {
    // Poll every 5 seconds for updates on processing topics
    this.pollingSubscription = interval(5000)
      .pipe(switchMap(() => this.apiService.getTopics()))
      .subscribe({
        next: (topics) => {
          const hasProcessing = topics.some(t => t.analysis_status === 'processing');
          if (hasProcessing) {
            this.topics = topics;
            this.cdr.markForCheck();
          }
        },
        error: (err) => console.error('Polling error:', err)
      });
  }

  stopPolling() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
  }

  loadTopics() {
    this.loading = true;
    this.cdr.markForCheck();
    
    this.apiService.getTopics().subscribe({
      next: (topics) => {
        this.topics = topics;
        this.loading = false;
        
        // Load analyzed video counts for completed topics
        topics.forEach(topic => {
          if (topic.analysis_status === 'completed') {
            this.loadAnalyzedVideoCount(topic.id);
            this.loadAnalyzedArticleCount(topic.id);
          }
        });
        
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading topics:', err);
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadAnalyzedVideoCount(topicId: number) {
    this.apiService.getVideosByTopic(topicId).subscribe({
      next: (videos) => {
        this.analyzedVideoCounts.set(topicId, videos.length);
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error(`Error loading video count for topic ${topicId}:`, err);
      }
    });
  }

  loadAnalyzedArticleCount(topicId: number) {
    this.apiService.getArticlesByTopic(topicId).subscribe({
      next: (articles) => {
        this.analyzedArticleCounts.set(topicId, articles.length);
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error(`Error loading article count for topic ${topicId}:`, err);
      }
    });
  }

  openCreateModal() {
    // Clear any old terminal state before navigating to ensure fresh start
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.removeItem('terminalState');
    }
    
    // Navigate to terminal/chat interface for new analysis
    this.router.navigate(['/create-analysis'], {
      queryParams: { t: Date.now() } // Add timestamp to force route refresh
    });
  }

  closeCreateModal() {
    this.showCreateModal = false;
    this.newTopicName = '';
  }

  createTopic() {
    if (!this.newTopicName.trim()) return;
    
    this.creating = true;
    this.cdr.markForCheck();
    const topicData: TopicCreate = { topic_name: this.newTopicName };
    
    this.apiService.createTopic(topicData).subscribe({
      next: (topic) => {
        this.topics.unshift(topic);
        this.closeCreateModal();
        this.creating = false;
        this.cdr.markForCheck();
        
        // Navigate to analysis page immediately
        this.router.navigate(['/analysis', topic.id]);
      },
      error: (err) => {
        console.error('Error creating topic:', err);
        this.creating = false;
        this.cdr.markForCheck();
      }
    });
  }

  navigateToAnalysis(topic: Topic, event?: Event) {
    if (event) event.stopPropagation();
    
    if (topic.analysis_status === 'completed') {
      this.router.navigate(['/analysis', topic.id]);
    }
  }

  getAnalyzedVideosCount(topicId: number): number | string {
    const count = this.analyzedVideoCounts.get(topicId);
    return count !== undefined ? count : '—';
  }

  getAnalyzedArticlesCount(topicId: number): number | string {
    const count = this.analyzedArticleCounts.get(topicId);
    return count !== undefined ? count : '—';
  }

  deleteTopic(id: number, event: Event) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this topic?')) return;
    
    this.apiService.deleteTopic(id).subscribe({
      next: () => {
        this.topics = this.topics.filter(t => t.id !== id);
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error deleting topic:', err);
      }
    });
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  goToLanding() {
    this.router.navigate(['/']);
  }

  trackByTopicId(index: number, topic: Topic): number {
    return topic.id;
  }

  getStatusClass(status: string): string {
    const classes: Record<string, string> = {
      completed: 'status-completed',
      processing: 'status-processing',
      pending: 'status-pending',
      failed: 'status-failed'
    };
    return classes[status] || '';
  }

  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      completed: '',
      processing: '',
      pending: '',
      failed: ''
    };
    return icons[status] || '?';
  }
  
  formatProcessingTime(seconds: number): string {
    if (!seconds || seconds === 0) return '';
    
    if (seconds < 60) {
      return `${seconds}s`;
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (remainingSeconds === 0) {
      return `${minutes}m`;
    }
    
    return `${minutes}m ${remainingSeconds}s`;
  }
}
