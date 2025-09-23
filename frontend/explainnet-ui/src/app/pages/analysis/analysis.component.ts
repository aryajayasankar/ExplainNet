import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
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
    MatProgressSpinnerModule
  ],
  templateUrl: './analysis.component.html',
  styleUrl: './analysis.component.scss'
})
export class Analysis {
  topicControl = new FormControl('');
  isLoading = false;
  statusMessage = '';

  constructor(private apiService: ApiService) {}

  startAnalysis() {
    const topicValue = this.topicControl.value;
    if (!topicValue) {
      return; // Don't run if the input is empty
    }

    this.isLoading = true;
    this.statusMessage = 'Starting analysis... This may take a minute.';

    this.apiService.analyzeTopic(topicValue).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.statusMessage = `Success! Analysis for "${topicValue}" is complete.`;
        console.log(response);
      },
      error: (error) => {
        this.isLoading = false;
        this.statusMessage = 'An error occurred during analysis. Please check the console.';
        console.error(error);
      }
    });
  }
}