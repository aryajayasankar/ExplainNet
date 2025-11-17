import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Topic, Video, Sentiment, Comment, Transcript, NewsArticle } from '../../models/topic.model';

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './analysis.component.html',
  styleUrls: ['./analysis.component.scss']
})
export class AnalysisComponent implements OnInit {
  topicId!: number;
  topic: Topic | null = null;
  videos: Video[] = [];
  articles: NewsArticle[] = [];
  loading = true;
  
  // Tab management
  activeTab: 'videos' | 'news' | 'ai' = 'videos';
  
  // AI Summary data
  aiSummary: any = null;
  
  selectedVideo: Video | null = null;
  showVideoModal = false;
  videoSentiments: Sentiment[] = [];
  videoComments: Comment[] = [];
  videoTranscript: Transcript | null = null;
  
  searchTerm = '';
  sortBy = 'impact_score';
  sortDirection = 'desc';

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.topicId = +params['id'];
      this.loadData();
    });
  }

  loadData() {
    this.loading = true;
    
    this.apiService.getTopic(this.topicId).subscribe({
      next: (topic) => {
        this.topic = topic;
        this.loadVideos();
        this.loadArticles();
      },
      error: (err) => {
        console.error('Error loading topic:', err);
        this.loading = false;
      }
    });
  }

  loadVideos() {
    this.apiService.getVideosByTopic(this.topicId).subscribe({
      next: (videos) => {
        this.videos = videos;
        this.loading = false;
      },
      error: (err) => console.error('Error loading videos:', err)
    });
  }

  loadArticles() {
    this.apiService.getArticlesByTopic(this.topicId).subscribe({
      next: (articles) => {
        this.articles = articles;
      },
      error: (err) => console.error('Error loading articles:', err)
    });
  }

  get topVideo(): Video | null {
    return this.videos.length > 0 
      ? this.videos.reduce((max, v) => (v.impact_score || 0) > (max.impact_score || 0) ? v : max)
      : null;
  }

  get filteredVideos(): Video[] {
    let filtered = this.videos.filter(v => 
      v.title.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
      v.channel_title.toLowerCase().includes(this.searchTerm.toLowerCase())
    );
    
    return filtered.sort((a, b) => {
      const aVal = (a as any)[this.sortBy] || 0;
      const bVal = (b as any)[this.sortBy] || 0;
      return this.sortDirection === 'desc' ? bVal - aVal : aVal - bVal;
    });
  }

  get sentimentCounts() {
    const counts = { positive: 0, negative: 0, neutral: 0, mixed: 0 };
    this.videos.forEach(v => {
      const sentiment = v.overall_sentiment?.toLowerCase();
      if (sentiment && sentiment in counts) {
        counts[sentiment as keyof typeof counts]++;
      }
    });
    return counts;
  }

  openVideoModal(video: Video) {
    this.selectedVideo = video;
    this.showVideoModal = true;
    
    this.apiService.getSentimentsByVideo(video.id).subscribe({
      next: (sentiments) => this.videoSentiments = sentiments,
      error: (err) => console.error('Error loading sentiments:', err)
    });
    
    this.apiService.getCommentsByVideo(video.id).subscribe({
      next: (comments) => this.videoComments = comments,
      error: (err) => console.error('Error loading comments:', err)
    });
    
    this.apiService.getTranscriptByVideo(video.id).subscribe({
      next: (transcript) => this.videoTranscript = transcript,
      error: (err) => console.error('Error loading transcript:', err)
    });
  }

  closeVideoModal() {
    this.showVideoModal = false;
    this.selectedVideo = null;
    this.videoSentiments = [];
    this.videoComments = [];
    this.videoTranscript = null;
  }

  setSortBy(field: string) {
    if (this.sortBy === field) {
      this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
    } else {
      this.sortBy = field;
      this.sortDirection = 'desc';
    }
  }

  switchTab(tab: 'videos' | 'news' | 'ai') {
    this.activeTab = tab;
    if (tab === 'ai' && !this.aiSummary) {
      this.loadAISummary();
    }
  }

  loadAISummary() {
    this.apiService.getAISummary(this.topicId).subscribe({
      next: (summary) => this.aiSummary = summary,
      error: (err) => console.error('Error loading AI summary:', err)
    });
  }

  deleteTopic() {
    if (!confirm(`Delete topic "${this.topic?.topic_name}"?`)) return;

    // disable UI while deleting
    (this as any).deletingTopic = true;
    this.apiService.deleteTopic(this.topicId).subscribe({
      next: () => {
        (this as any).deletingTopic = false;
        this.router.navigate(['/locker']);
      },
      error: (err) => {
        (this as any).deletingTopic = false;
        console.error('Error deleting topic:', err);
      }
    });
  }

  // UI helpers for expandable justifications
  expandedArticles: Set<number> = new Set();
  expandedComments: Set<number> = new Set();
  expandedSentiments: Set<number> = new Set();

  toggleArticleExpand(id: number, event?: Event) {
    if (event) event.stopPropagation();
    if (this.expandedArticles.has(id)) this.expandedArticles.delete(id);
    else this.expandedArticles.add(id);
  }

  isArticleExpanded(id: number) {
    return this.expandedArticles.has(id);
  }

  toggleCommentExpand(id: number, event?: Event) {
    if (event) event.stopPropagation();
    if (this.expandedComments.has(id)) this.expandedComments.delete(id);
    else this.expandedComments.add(id);
  }

  isCommentExpanded(id: number) {
    return this.expandedComments.has(id);
  }

  toggleSentimentExpand(id: number, event?: Event) {
    if (event) event.stopPropagation();
    if (this.expandedSentiments.has(id)) this.expandedSentiments.delete(id);
    else this.expandedSentiments.add(id);
  }

  isSentimentExpanded(id: number) {
    return this.expandedSentiments.has(id);
  }

  getSentimentClass(sentiment?: string): string {
    return `sentiment-${sentiment?.toLowerCase() || 'neutral'}`;
  }

  formatNumber(num?: number): string {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  formatDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
      if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
      return `${Math.floor(diffDays / 365)} years ago`;
    } catch {
      return '';
    }
  }
}
