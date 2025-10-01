import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { Chart } from 'chart.js/auto';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule } from '@angular/forms';
import { Topic } from '../../models/topicmodel';

@Component({
  selector: 'app-locker',
  templateUrl: './locker.html',
  styleUrls: ['./locker.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    MatSelectModule,
    FormsModule
  ]
})
export class LockerComponent implements OnInit {
  displayedColumns: string[] = ['topic_name', 'article_count', 'video_count'];
  isLoading = false;
  activeTab: 'youtube' | 'news' = 'youtube';
  activeNewsTab: 'guardian' | 'overall' = 'guardian';
  selectedTopic: string = '';
  topics: Topic[] = []; // Changed to use proper Topic interface
  viewsChart: any;
  
  youtubeMetrics = {
    channels: [],
    viewsData: [],
    sentimentAnalysis: []
  };

  newsMetrics = {
    guardian: {
      reliability: 0,
      coverage: 0,
      articles: 0
    },
    overall: {
      sourcesRanking: [],
      topicCoverage: []
    }
  };

  constructor(private apiService: ApiService, private router: Router) {}

  ngOnInit() {
    this.loadTopics();
    this.loadMetrics();
  }

  // ADD THIS METHOD - This was missing!
  navigateToTopic(row: Topic) {
    console.log('Navigating to topic:', row);
    this.router.navigate(['/locker', row.topic_id]);
  }

  loadTopics() {
    this.apiService.getTopics().subscribe(
      (data) => {
        this.topics = data; // Store full objects instead of just names
        if (this.topics.length > 0) {
          this.selectedTopic = this.topics[0].topic_name;
          this.loadViewsTimeline(this.topics[0].topic_id);
        }
      },
      (error) => {
        console.error('Error loading topics:', error);
      }
    );
  }

  loadMetrics() {
    // For now, let's comment these out since the API methods don't exist yet
    /*
    this.apiService.getYouTubeMetrics().subscribe(
      (data) => {
        this.youtubeMetrics = data;
      }
    );

    this.apiService.getNewsMetrics().subscribe(
      (data) => {
        this.newsMetrics = data;
      }
    );
    */
  }

  loadViewsTimeline(topicId: number) {
    if (this.viewsChart) {
      this.viewsChart.destroy();
    }

    // For now, create mock data since the API method doesn't exist yet
    const mockData = {
      dates: ['2023-01-01', '2023-01-02', '2023-01-03'],
      channels: ['Channel 1', 'Channel 2'],
      views: [[100, 200, 300], [150, 250, 350]]
    };
    this.createViewsChart(mockData);

    /*
    // Uncomment this when the API method exists
    this.apiService.getViewsTimeline(topicId).subscribe(
      (data) => {
        this.createViewsChart(data);
      },
      (error) => {
        console.error('Error loading timeline:', error);
      }
    );
    */
  }

  private createViewsChart(data: any) {
    const ctx = document.getElementById('viewsChart') as HTMLCanvasElement;
    if (ctx) {
      this.viewsChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.dates,
          datasets: data.channels.map((channel: string, index: number) => ({
            label: channel,
            data: data.views[index],
            borderColor: this.getChartColor(index),
            fill: false
          }))
        },
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Views Over Time by Channel'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Views'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Publication Date'
              }
            }
          }
        }
      });
    }
  }

  private getChartColor(index: number): string {
    const colors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
      '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];
    return colors[index % colors.length];
  }

  onTopicChange(topic: string) {
    this.selectedTopic = topic;
    const selectedTopicObj = this.topics.find(t => t.topic_name === topic);
    if (selectedTopicObj) {
      this.loadViewsTimeline(selectedTopicObj.topic_id);
    }
  }
}