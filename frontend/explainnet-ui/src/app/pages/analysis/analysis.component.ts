import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ThemeService } from '../../services/theme.service';
import { Topic, Video, Sentiment, Comment, Transcript, NewsArticle } from '../../models/topic.model';

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './analysis.component.html',
  styleUrls: ['./analysis.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AnalysisComponent implements OnInit {
  topicId!: number;
  topic: Topic | null = null;
  videos: Video[] = [];
  articles: NewsArticle[] = [];
  newsAnalysis: any = null;
  aiAnalytics: any = null;
  loading = true;
  
  // Tab management
  activeTab: 'videos' | 'news' | 'ai' | 'overview' = 'overview';
  modalTab: 'transcript' | 'sentiment' | 'comments' = 'transcript';
  videoSubTab: 'overview' | 'gnn' = 'overview';
  
  // AI Summary data
  aiSummary: any = null;
  regeneratingAI = false;
  
  // GNN data from backend
  gnnData: { nodes: any[], edges: any[] } = { nodes: [], edges: [] };
  
  selectedVideo: Video | null = null;
  showVideoModal = false;
  videoSentiments: Sentiment[] = [];
  videoComments: Comment[] = [];
  videoTranscript: Transcript | null = null;
  
  // Loading states for modal
  transcriptLoading = false;
  sentimentsLoading = false;
  commentsLoading = false;
  transcriptError: string | null = null;
  
  searchTerm = '';
  sortBy = 'impact_score';
  sortDirection = 'desc';
  
  // News timeline
  timelineSortOrder: 'asc' | 'desc' = 'desc';

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router,
    public themeService: ThemeService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.topicId = +params['id'];
      this.loadData();
    });
  }

  loadData() {
    this.loading = true;
    this.cdr.markForCheck();
    
    this.apiService.getTopic(this.topicId).subscribe({
      next: (topic) => {
        this.topic = topic;
        console.log('📊 Topic loaded:', topic);
        console.log('📊 Overall sentiment:', topic.overall_sentiment);
        console.log('📊 Overall impact score:', topic.overall_impact_score);
        console.log('📊 Total videos:', topic.total_videos);
        console.log('📊 Total articles:', topic.total_articles);
        this.loadVideos();
        this.loadArticles();
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading topic:', err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadVideos() {
    this.apiService.getVideosByTopic(this.topicId).subscribe({
      next: (videos) => {
        this.videos = videos;
        console.log(`📹 Loaded ${videos.length} videos`);
        console.log('📹 First video sample:', videos[0]);
        console.log('📹 Video emotions check:', videos.map(v => ({ 
          id: v.id, 
          title: v.title.substring(0, 30), 
          hasEmotions: !!(v.emotions || v.emotions_json),
          emotions: v.emotions || v.emotions_json 
        })));
        console.log('📹 Video impact scores:', videos.map(v => v.impact_score));
        console.log('📹 Calculated average impact:', this.averageImpact);
        
        // Load GNN data from backend
        this.loadGNNData();
        
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading videos:', err);
        this.cdr.detectChanges();
      }
    });
  }

  loadGNNData() {
    this.apiService.getVideosGNN(this.topicId).subscribe({
      next: (gnnData) => {
        this.gnnData = gnnData;
        console.log('🕸️ GNN data loaded:', gnnData);
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading GNN data:', err);
        this.cdr.markForCheck();
      }
    });
  }

  loadArticles() {
    this.apiService.getArticlesByTopic(this.topicId).subscribe({
      next: (articles) => {
        this.articles = articles;
        this.loadNewsAnalysis();
        this.loadAISynthesis();
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading articles:', err);
        this.cdr.markForCheck();
      }
    });
  }

  loadNewsAnalysis() {
    this.apiService.getNewsAnalysis(this.topicId).subscribe({
      next: (analysis) => {
        this.newsAnalysis = analysis;
        console.log('📰 News analysis loaded:', analysis);
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading news analysis:', err);
        this.cdr.markForCheck();
      }
    });
  }

  loadAISynthesis(forceRefresh: boolean = false) {
    if (forceRefresh) {
      this.regeneratingAI = true;
      this.cdr.markForCheck();
    }
    
    this.apiService.getAISynthesis(this.topicId, forceRefresh).subscribe({
      next: (synthesis) => {
        this.aiSummary = synthesis;
        this.regeneratingAI = false;
        this.loadAIAnalytics();
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading AI synthesis:', err);
        this.regeneratingAI = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadAIAnalytics() {
    this.apiService.getAIAnalytics(this.topicId).subscribe({
      next: (analytics) => {
        this.aiAnalytics = analytics;
        console.log('🤖 AI analytics loaded:', analytics);
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading AI analytics:', err);
        this.cdr.markForCheck();
      }
    });
  }
  
  regenerateAIInsights() {
    this.aiSummary = null;
    this.loadAISynthesis(true);
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
      const emotionsStr = v.emotions_json || v.emotions;
      if (emotionsStr) {
        try {
          const emotions = typeof emotionsStr === 'string' ? JSON.parse(emotionsStr) : emotionsStr;
          if (emotions && typeof emotions === 'object') {
            Object.entries(emotions).forEach(([name, value]) => {
              const numValue = parseInt(String(value || 0), 10) || 0;
              emotionTotals[name] = (emotionTotals[name] || 0) + numValue;
            });
            videoCount++;
          }
        } catch (error) {
          console.error('Error parsing dominant emotion:', error);
        }
      }
    });

    if (videoCount === 0) return null;

    const emotionAverages = Object.entries(emotionTotals)
      .map(([name, total]) => ({ 
        name, 
        percentage: Math.min(100, Math.max(0, Math.round(total / videoCount)))
      }))
      .sort((a, b) => b.percentage - a.percentage);

    return emotionAverages[0] || null;
  }

  // Emotion Heatmap Data - Compact version showing top emotions
  getEmotionHeatmapData(): Array<{ emotion: string; icon: string; intensity: number; color: string }> {
    const emotionTotals: { [key: string]: number } = {};
    let videoCount = 0;

    this.videos.forEach(v => {
      const emotionsStr = v.emotions_json || v.emotions;
      if (emotionsStr) {
        try {
          const emotions = typeof emotionsStr === 'string' ? JSON.parse(emotionsStr) : emotionsStr;
          if (emotions && typeof emotions === 'object') {
            Object.entries(emotions).forEach(([name, value]) => {
              const numValue = parseInt(String(value || 0), 10) || 0;
              emotionTotals[name] = (emotionTotals[name] || 0) + numValue;
            });
            videoCount++;
          }
        } catch (error) {
          console.error('Error parsing emotions:', error, 'Raw:', emotionsStr);
        }
      }
    });

    console.log('🎭 Emotion aggregation:', { videoCount, emotionTotals, totalVideos: this.videos.length });

    const emotionConfig: { [key: string]: { icon: string; color: string } } = {
      'joy': { icon: '😊', color: '#fbbf24' },
      'sadness': { icon: '😢', color: '#38bdf8' },
      'anger': { icon: '😠', color: '#f87171' },
      'fear': { icon: '😨', color: '#c084fc' },
      'surprise': { icon: '😲', color: '#fb923c' },
      'disgust': { icon: '🤢', color: '#4ade80' },
      'love': { icon: '💖', color: '#ec4899' },
      'trust': { icon: '🤝', color: '#60a5fa' },
      'anticipation': { icon: '🤩', color: '#a78bfa' },
      'neutral': { icon: '😐', color: '#94a3b8' }
    };

    if (videoCount === 0) {
      return Object.entries(emotionConfig).slice(0, 6).map(([name, config]) => ({
        emotion: name.charAt(0).toUpperCase() + name.slice(1),
        icon: config.icon,
        intensity: 0,
        color: config.color
      }));
    }

    return Object.entries(emotionTotals)
      .map(([name, total]) => {
        const normalized = name.toLowerCase();
        const config = emotionConfig[normalized] || { icon: '😐', color: '#94a3b8' };
        return {
          emotion: name.charAt(0).toUpperCase() + name.slice(1),
          icon: config.icon,
          intensity: Math.round((total / videoCount) * 100) / 100,
          color: config.color
        };
      })
      .sort((a, b) => b.intensity - a.intensity);
  }

  // Video Impact Score Bar Chart Data
  getVideoImpactScoreData(): Array<{ title: string; impactScore: number; percentage: number; rank: number }> {
    const sortedVideos = [...this.videos]
      .filter(v => v.impact_score !== null && v.impact_score !== undefined)
      .sort((a, b) => (b.impact_score || 0) - (a.impact_score || 0))
      .slice(0, 10);

    const maxScore = sortedVideos.length > 0 ? (sortedVideos[0].impact_score || 1) : 1;

    return sortedVideos.map((video, index) => ({
      title: video.title.length > 50 ? video.title.substring(0, 50) + '...' : video.title,
      impactScore: video.impact_score || 0,
      percentage: ((video.impact_score || 0) / maxScore) * 100,
      rank: index + 1
    }));
  }

  // Video Views Bar Chart Data
  getVideoViewsData(): Array<{ title: string; views: number; viewsFormatted: string; percentage: number; rank: number }> {
    const sortedVideos = [...this.videos]
      .filter(v => v.view_count !== null && v.view_count !== undefined)
      .sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
      .slice(0, 10);

    const maxViews = sortedVideos.length > 0 ? (sortedVideos[0].view_count || 1) : 1;

    return sortedVideos.map((video, index) => ({
      title: video.title.length > 50 ? video.title.substring(0, 50) + '...' : video.title,
      views: video.view_count || 0,
      viewsFormatted: this.formatNumber(video.view_count || 0),
      percentage: ((video.view_count || 0) / maxViews) * 100,
      rank: index + 1
    }));
  }

  // Video Engagement Data
  getVideoEngagementData(): Array<{ 
    title: string; 
    likes: number; 
    likesFormatted: string;
    likesPercentage: number;
    comments: number; 
    commentsFormatted: string;
    commentsPercentage: number;
    engagement: number;
    engagementFormatted: string;
  }> {
    const sortedVideos = [...this.videos]
      .sort((a, b) => {
        const engagementA = (a.like_count || 0) + (a.comment_count || 0);
        const engagementB = (b.like_count || 0) + (b.comment_count || 0);
        return engagementB - engagementA;
      })
      .slice(0, 10);

    const maxLikes = Math.max(...sortedVideos.map(v => v.like_count || 0), 1);
    const maxComments = Math.max(...sortedVideos.map(v => v.comment_count || 0), 1);

    return sortedVideos.map(video => {
      const totalEngagement = (video.like_count || 0) + (video.comment_count || 0);
      return {
        title: video.title.length > 45 ? video.title.substring(0, 45) + '...' : video.title,
        likes: video.like_count || 0,
        likesFormatted: this.formatNumber(video.like_count || 0),
        likesPercentage: ((video.like_count || 0) / maxLikes) * 100,
        comments: video.comment_count || 0,
        commentsFormatted: this.formatNumber(video.comment_count || 0),
        commentsPercentage: ((video.comment_count || 0) / maxComments) * 100,
        engagement: totalEngagement,
        engagementFormatted: this.formatNumber(totalEngagement)
      };
    });
  }

  getVideoEmotionRadarData(): Array<{
    title: string;
    emotions: { [key: string]: number };
    radarPoints: string;
    maxEmotion: string;
    totalEmotions: number;
  }> {
    const emotionKeys = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'love'];
    
    return this.videos.slice(0, 6).map(video => {
      const emotions = video.emotions ? JSON.parse(video.emotions) : {};
      const emotionValues = emotionKeys.map(key => emotions[key] || 0);
      const maxValue = Math.max(...emotionValues, 1);
      const total = emotionValues.reduce((sum, val) => sum + val, 0);
      
      // Calculate radar polygon points (hexagon)
      const centerX = 100;
      const centerY = 100;
      const radius = 80;
      const angleStep = (Math.PI * 2) / 6;
      
      const points = emotionValues.map((value, index) => {
        const angle = angleStep * index - Math.PI / 2; // Start from top
        const normalized = (value / maxValue) * radius;
        const x = centerX + normalized * Math.cos(angle);
        const y = centerY + normalized * Math.sin(angle);
        return `${x},${y}`;
      }).join(' ');
      
      // Find dominant emotion
      const maxEmotionIndex = emotionValues.indexOf(Math.max(...emotionValues));
      const maxEmotion = emotionKeys[maxEmotionIndex];
      
      return {
        title: video.title.length > 40 ? video.title.substring(0, 40) + '...' : video.title,
        emotions: emotionKeys.reduce((acc, key, idx) => {
          acc[key] = emotionValues[idx];
          return acc;
        }, {} as { [key: string]: number }),
        radarPoints: points,
        maxEmotion: maxEmotion,
        totalEmotions: total
      };
    });
  }

  getOverallEmotionRadarData(): {
    emotions: { [key: string]: number };
    radarPoints: string;
    maxEmotion: string;
    totalEmotions: number;
  } {
    const emotionKeys = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'love'];
    
    // Aggregate emotions from all videos
    const aggregatedEmotions: { [key: string]: number } = {};
    emotionKeys.forEach(key => aggregatedEmotions[key] = 0);
    
    let videoCount = 0;
    this.videos.forEach(video => {
      const emotionsStr = video.emotions_json || video.emotions;
      if (emotionsStr) {
        try {
          const emotions = typeof emotionsStr === 'string' ? JSON.parse(emotionsStr) : emotionsStr;
          if (emotions && typeof emotions === 'object') {
            emotionKeys.forEach(key => {
              const val = parseInt(String(emotions[key] || 0), 10) || 0;
              aggregatedEmotions[key] += val;
            });
            videoCount++;
          }
        } catch (error) {
          console.error('Error parsing emotions for radar:', error, emotionsStr);
        }
      }
    });
    
    console.log('📡 Overall emotion radar:', { videoCount, aggregatedEmotions });
    
    const emotionValues = emotionKeys.map(key => aggregatedEmotions[key]);
    const maxValue = Math.max(...emotionValues, 1);
    const total = emotionValues.reduce((sum, val) => sum + val, 0);
    
    // Calculate radar polygon points (hexagon)
    const centerX = 100;
    const centerY = 100;
    const radius = 80;
    const angleStep = (Math.PI * 2) / 6;
    
    const points = emotionValues.map((value, index) => {
      const angle = angleStep * index - Math.PI / 2;
      const normalized = (value / maxValue) * radius;
      const x = centerX + normalized * Math.cos(angle);
      const y = centerY + normalized * Math.sin(angle);
      return `${x},${y}`;
    }).join(' ');
    
    // Find dominant emotion
    const maxEmotionIndex = emotionValues.indexOf(Math.max(...emotionValues));
    const maxEmotion = emotionKeys[maxEmotionIndex];
    
    return {
      emotions: aggregatedEmotions,
      radarPoints: points,
      maxEmotion: maxEmotion,
      totalEmotions: total
    };
  }

  getVideoGNNData(): any[] {
    // Return nodes from backend GNN data
    return this.gnnData.nodes || [];
  }

  getVideoGNNEdges(): any[] {
    // Return edges from backend GNN data
    return this.gnnData.edges || [];
  }

  getNodeById(nodeId: number): any {
    // Find node by ID for edge rendering
    return this.gnnData.nodes?.find(n => n.id === nodeId);
  }

  getNodeConnections(nodeId: number): number {
    // Count connections for a node
    const edges = this.gnnData.edges || [];
    return edges.filter(e => e.source === nodeId || e.target === nodeId).length;
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
    
    // Reset states
    this.videoSentiments = [];
    this.videoComments = [];
    this.videoTranscript = null;
    this.transcriptError = null;
    
    // Load sentiments
    this.sentimentsLoading = true;
    this.apiService.getSentimentsByVideo(video.id).subscribe({
      next: (sentiments) => {
        this.videoSentiments = sentiments;
        this.sentimentsLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading sentiments:', err);
        this.sentimentsLoading = false;
        this.cdr.markForCheck();
      }
    });
    
    // Load comments
    this.commentsLoading = true;
    this.apiService.getCommentsByVideo(video.id).subscribe({
      next: (comments) => {
        this.videoComments = comments;
        this.commentsLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading comments:', err);
        this.commentsLoading = false;
        this.cdr.markForCheck();
      }
    });
    
    // Load transcript
    this.transcriptLoading = true;
    this.apiService.getTranscriptByVideo(video.id).subscribe({
      next: (transcript) => {
        this.videoTranscript = transcript;
        this.transcriptLoading = false;
        this.transcriptError = null;
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error loading transcript:', err);
        this.transcriptLoading = false;
        // Extract error message from backend
        if (err.error && err.error.detail) {
          this.transcriptError = err.error.detail;
        } else if (err.status === 404) {
          this.transcriptError = 'Transcript not available for this video';
        } else {
          this.transcriptError = 'Failed to load transcript';
        }
        this.cdr.markForCheck();
      }
    });
  }

  closeVideoModal() {
    this.showVideoModal = false;
    this.selectedVideo = null;
    this.videoSentiments = [];
    this.videoComments = [];
    this.videoTranscript = null;
    this.transcriptLoading = false;
    this.sentimentsLoading = false;
    this.commentsLoading = false;
    this.transcriptError = null;
  }

  setSortBy(field: string) {
    if (this.sortBy === field) {
      this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
    } else {
      this.sortBy = field;
      this.sortDirection = 'desc';
    }
  }

  switchTab(tab: 'videos' | 'news' | 'ai' | 'overview') {
    this.activeTab = tab;
    if (tab === 'ai' && !this.aiSummary) {
      this.loadAISynthesis();
    }
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  exportData() {
    // TODO: Implement export functionality
    console.log('Export data');
  }

  getPercentage(count: number): number {
    const total = this.videos.length || 1;
    return Math.round((count / total) * 100);
  }

  getSparklinePoints(): string {
    if (this.videos.length === 0) return '0,50 100,50';
    const points = this.videos.map((v, i) => {
      const x = (i / Math.max(this.videos.length - 1, 1)) * 200;
      const sentiment = v.overall_sentiment?.toLowerCase();
      const y = sentiment === 'positive' ? 20 : sentiment === 'negative' ? 80 : 50;
      return `${x},${y}`;
    });
    return points.join(' ');
  }

  getAvgViews(): string {
    if (this.videos.length === 0) return '0';
    const avg = this.videos.reduce((sum, v) => sum + (v.view_count || 0), 0) / this.videos.length;
    return this.formatNumber(avg);
  }

  getTotalLikes(): string {
    const total = this.videos.reduce((sum, v) => sum + (v.like_count || 0), 0);
    return this.formatNumber(total);
  }

  getTotalComments(): string {
    const total = this.videos.reduce((sum, v) => sum + (v.comment_count || 0), 0);
    return this.formatNumber(total);
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

  // Convert markdown-style bold syntax (**text**) to HTML
  formatMarkdown(text: string): string {
    if (!text) return '';
    // Replace **bold** with <strong>bold</strong>
    return text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  }

  // News Chart Data Helpers
  getSourceDistributionData(): { source: string; count: number; percentage: number }[] {
    if (!this.newsAnalysis || !this.newsAnalysis.sources) return [];
    
    const total = this.newsAnalysis.total_articles || 1;
    return Object.entries(this.newsAnalysis.sources)
      .map(([source, count]) => ({
        source,
        count: count as number,
        percentage: Math.round(((count as number) / total) * 100)
      }))
      .sort((a, b) => b.count - a.count);
  }

  getRelevanceHistogramData(): { range: string; count: number; percentage: number }[] {
    if (!this.articles || this.articles.length === 0) return [];
    
    const bins = [
      { range: '0-25%', min: 0, max: 25, count: 0 },
      { range: '26-50%', min: 26, max: 50, count: 0 },
      { range: '51-75%', min: 51, max: 75, count: 0 },
      { range: '76-100%', min: 76, max: 100, count: 0 }
    ];

    this.articles.forEach(article => {
      const score = article.relevance_score || 50;
      const bin = bins.find(b => score >= b.min && score <= b.max);
      if (bin) bin.count++;
    });

    const total = this.articles.length;
    return bins.map(bin => ({
      range: bin.range,
      count: bin.count,
      percentage: Math.round((bin.count / total) * 100)
    }));
  }

  getRelevanceBarWidth(count: number): number {
    if (!this.articles || this.articles.length === 0) return 0;
    return (count / this.articles.length) * 100;
  }

  getSourceBarWidth(count: number): number {
    if (!this.newsAnalysis || !this.newsAnalysis.total_articles) return 0;
    return (count / this.newsAnalysis.total_articles) * 100;
  }

  getRelevanceRangeColor(range: string): string {
    const colors: { [key: string]: string } = {
      '0-25%': '#ef4444',
      '26-50%': '#f59e0b',
      '51-75%': '#3b82f6',
      '76-100%': '#22c55e'
    };
    return colors[range] || '#6b7280';
  }

  getSourceBarColor(index: number): string {
    const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#6366f1', '#f43f5e'];
    return colors[index % colors.length];
  }

  // AI Analytics Chart Helpers
  getModelAgreementData(): { label: string; count: number; percentage: number; color: string }[] {
    if (!this.aiAnalytics || !this.aiAnalytics.model_agreement) return [];
    
    const agreement = this.aiAnalytics.model_agreement;
    const total = this.aiAnalytics.total_videos || 1;
    
    const agreePositive = agreement.both_agree?.positive || 0;
    const agreeNegative = agreement.both_agree?.negative || 0;
    const agreeNeutral = agreement.both_agree?.neutral || 0;
    const disagree = agreement.disagree || 0;
    
    return [
      {
        label: 'Agree Positive',
        count: agreePositive,
        percentage: Math.round((agreePositive / total) * 100),
        color: '#22c55e'
      },
      {
        label: 'Agree Neutral',
        count: agreeNeutral,
        percentage: Math.round((agreeNeutral / total) * 100),
        color: '#64748b'
      },
      {
        label: 'Agree Negative',
        count: agreeNegative,
        percentage: Math.round((agreeNegative / total) * 100),
        color: '#ef4444'
      },
      {
        label: 'Disagree',
        count: disagree,
        percentage: Math.round((disagree / total) * 100),
        color: '#f59e0b'
      }
    ].filter(item => item.count > 0);
  }

  getConfidenceDistributionData(): { model: string; bins: any[]; avgConfidence: number; color: string }[] {
    if (!this.aiAnalytics || !this.aiAnalytics.confidence_data) return [];
    
    const vaderData = this.aiAnalytics.confidence_data.vader || [];
    const geminiData = this.aiAnalytics.confidence_data.gemini || [];
    
    const createBins = (data: number[]) => {
      const bins = [
        { range: '0-25%', min: 0, max: 25, count: 0 },
        { range: '26-50%', min: 26, max: 50, count: 0 },
        { range: '51-75%', min: 51, max: 75, count: 0 },
        { range: '76-100%', min: 76, max: 100, count: 0 }
      ];
      
      data.forEach(value => {
        const bin = bins.find(b => value >= b.min && value <= b.max);
        if (bin) bin.count++;
      });
      
      return bins.map(bin => ({
        range: bin.range,
        count: bin.count,
        percentage: data.length > 0 ? Math.round((bin.count / data.length) * 100) : 0
      }));
    };
    
    return [
      {
        model: 'VADER',
        bins: createBins(vaderData),
        avgConfidence: this.aiAnalytics.vader_avg_confidence || 0,
        color: '#3b82f6'
      },
      {
        model: 'Gemini AI',
        bins: createBins(geminiData),
        avgConfidence: this.aiAnalytics.gemini_avg_confidence || 0,
        color: '#8b5cf6'
      }
    ];
  }

  getAgreementDonutSegments(): { label: string; percentage: number; color: string; offset: number; dashArray: string }[] {
    const data = this.getModelAgreementData();
    if (data.length === 0) return [];
    
    let currentOffset = 0;
    const circumference = 2 * Math.PI * 45; // radius = 45
    
    return data.map(item => {
      const segmentLength = (item.percentage / 100) * circumference;
      const segment = {
        label: item.label,
        percentage: item.percentage,
        color: item.color,
        offset: currentOffset,
        dashArray: `${segmentLength} ${circumference}`
      };
      currentOffset += segmentLength;
      return segment;
    });
  }

  getConfidenceBarMaxHeight(bins: any[]): number {
    const maxCount = Math.max(...bins.map(b => b.count), 1);
    return maxCount;
  }

  // Overview Tab - Sentiment Distribution Donut Chart
  getSentimentDistributionData(): { label: string; count: number; percentage: number; icon: string; color: string }[] {
    const counts = this.sentimentCounts;
    const total = this.videos.length || 1;
    
    return [
      {
        label: 'Positive',
        count: counts.positive,
        percentage: Math.round((counts.positive / total) * 100),
        icon: '😊',
        color: '#22c55e'
      },
      {
        label: 'Neutral',
        count: counts.neutral,
        percentage: Math.round((counts.neutral / total) * 100),
        icon: '😐',
        color: '#64748b'
      },
      {
        label: 'Negative',
        count: counts.negative,
        percentage: Math.round((counts.negative / total) * 100),
        icon: '😟',
        color: '#ef4444'
      }
    ].filter(item => item.count > 0);
  }

  getSentimentDonutSegments(): { gradient: string; dashArray: string; offset: number }[] {
    const data = this.getSentimentDistributionData();
    if (data.length === 0) return [];
    
    let currentOffset = 0;
    const circumference = 2 * Math.PI * 50; // radius = 50
    
    const gradientMap: { [key: string]: string } = {
      'Positive': 'url(#positiveGrad)',
      'Neutral': 'url(#neutralGrad)',
      'Negative': 'url(#negativeGrad)'
    };
    
    return data.map(item => {
      const segmentLength = (item.percentage / 100) * circumference;
      const segment = {
        gradient: gradientMap[item.label],
        dashArray: `${segmentLength} ${circumference}`,
        offset: -currentOffset
      };
      currentOffset += segmentLength;
      return segment;
    });
  }

  Math = Math;
}
