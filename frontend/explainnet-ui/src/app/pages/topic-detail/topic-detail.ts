import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { Chart, ChartConfiguration } from 'chart.js/auto';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-topic-detail',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatCardModule, MatTabsModule],
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
  ) {}

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
    this.apiService.getTopics().subscribe(
      (topics) => {
        this.topicData = topics.find(t => t.topic_id === this.topicId);
        if (this.topicData) {
          this.loadAnalyticsData();
        }
        this.isLoading = false;
      },
      (error) => {
        console.error('Error loading topic data:', error);
        this.isLoading = false;
      }
    );
  }

  loadAnalyticsData() {
    // Load channel analytics
    this.apiService.getChannelAnalytics(this.topicId).subscribe(
      (data) => {
        this.channelAnalytics = data;
        console.log('Channel Analytics:', data);
      },
      (error) => {
        console.error('Error loading channel analytics:', error);
      }
    );

    // Load video timeline
    this.apiService.getVideoTimeline(this.topicId).subscribe(
      (data) => {
        this.videoTimeline = data;
        console.log('Video Timeline:', data);
        this.createTimelineChart();
      },
      (error) => {
        console.error('Error loading video timeline:', error);
      }
    );
  }

  createTimelineChart() {
    if (!this.timelineChart || this.videoTimeline.length === 0) return;

    const ctx = this.timelineChart.nativeElement;
    
    // Destroy existing chart if it exists
    if (this.chart) {
      this.chart.destroy();
    }

    // Prepare data for chart
    const chartData = this.videoTimeline.map(video => ({
      x: video.publication_date,
      y: video.view_count,
      label: video.title,
      channel: video.channel_name
    }));

    const config: ChartConfiguration = {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Video Views Over Time',
          data: chartData,
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Video Views vs Publication Date'
          },
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              displayFormats: {
                day: 'MMM DD'
              }
            },
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

    this.chart = new Chart(ctx, config);
  }

  goBackToLocker() {
    this.router.navigate(['/locker']);
  }
}