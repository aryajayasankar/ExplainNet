import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Chart, ChartConfiguration, registerables } from 'chart.js/auto';
import { ApiService } from '../../services/api.service';
import 'chartjs-adapter-date-fns';

@Component({
  selector: 'app-topic-detail',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatCardModule, MatTabsModule, MatProgressSpinnerModule],
  templateUrl: './topic-detail.html',
  styleUrl: './topic-detail.scss'
})
export class TopicDetail implements OnInit, AfterViewInit {
  @ViewChild('timelineChart', { static: false }) timelineChart!: ElementRef;
  
  topicId: number = 0;
  topicData: any = null;
  isLoading = true;
  
  // Analytics data
  channelAnalytics: any[] = [];
  videoTimeline: any[] = [];
  chart: Chart | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
  ) {
    Chart.register(...registerables);
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.topicId = +params['id'];
      this.loadTopicData();
    });
  }

  ngAfterViewInit() {
    // Chart will be created after data loads
  }

  loadTopicData() {
    this.apiService.getTopics().subscribe({
      next: (topics) => {
        this.topicData = topics.find(t => t.topic_id === this.topicId);
        if (this.topicData) {
          this.loadAnalyticsData();
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading topic data:', error);
        this.isLoading = false;
      }
    });
  }

  loadAnalyticsData() {
    // Load channel analytics
    this.apiService.getChannelAnalytics(this.topicId).subscribe({
      next: (data) => {
        this.channelAnalytics = data;
        console.log('Channel Analytics:', data);
      },
      error: (error) => {
        console.error('Error loading channel analytics:', error);
      }
    });

    // Load video timeline
    this.apiService.getVideoTimeline(this.topicId).subscribe({
      next: (data) => {
        this.videoTimeline = data;
        console.log('Video Timeline:', data);
        this.createTimelineChart();
      },
      error: (error) => {
        console.error('Error loading video timeline:', error);
      }
    });
  }

  createTimelineChart() {
    setTimeout(() => {
      console.log('Raw timeline data:', this.videoTimeline);
      console.log('Is array?', Array.isArray(this.videoTimeline));
      console.log('Data length:', this.videoTimeline?.length);
      
      if (!this.timelineChart) {
        console.log('Canvas element not found');
        return;
      }
      
      if (!Array.isArray(this.videoTimeline) || this.videoTimeline.length === 0) {
        console.log('No valid timeline data');
        return;
      }

      const ctx = this.timelineChart.nativeElement;
      
      // Destroy existing chart if it exists
      if (this.chart) {
        this.chart.destroy();
      }

      // Test with simple configuration first
      const config: ChartConfiguration = {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Video Views',
            data: this.videoTimeline.map(video => ({
              x: video.publication_date,
              y: video.view_count
            })),
            backgroundColor: '#36A2EB',
            borderColor: '#36A2EB',
            borderWidth: 2,
            pointRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Video Views vs Publication Date'
            }
          },
          scales: {
            x: {
              type: 'time',
              title: {
                display: true,
                text: 'Publication Date'
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Views'
              }
            }
          }
        }
      };

      try {
        this.chart = new Chart(ctx, config);
        console.log('Chart created successfully');
      } catch (error) {
        console.error('Chart creation failed:', error);
      }
    }, 1000); // Increased timeout
  }

  private getChartColor(index: number): string {
    const colors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
      '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];
    return colors[index % colors.length];
  }

  goBackToLocker() {
    this.router.navigate(['/locker']);
  }
}