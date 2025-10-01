import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router } from '@angular/router';
import { Topic } from '../../models/topicmodel';

@Component({
  selector: 'app-locker',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatProgressSpinnerModule],
  templateUrl: './locker.html',
  styleUrl: './locker.scss'
})
export class Locker implements OnInit {
  isLoading = true;
  topics: Topic[] = [];
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

  navigateToTopic(topic: Topic): void {
    this.router.navigate(['/locker', topic.topic_id]);
  }
}