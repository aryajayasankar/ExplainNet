import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Topic, TopicCreate, Video, Sentiment, Comment, Transcript, NewsArticle } from '../models/topic.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  // Topic endpoints
  getTopics(): Observable<Topic[]> {
    return this.http.get<Topic[]>(`${this.baseUrl}/topics`);
  }

  getTopic(id: number): Observable<Topic> {
    return this.http.get<Topic>(`${this.baseUrl}/topics/${id}`);
  }

  createTopic(topic: TopicCreate): Observable<Topic> {
    return this.http.post<Topic>(`${this.baseUrl}/topics`, topic);
  }

  deleteTopic(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/topics/${id}`);
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

  getAISynthesis(topicId: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/topics/${topicId}/ai-synthesis`);
  }
}
