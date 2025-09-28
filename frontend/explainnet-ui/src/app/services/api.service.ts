import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) { }

  analyzeTopic(topicName: string): Observable<any> {
    const endpoint = `${this.backendUrl}/analyze/`;
    const body = { topic_name: topicName };
    return this.http.post(endpoint, body);
  }

  getTopics(): Observable<any[]> {
    const endpoint = `${this.backendUrl}/topics/`;
    return this.http.get<any[]>(endpoint);
  }

  // New methods for enhanced features
  getYouTubeMetrics(): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/youtube/`;
    return this.http.get(endpoint);
  }

  getNewsMetrics(): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/news/`;
    return this.http.get(endpoint);
  }

  getViewsTimeline(topic: string): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/youtube/timeline/${topic}`;
    return this.http.get(endpoint);
  }

  getSentimentAnalysis(topic: string): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/youtube/sentiment/${topic}`;
    return this.http.get(endpoint);
  }

  getSourceReliability(): Observable<any> {
    const endpoint = `${this.backendUrl}/metrics/news/reliability/`;
    return this.http.get(endpoint);
  }

  // Add these methods to your existing ApiService class

  getChannelAnalytics(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/channel-analytics/`;
    return this.http.get(endpoint);
  }

  getVideoTimeline(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/video-timeline/`;
    return this.http.get(endpoint);
  }

  getNewsData(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/news-data/`;
    return this.http.get(endpoint);
  }

  getYouTubeData(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/youtube-data/`;
    return this.http.get(endpoint);
  }

  getEnhancedNewsReliability(topicId: number): Observable<any> {
    const endpoint = `${this.backendUrl}/topics/${topicId}/enhanced-news-reliability/`;
    return this.http.get(endpoint);
  }

  
}