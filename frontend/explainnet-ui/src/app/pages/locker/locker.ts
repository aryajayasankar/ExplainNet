import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatOptionModule } from '@angular/material/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Topic } from '../../models/topicmodel';

@Component({
  selector: 'app-locker',
  standalone: true,
  imports: [
    CommonModule, 
    MatTableModule, 
    MatProgressSpinnerModule,
    MatSelectModule,
    MatFormFieldModule,
    MatOptionModule,
    FormsModule
  ],
  templateUrl: './locker.html',
  styleUrl: './locker.scss'
})
export class Locker implements OnInit {
  isLoading = true;
  topics: Topic[] = [];
  timezones: any[] = [];
  selectedTimezone: string = 'UTC';
  displayedColumns: string[] = ['topic_name', 'search_date', 'article_count', 'video_count'];

  constructor(private apiService: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.loadTimezones();
    this.loadTopics();
  }

  loadTimezones() {
    this.apiService.getTimezones().subscribe({
      next: (data) => {
        this.timezones = data.timezones;
      },
      error: (error) => {
        console.error('Error loading timezones:', error);
      }
    });
  }

  onTimezoneChange() {
    this.loadTopics();
  }

  loadTopics() {
    this.isLoading = true;
    this.apiService.getTopics(this.selectedTimezone).subscribe({
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