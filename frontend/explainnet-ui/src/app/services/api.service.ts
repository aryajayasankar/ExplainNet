import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, catchError, retry } from 'rxjs';
import { Topic } from '../models/topicmodel';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) { }

  // Error handling
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred';
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  analyzeTopic(topicName: string): Observable<any> {
    const endpoint = `${this.backendUrl}/analyze/`;
    const body = { topic_name: topicName };
    return this.http.post(endpoint, body).pipe(
      catchError(this.handleError)
    );
  }

  getTopics(): Observable<Topic[]> {
    const endpoint = `${this.backendUrl}/topics/`;
    return this.http.get<Topic[]>(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getTopicById(id: number): Observable<Topic> {
    return this.http.get<Topic>(`${this.backendUrl}/topics/${id}`).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // YouTube analytics
  getChannelAnalytics(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/channel-analytics/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getVideoTimeline(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/video-timeline/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // News analytics
  getNewsReliability(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/enhanced-news-reliability/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getGuardianArticles(topicId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/topics/${topicId}/news-data/`).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getNewsApiArticles(topicId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.backendUrl}/topics/${topicId}/news-data/`).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getNewsData(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/news-data/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getYouTubeData(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/youtube-data/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // News data fetching
  fetchHistoricalNews(topicId: number): Observable<any> {
    return this.http.post<any>(`${this.backendUrl}/topics/${topicId}/fetch-historical-news/`, {}).pipe(
      catchError(this.handleError)
    );
  }

  fetchRecentNews(topicId: number): Observable<any> {
    return this.http.post<any>(`${this.backendUrl}/topics/${topicId}/fetch-recent-news/`, {}).pipe(
      catchError(this.handleError)
    );
  }

  // Legacy methods for compatibility
  getYouTubeMetrics(): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/youtube/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getNewsMetrics(): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/news/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getViewsTimeline(topic: string): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/youtube/timeline/${topic}`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getSentimentAnalysis(topic: string): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/youtube/sentiment/${topic}`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getSourceReliability(): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/news/reliability/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getEnhancedNewsReliability(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/enhanced-news-reliability/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Analytics endpoints - Get all data across topics
  getAllVideos(): Observable<any> {
    const endpoint = `${this.backendUrl}/analytics/videos/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getAllRecentNews(): Observable<any> {
    const endpoint = `${this.backendUrl}/analytics/recent-news/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getAllOlderNews(): Observable<any> {
    const endpoint = `${this.backendUrl}/analytics/older-news/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Topic-specific analytics endpoints
  getTopicVideos(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/youtube-data/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getTopicNews(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/news-data/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  getTopicOlderNews(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/news-data/`;
    return this.http.get(endpoint).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  
}