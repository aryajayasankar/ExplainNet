import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-topic-detail',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatCardModule, MatTabsModule],
  templateUrl: './topic-detail.html',
  styleUrl: './topic-detail.scss'
})
export class TopicDetail implements OnInit {
  topicId: number = 0;
  topicData: any = null;
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.topicId = +params['id'];
      this.loadTopicData();
    });
  }

  loadTopicData() {
    this.apiService.getTopics().subscribe(
      (topics) => {
        this.topicData = topics.find(t => t.topic_id === this.topicId);
        this.isLoading = false;
      },
      (error) => {
        console.error('Error loading topic data:', error);
        this.isLoading = false;
      }
    );
  }

  goBackToLocker() {
    this.router.navigate(['/locker']);
  }
}