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
  
  // News timeline
  timelineSortOrder: 'asc' | 'desc' = 'desc';

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
        this.loadAISynthesis();
      },
      error: (err) => console.error('Error loading articles:', err)
    });
  }

  loadAISynthesis() {
    this.apiService.getAISynthesis(this.topicId).subscribe({
      next: (synthesis) => {
        this.aiSummary = synthesis;
      },
      error: (err) => console.error('Error loading AI synthesis:', err)
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

  get overallConfidence(): number {
    if (this.videos.length === 0) return 0;
    const totalConfidence = this.videos.reduce((sum, v) => sum + (v.confidence_score || 0), 0);
    return Math.round((totalConfidence / this.videos.length) * 100);
  }

  get dominantEmotion(): { name: string; percentage: number } | null {
    const emotionTotals: { [key: string]: number } = {};
    let videoCount = 0;

    this.videos.forEach(v => {
      if (v.emotions_json) {
        try {
          const emotions = JSON.parse(v.emotions_json);
          Object.entries(emotions).forEach(([name, value]) => {
            emotionTotals[name] = (emotionTotals[name] || 0) + (value as number);
          });
          videoCount++;
        } catch (error) {
          // Skip invalid JSON
        }
      }
    });

    if (videoCount === 0) return null;

    const emotionAverages = Object.entries(emotionTotals)
      .map(([name, total]) => ({ name, percentage: Math.round(total / videoCount) }))
      .sort((a, b) => b.percentage - a.percentage);

    return emotionAverages[0] || null;
  }

  get sentimentTrend(): 'up' | 'down' | 'stable' {
    if (this.videos.length < 2) return 'stable';
    
    const firstHalf = this.videos.slice(0, Math.floor(this.videos.length / 2));
    const secondHalf = this.videos.slice(Math.floor(this.videos.length / 2));
    
    const firstPositive = firstHalf.filter(v => v.overall_sentiment === 'positive').length / firstHalf.length;
    const secondPositive = secondHalf.filter(v => v.overall_sentiment === 'positive').length / secondHalf.length;
    
    if (secondPositive > firstPositive + 0.1) return 'up';
    if (secondPositive < firstPositive - 0.1) return 'down';
    return 'stable';
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

  parseEmotions(emotionsJson: string | null): { name: string; value: number }[] {
    if (!emotionsJson) return [];
    try {
      const emotions = JSON.parse(emotionsJson);
      return Object.entries(emotions)
        .map(([name, value]) => ({ 
          name, 
          value: typeof value === 'number' ? Math.round(value) : 0 
        }))
        .filter(e => e.value > 0); // Only show emotions with non-zero values
    } catch (error) {
      console.error('Error parsing emotions JSON:', error);
      return [];
    }
  }

  getEmotionIcon(emotion: string): string {
    const icons: { [key: string]: string } = {
      'joy': '😊',
      'sadness': '😢',
      'anger': '😠',
      'fear': '😨',
      'surprise': '😲',
      'disgust': '🤢'
    };
    return icons[emotion.toLowerCase()] || '😐';
  }

  // Video Analytics Dashboard Calculations
  get impactDistribution() {
    const distribution = { low: 0, medium: 0, high: 0, lowCount: 0, mediumCount: 0, highCount: 0 };
    this.videos.forEach(v => {
      const score = v.impact_score || 0;
      if (score < 2) { distribution.lowCount++; }
      else if (score < 4) { distribution.mediumCount++; }
      else { distribution.highCount++; }
    });
    const total = this.videos.length || 1;
    distribution.low = Math.round((distribution.lowCount / total) * 100);
    distribution.medium = Math.round((distribution.mediumCount / total) * 100);
    distribution.high = Math.round((distribution.highCount / total) * 100);
    return distribution;
  }

  getScatterX(views: number | undefined): number {
    if (!views) return 0;
    const maxViews = Math.max(...this.videos.map(v => v.view_count || 0));
    return Math.min(((views / maxViews) * 90) + 5, 95);
  }

  getScatterY(sentiment: string | undefined): number {
    const sentimentMap: { [key: string]: number } = {
      'positive': 80,
      'neutral': 45,
      'negative': 10,
      'mixed': 60
    };
    return sentimentMap[sentiment?.toLowerCase() || 'neutral'] || 45;
  }

  get topEngagementVideos() {
    return this.videos
      .map(v => ({
        title: v.title,
        engagementRatio: v.like_count && v.view_count ? 
          Math.round((v.like_count / v.view_count) * 10000) / 100 : 0,
        engagementPercentage: 0
      }))
      .sort((a, b) => b.engagementRatio - a.engagementRatio)
      .slice(0, 5)
      .map((v, i, arr) => ({
        ...v,
        engagementPercentage: arr[0].engagementRatio > 0 ? 
          Math.round((v.engagementRatio / arr[0].engagementRatio) * 100) : 0
      }));
  }

  getEmotionPoints(emotion: string): string {
    // This would ideally parse emotions from video data
    // For now, return a placeholder
    return '0,50 25,30 50,60 75,40 100,20';
  }

  get viewDistribution() {
    const maxViews = Math.max(...this.videos.map(v => v.view_count || 0));
    const bucketSize = Math.ceil(maxViews / 5);
    const buckets = Array(5).fill(0).map((_, i) => ({
      range: `${i * bucketSize}-${(i + 1) * bucketSize}`,
      label: this.formatNumber(i * bucketSize),
      count: 0,
      percentage: 0
    }));

    this.videos.forEach(v => {
      const views = v.view_count || 0;
      const bucketIndex = Math.min(Math.floor(views / bucketSize), 4);
      buckets[bucketIndex].count++;
    });

    const maxCount = Math.max(...buckets.map(b => b.count), 1);
    buckets.forEach(b => {
      b.percentage = Math.round((b.count / maxCount) * 100);
    });

    return buckets;
  }

  get impactTrendPoints(): string {
    const points = this.videos.map((v, i) => {
      const x = (i / Math.max(this.videos.length - 1, 1)) * 380 + 10;
      const y = 190 - ((v.impact_score || 0) / 5) * 170;
      return `${x},${y}`;
    });
    // Add bottom corners for filled area
    if (points.length > 0) {
      const lastX = (this.videos.length - 1) / Math.max(this.videos.length - 1, 1) * 380 + 10;
      points.push(`${lastX},190`);
      points.push('10,190');
    }
    return points.join(' ');
  }

  get impactTrendLine(): string {
    return this.videos.map((v, i) => {
      const x = (i / Math.max(this.videos.length - 1, 1)) * 380 + 10;
      const y = 190 - ((v.impact_score || 0) / 5) * 170;
      return `${x},${y}`;
    }).join(' ');
  }

  get averageImpact(): number {
    if (this.videos.length === 0) return 0;
    const sum = this.videos.reduce((acc, v) => acc + (v.impact_score || 0), 0);
    return sum / this.videos.length;
  }

  get maxImpact(): number {
    return Math.max(...this.videos.map(v => v.impact_score || 0), 0);
  }

  // News Timeline Methods
  get sortedArticles(): NewsArticle[] {
    return [...this.articles].sort((a, b) => {
      const dateA = new Date(a.published_at).getTime();
      const dateB = new Date(b.published_at).getTime();
      return this.timelineSortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    });
  }

  getTimelinePosition(dateString: string): number {
    if (this.articles.length === 0) return 50;
    
    const dates = this.articles.map(a => new Date(a.published_at).getTime());
    const minDate = Math.min(...dates);
    const maxDate = Math.max(...dates);
    const currentDate = new Date(dateString).getTime();
    
    if (maxDate === minDate) return 50;
    return ((currentDate - minDate) / (maxDate - minDate)) * 90 + 5;
  }

  getRelevanceColor(relevance: number | null | undefined): string {
    if (!relevance) return '#6b7280';
    if (relevance >= 75) return '#22c55e';
    if (relevance >= 50) return '#fbbf24';
    if (relevance >= 25) return '#f59e0b';
    return '#ef4444';
  }

  get timelineStartDate(): string {
    if (this.articles.length === 0) return '';
    const dates = this.articles.map(a => new Date(a.published_at));
    const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
    return minDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  get timelineEndDate(): string {
    if (this.articles.length === 0) return '';
    const dates = this.articles.map(a => new Date(a.published_at));
    const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));
    return maxDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  get averageRelevance(): number {
    const relevantArticles = this.articles.filter(a => a.relevance_score !== null && a.relevance_score !== undefined);
    if (relevantArticles.length === 0) return 0;
    const sum = relevantArticles.reduce((acc, a) => acc + (a.relevance_score || 0), 0);
    return sum / relevantArticles.length;
  }

  get articleDateRange(): string {
    if (this.articles.length === 0) return '0 days';
    const dates = this.articles.map(a => new Date(a.published_at).getTime());
    const diffMs = Math.max(...dates) - Math.min(...dates);
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Same day';
    if (diffDays === 1) return '1 day';
    if (diffDays < 30) return `${diffDays} days`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months`;
    return `${Math.floor(diffDays / 365)} years`;
  }

  getSentimentIcon(sentiment: string | undefined): string {
    const icons: { [key: string]: string } = {
      'positive': '😊',
      'negative': '😞',
      'neutral': '😐',
      'mixed': '😕'
    };
    return icons[sentiment?.toLowerCase() || 'neutral'] || '😐';
  }

  getQualityPercentage(): number {
    // Calculate quality based on average impact and relevance
    const impactPercent = (this.averageImpact / 5) * 50; // 50% weight
    const relevancePercent = (this.averageRelevance / 100) * 50; // 50% weight
    return Math.round(impactPercent + relevancePercent);
  }

  getRandomOpacity(): number {
    return 0.3 + Math.random() * 0.7;
  }

  Math = Math;
}
