import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // The base URL of our FastAPI backend
  private backendUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) { }

  analyzeTopic(topicName: string): Observable<any> {
    const endpoint = `${this.backendUrl}/analyze/`;
    const body = { topic_name: topicName };
    return this.http.post(endpoint, body);
  }
}