import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Topic, TopicCreate } from '../../models/topic.model';

@Component({
  selector: 'app-locker',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './locker.component.html',
  styleUrls: ['./locker.component.scss']
})
export class LockerComponent implements OnInit {
  topics: Topic[] = [];
  loading = false;
  showCreateModal = false;
  newTopicName = '';
  creating = false;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadTopics();
  }

  loadTopics() {
    this.loading = true;
    this.apiService.getTopics().subscribe({
      next: (topics) => {
        this.topics = topics;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading topics:', err);
        this.loading = false;
      }
    });
  }

  openCreateModal() {
    this.showCreateModal = true;
    this.newTopicName = '';
  }

  closeCreateModal() {
    this.showCreateModal = false;
    this.newTopicName = '';
  }

  createTopic() {
    if (!this.newTopicName.trim()) return;
    
    this.creating = true;
    const topicData: TopicCreate = { topic_name: this.newTopicName };
    
    this.apiService.createTopic(topicData).subscribe({
      next: (topic) => {
        this.topics.unshift(topic);
        this.closeCreateModal();
        this.creating = false;
      },
      error: (err) => {
        console.error('Error creating topic:', err);
        this.creating = false;
      }
    });
  }

  deleteTopic(id: number, event: Event) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this topic?')) return;
    
    this.apiService.deleteTopic(id).subscribe({
      next: () => {
        this.topics = this.topics.filter(t => t.id !== id);
      },
      error: (err) => {
        console.error('Error deleting topic:', err);
      }
    });
  }

  getStatusClass(status: string): string {
    const classes: Record<string, string> = {
      completed: 'status-completed',
      processing: 'status-processing',
      pending: 'status-pending',
      failed: 'status-failed'
    };
    return classes[status] || '';
  }

  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      completed: '',
      processing: '',
      pending: '',
      failed: ''
    };
    return icons[status] || '?';
  }
}
