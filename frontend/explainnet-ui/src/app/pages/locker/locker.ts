import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router } from '@angular/router';

export interface TopicData {
  topic_id: number;
  topic_name: string;
  article_count: number;
  video_count: number;
}

@Component({
  selector: 'app-locker',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatProgressSpinnerModule],
  templateUrl: './locker.html',
  styleUrl: './locker.scss'
})
export class Locker implements OnInit {
  isLoading = true;
  topics: TopicData[] = [];
  displayedColumns: string[] = ['topic_name', 'article_count', 'video_count'];

  constructor(private apiService: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.apiService.getTopics().subscribe({
      next: (data) => {
        this.topics = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching topics', err);
        this.isLoading = false;
      }
    });
  }

  navigateToTopic(topic: TopicData): void {
    this.router.navigate(['/locker', topic.topic_id]);
  }
}