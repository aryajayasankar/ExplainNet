import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    MatTableModule,
    MatIconModule,
    MatCardModule,
    MatPaginatorModule,
    MatSortModule
  ],
  templateUrl: './analysis.component.html',
  styleUrl: './analysis.component.scss'
})
export class AnalysisComponent implements OnInit {
  topicControl = new FormControl('');
  isLoading = false;
  statusMessage = '';
  showResults = false; // Controls whether to show tabs
  currentTopicId: number | null = null;
  currentTopicName = '';
  
  // Analytics data for current topic
  videoData: any[] = [];
  recentNewsData: any[] = [];
  olderNewsData: any[] = [];
  
  // Loading states for each tab
  videoLoading = false;
  recentNewsLoading = false;
  olderNewsLoading = false;
  
  // Table columns
  videoColumns: string[] = ['title', 'publication_date', 'channel_name', 'view_count', 'url'];
  recentNewsColumns: string[] = ['headline', 'publication_date', 'source_name', 'url'];
  olderNewsColumns: string[] = ['headline', 'publication_date', 'source_name', 'url'];

  constructor(
    private apiService: ApiService
  ) {}

  ngOnInit(): void {
    // Component starts with only search bar visible
    // No data loading until user searches
  }

  startAnalysis() {
    const topicValue = this.topicControl.value;
    if (!topicValue) {
      return; // Don't run if the input is empty
    }

    this.isLoading = true;
    this.showResults = false;
    this.statusMessage = 'Starting analysis... This may take a minute.';

    this.apiService.analyzeTopic(topicValue).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.currentTopicId = response.topic_id;
        this.currentTopicName = topicValue;
        this.statusMessage = `Success! Analysis for "${topicValue}" is complete.`;
        this.showResults = true;
        
        // Load topic-specific data
        this.loadTopicData();
      },
      error: (error) => {
        this.isLoading = false;
        this.statusMessage = 'An error occurred during analysis. Please check the console.';
        console.error(error);
      }
    });
  }

  onTabChange(event: any): void {
    const tabIndex = event.index;
    
    switch(tabIndex) {
      case 0: // Videos tab
        this.loadTopicVideos();
        break;
      case 1: // Recent news tab
        this.loadTopicNews();
        break;
      case 2: // Older news tab
        this.loadTopicOlderNews();
        break;
      default:
        break;
    }
  }

  loadTopicData(): void {
    // Load all data for the current topic
    this.loadTopicVideos();
    this.loadTopicNews();
    this.loadTopicOlderNews();
  }

  loadTopicVideos(): void {
    if (!this.currentTopicId) return;
    
    this.videoLoading = true;
    this.apiService.getTopicVideos(this.currentTopicId).subscribe({
      next: (response) => {
        this.videoData = response.videos || [];
        this.videoLoading = false;
      },
      error: (error) => {
        console.error('Error loading video data:', error);
        this.videoLoading = false;
      }
    });
  }

  loadTopicNews(): void {
    if (!this.currentTopicId) return;
    
    this.recentNewsLoading = true;
    this.apiService.getTopicNews(this.currentTopicId).subscribe({
      next: (response: any) => {
        this.recentNewsData = response.newsapi || [];
        this.recentNewsLoading = false;
      },
      error: (error: any) => {
        console.error('Error loading news data:', error);
        this.recentNewsLoading = false;
      }
    });
  }

  loadTopicOlderNews(): void {
    if (!this.currentTopicId) return;
    
    this.olderNewsLoading = true;
    this.apiService.getTopicOlderNews(this.currentTopicId).subscribe({
      next: (response: any) => {
        this.olderNewsData = response.guardian || [];
        this.olderNewsLoading = false;
      },
      error: (error: any) => {
        console.error('Error loading older news data:', error);
        this.olderNewsLoading = false;
      }
    });
  }

  openLink(url: string): void {
    if (url) {
      window.open(url, '_blank');
    }
  }
}