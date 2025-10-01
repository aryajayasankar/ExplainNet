import { Component, OnInit, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { Chart, ChartConfiguration, registerables } from 'chart.js/auto';
import { ApiService } from '../../services/api.service';
import { HttpClient } from '@angular/common/http';
import 'chartjs-adapter-date-fns';

@Component({
  selector: 'app-topic-detail',
  standalone: true,
  imports: [
    CommonModule, 
    MatButtonModule,
    MatButtonToggleModule,
    MatIconModule, 
    MatCardModule, 
    MatTabsModule, 
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTableModule,
    MatSelectModule,
    MatFormFieldModule
  ],
  templateUrl: './topic-detail.html',
  styleUrl: './topic-detail.scss'
})
export class TopicDetail implements OnInit, AfterViewInit {
  topicId: number = 0;
  topicData: any = null;
  isLoading = true;
  isLoadingNews = false;
  activeTabIndex = 0;
  
  // Analytics data
  channelAnalytics: any[] = [];
  videoTimeline: any[] = [];
  newsReliability: any[] = [];
  newsData: any = { 
    guardian: [], 
    newsapi: [], 
    guardian_count: 0, 
    newsapi_count: 0 
  };
  chart: Chart | null = null;
  timelineChart: Chart | null = null;
  selectedChartType: string = 'line';
  
  // Filter properties
  channelLimit: number = 5;
  sortBy: string = 'views_desc';
  chartVideoData: any[] = [];

  // Table columns for news
  displayedColumns: string[] = ['headline', 'source_name', 'publication_date', 'url'];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService,
    private http: HttpClient,
    private snackBar: MatSnackBar
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
        this.snackBar.open('Error loading channel analytics', 'Close', { duration: 3000 });
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
        this.snackBar.open('Error loading video timeline', 'Close', { duration: 3000 });
      }
    });

    // Load news reliability
    this.apiService.getNewsReliability(this.topicId).subscribe({
      next: (data) => {
        this.newsReliability = data;
        console.log('News Reliability:', data);
      },
      error: (error) => {
        console.error('Error loading news reliability:', error);
        this.snackBar.open('Error loading news reliability', 'Close', { duration: 3000 });
      }
    });

    // Load news data
    this.apiService.getNewsData(this.topicId).subscribe({
      next: (data) => {
        this.newsData = data;
        console.log('News Data:', data);
      },
      error: (error) => {
        console.error('Error loading news data:', error);
        this.snackBar.open('Error loading news data', 'Close', { duration: 3000 });
      }
    });
  }

  onTabChange(event: any): void {
    this.activeTabIndex = event.index;
    if (event.index === 1) { // News tab
      this.loadNewsData();
    }
  }

  loadNewsData() {
    if (!this.topicId) return;
    
    // Load news data if not already loaded
    if (this.newsData.guardian.length === 0 && this.newsData.newsapi.length === 0) {
      this.apiService.getNewsData(this.topicId).subscribe({
        next: (data) => {
          this.newsData = data;
          console.log('News Data loaded:', data);
        },
        error: (error) => {
          console.error('Error loading news data:', error);
          this.snackBar.open('Error loading news data', 'Close', { duration: 3000 });
        }
      });
    }
  }

  updateChart(): void {
    this.createTimelineChart();
  }

  createTimelineChart() {
    setTimeout(() => {
      console.log('Raw timeline data:', this.videoTimeline);
      console.log('Is array?', Array.isArray(this.videoTimeline));
      console.log('Data length:', this.videoTimeline?.length);
      
      // Debug: Show data structure
      if (this.videoTimeline && this.videoTimeline.length > 0) {
        console.log('Sample video data:', this.videoTimeline[0]);
        const channels = [...new Set(this.videoTimeline.map((v: any) => v.channel_name))];
        console.log('Unique channels:', channels);
        console.log('Videos per channel:', channels.map(ch => ({
          channel: ch,
          count: this.videoTimeline.filter((v: any) => v.channel_name === ch).length,
          dates: [...new Set(this.videoTimeline.filter((v: any) => v.channel_name === ch).map((v: any) => v.publication_date))]
        })));
      }
      
      if (!Array.isArray(this.videoTimeline) || this.videoTimeline.length === 0) {
        console.log('No valid timeline data to display');
        return;
      }

      const ctx = document.getElementById('timelineChart') as HTMLCanvasElement;
      if (!ctx) {
        console.log('Canvas element not found');
        return;
      }
      
      // Destroy existing chart if it exists
      if (this.timelineChart) {
        this.timelineChart.destroy();
      }

      // Create chart with the selected type
      const chartType = this.selectedChartType === 'scatter' ? 'scatter' : this.selectedChartType;
      
      // Create gradient colors for better visual appeal
      const gradientColors = [
        { bg: 'rgba(255, 99, 132, 0.6)', border: 'rgba(255, 99, 132, 1)' },   // Red
        { bg: 'rgba(54, 162, 235, 0.6)', border: 'rgba(54, 162, 235, 1)' },   // Blue
        { bg: 'rgba(255, 206, 86, 0.6)', border: 'rgba(255, 206, 86, 1)' },   // Yellow
        { bg: 'rgba(75, 192, 192, 0.6)', border: 'rgba(75, 192, 192, 1)' },   // Teal
        { bg: 'rgba(153, 102, 255, 0.6)', border: 'rgba(153, 102, 255, 1)' }, // Purple
        { bg: 'rgba(255, 159, 64, 0.6)', border: 'rgba(255, 159, 64, 1)' },   // Orange
        { bg: 'rgba(233, 30, 99, 0.6)', border: 'rgba(233, 30, 99, 1)' },     // Pink
        { bg: 'rgba(0, 150, 136, 0.6)', border: 'rgba(0, 150, 136, 1)' },     // Teal
        { bg: 'rgba(121, 85, 72, 0.6)', border: 'rgba(121, 85, 72, 1)' },     // Brown
        { bg: 'rgba(158, 158, 158, 0.6)', border: 'rgba(158, 158, 158, 1)' }  // Grey
      ];

      // Since we can't get historical view progression, let's show individual videos
      // Each video becomes a separate bar with click functionality
      
      let videoEntries = this.videoTimeline.map((video: any) => ({
        title: video.title || 'Untitled Video',
        channel: video.channel_name || 'Unknown Channel',
        views: video.view_count || 0,
        date: video.publication_date,
        url: video.url,
        video_id: video.video_id
      }));

      // Apply sorting to individual videos
      switch (this.sortBy) {
        case 'views_desc':
          videoEntries.sort((a, b) => b.views - a.views);
          break;
        case 'views_asc':
          videoEntries.sort((a, b) => a.views - b.views);
          break;
        case 'name_asc':
          videoEntries.sort((a, b) => a.channel.localeCompare(b.channel));
          break;
        case 'name_desc':
          videoEntries.sort((a, b) => b.channel.localeCompare(a.channel));
          break;
        case 'videos_desc':
          // For individual videos, sort by views instead
          videoEntries.sort((a, b) => b.views - a.views);
          break;
      }

      // Apply limit - ensure it doesn't exceed our API limit of 10
      const actualLimit = Math.min(this.channelLimit, 10);
      if (actualLimit > 0) {
        videoEntries = videoEntries.slice(0, actualLimit);
      }

      // Always use bar chart for individual videos (cleaner visualization)
      const smartChartType = 'bar';
      
      console.log('Displaying individual videos:', videoEntries.length);

      const datasets = [{
        label: 'Video Views',
        data: videoEntries.map((video, index) => video.views),
        backgroundColor: videoEntries.map((_, index) => {
          const colors = [
            'rgba(255, 99, 132, 0.8)',   // Red
            'rgba(54, 162, 235, 0.8)',   // Blue  
            'rgba(255, 206, 86, 0.8)',   // Yellow
            'rgba(75, 192, 192, 0.8)',   // Teal
            'rgba(153, 102, 255, 0.8)',  // Purple
            'rgba(255, 159, 64, 0.8)',   // Orange
            'rgba(233, 30, 99, 0.8)',    // Pink
            'rgba(0, 150, 136, 0.8)',    // Teal
            'rgba(121, 85, 72, 0.8)',    // Brown
            'rgba(158, 158, 158, 0.8)'   // Grey
          ];
          return colors[index % colors.length];
        }),
        borderColor: videoEntries.map((_, index) => {
          const colors = [
            'rgba(255, 99, 132, 1)',     // Red
            'rgba(54, 162, 235, 1)',     // Blue
            'rgba(255, 206, 86, 1)',     // Yellow
            'rgba(75, 192, 192, 1)',     // Teal
            'rgba(153, 102, 255, 1)',    // Purple
            'rgba(255, 159, 64, 1)',     // Orange
            'rgba(233, 30, 99, 1)',      // Pink
            'rgba(0, 150, 136, 1)',      // Teal
            'rgba(121, 85, 72, 1)',      // Brown
            'rgba(158, 158, 158, 1)'     // Grey
          ];
          return colors[index % colors.length];
        }),
        borderWidth: 2
      }];

      // Store video data for click handling
      this.chartVideoData = videoEntries;

      const config: ChartConfiguration = {
        type: 'bar',
        data: { 
          labels: videoEntries.map(video => `${video.channel}\n"${video.title.substring(0, 30)}..."`),
          datasets 
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: smartChartType === 'bar' ? 'nearest' : 'index'
          },
          plugins: {
            title: {
              display: true,
              text: 'Individual Video Performance',
              font: {
                size: 18,
                weight: 'bold'
              },
              color: '#2c3e50'
            },
            legend: {
              display: true,
              position: 'top',
              labels: {
                usePointStyle: true,
                padding: 20,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0,0,0,0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: 'rgba(255,255,255,0.1)',
              borderWidth: 1,
              cornerRadius: 8,
              displayColors: true,
              callbacks: {
                title: function(context: any) {
                  return 'Click to open video';
                },
                label: function(context: any) {
                  const videoData = context.chart.chartVideoData[context.dataIndex];
                  return [
                    `Channel: ${videoData.channel}`,
                    `Title: ${videoData.title}`,
                    `Views: ${videoData.views.toLocaleString()}`,
                    `Date: ${new Date(videoData.date).toLocaleDateString()}`
                  ];
                }
              }
            }
          },
          onClick: (event: any, elements: any) => {
            if (elements.length > 0) {
              const dataIndex = elements[0].index;
              const videoData = this.chartVideoData[dataIndex];
              if (videoData && videoData.url) {
                window.open(videoData.url, '_blank');
              }
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Videos (Click to Open)',
                font: {
                  size: 14,
                  weight: 'bold'
                },
                color: '#34495e'
              },
              grid: {
                color: 'rgba(0,0,0,0.1)'
              },
              ticks: {
                color: '#7f8c8d',
                maxRotation: 45
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'View Count',
                font: {
                  size: 14,
                  weight: 'bold'
                },
                color: '#34495e'
              },
              grid: {
                color: 'rgba(0,0,0,0.1)'
              },
              ticks: {
                color: '#7f8c8d',
                callback: function(value: any) {
                  return value.toLocaleString();
                }
              }
            }
          }
        }
      };

      try {
        this.timelineChart = new Chart(ctx, config);
        // Store video data for click handling
        (this.timelineChart as any).chartVideoData = videoEntries;
        console.log('Chart created successfully with clickable bars');
      } catch (error) {
        console.error('Chart creation failed:', error);
      }
    }, 1000); // Increased timeout
  }

  fetchHistoricalNews() {
    this.isLoadingNews = true;
    this.http.post(`http://127.0.0.1:8000/topics/${this.topicId}/fetch-historical-news/`, {}).subscribe({
      next: (response: any) => {
        this.snackBar.open('Historical news fetched successfully', 'Close', { duration: 3000 });
        this.loadNewsData(); // Reload data
        this.isLoadingNews = false;
      },
      error: (error) => {
        this.snackBar.open('Error fetching historical news', 'Close', { duration: 3000 });
        console.error('Error:', error);
        this.isLoadingNews = false;
      }
    });
  }

  fetchRecentNews() {
    this.isLoadingNews = true;
    this.http.post(`http://127.0.0.1:8000/topics/${this.topicId}/fetch-recent-news/`, {}).subscribe({
      next: (response: any) => {
        this.snackBar.open('Recent news fetched successfully', 'Close', { duration: 3000 });
        this.loadNewsData(); // Reload data
        this.isLoadingNews = false;
      },
      error: (error) => {
        this.snackBar.open('Error fetching recent news', 'Close', { duration: 3000 });
        console.error('Error:', error);
        this.isLoadingNews = false;
      }
    });
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