import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { tap, shareReplay } from 'rxjs/operators';
import { Topic, TopicCreate, Video, Sentiment, Comment, Transcript, NewsArticle } from '../models/topic.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiBaseUrl;
  private topicsCache$: Observable<Topic[]> | null = null;
  private topicsCacheTime: number = 0;
  private readonly CACHE_TTL = 10000; // 10 seconds cache

  constructor(private http: HttpClient) {}

  // Topic endpoints
  getTopics(): Observable<Topic[]> {
    const now = Date.now();
    
    // Return cached data if still valid
    if (this.topicsCache$ && (now - this.topicsCacheTime < this.CACHE_TTL)) {
      return this.topicsCache$;
    }
    
    // Otherwise fetch fresh data and cache it
    this.topicsCacheTime = now;
    this.topicsCache$ = this.http.get<Topic[]>(`${this.baseUrl}/topics`).pipe(
      shareReplay(1) // Share the result with all subscribers
    );
    
    return this.topicsCache$;
  }
  
  // Method to invalidate cache (call after creating/deleting topics)
  invalidateTopicsCache(): void {
    this.topicsCache$ = null;
    this.topicsCacheTime = 0;
  }

  getTopic(id: number): Observable<Topic> {
    return this.http.get<Topic>(`${this.baseUrl}/topics/${id}`);
  }

  createTopic(topic: TopicCreate): Observable<Topic> {
    return this.http.post<Topic>(`${this.baseUrl}/topics`, topic).pipe(
      tap(() => this.invalidateTopicsCache()) // Invalidate cache on create
    );
  }

  deleteTopic(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/topics/${id}`).pipe(
      tap(() => this.invalidateTopicsCache()) // Invalidate cache on delete
    );
  }

  // Video endpoints
  getVideosByTopic(topicId: number): Observable<Video[]> {
    return this.http.get<Video[]>(`${this.baseUrl}/topics/${topicId}/videos`);
  }

  getVideo(id: number): Observable<Video> {
    return this.http.get<Video>(`${this.baseUrl}/videos/${id}`);
  }

  // Sentiment endpoints
  getSentimentsByVideo(videoId: number): Observable<Sentiment[]> {
    return this.http.get<Sentiment[]>(`${this.baseUrl}/videos/${videoId}/sentiments`);
  }

  // Comment endpoints
  getCommentsByVideo(videoId: number): Observable<Comment[]> {
    return this.http.get<Comment[]>(`${this.baseUrl}/videos/${videoId}/comments`);
  }

  // Transcript endpoints
  getTranscriptByVideo(videoId: number): Observable<Transcript> {
    return this.http.get<Transcript>(`${this.baseUrl}/videos/${videoId}/transcript`);
  }

  // News endpoints
  getArticlesByTopic(topicId: number): Observable<NewsArticle[]> {
    return this.http.get<NewsArticle[]>(`${this.baseUrl}/topics/${topicId}/articles`);
  }

  // Analysis Tab endpoints
  getVideosAnalysis(topicId: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/topics/${topicId}/videos-analysis`);
  }

  getNewsAnalysis(topicId: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/topics/${topicId}/news-analysis`);
  }

  getAISummary(topicId: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/topics/${topicId}/ai-summary`);
  }

  getAISynthesis(topicId: number, forceRefresh: boolean = false): Observable<any> {
    const url = `${this.baseUrl}/topics/${topicId}/ai-synthesis`;
    return forceRefresh 
      ? this.http.get<any>(url, { params: { force_refresh: 'true' } })
      : this.http.get<any>(url);
  }
}
