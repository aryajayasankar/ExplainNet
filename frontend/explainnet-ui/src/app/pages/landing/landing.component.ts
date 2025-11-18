import { Component, OnInit, PLATFORM_ID, Inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss']
})
export class LandingComponent implements OnInit {
  isDarkMode$: Observable<boolean>;
  
  features = [
    {
      icon: '🎥',
      title: 'YouTube Analysis',
      description: 'Deep dive into video content with AI-powered sentiment analysis and transcription.',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
    },
    {
      icon: '📰',
      title: 'News Intelligence',
      description: 'Aggregate and analyze news articles to understand media sentiment and trends.',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
    },
    {
      icon: '🤖',
      title: 'AI Insights',
      description: 'Powered by Gemini and HuggingFace models for comprehensive sentiment analysis.',
      gradient: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)'
    },
    {
      icon: '📊',
      title: 'Real-time Metrics',
      description: 'Track sentiment trends, engagement patterns, and impact scores in real-time.',
      gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    }
  ];
  
  stats = [
    { value: '10K+', label: 'Videos Analyzed', icon: '🎬' },
    { value: '50K+', label: 'News Articles', icon: '📑' },
    { value: '1M+', label: 'Comments Processed', icon: '💬' },
    { value: '99.9%', label: 'Accuracy', icon: '✨' }
  ];

  constructor(
    private router: Router,
    private themeService: ThemeService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isDarkMode$ = this.themeService.isDarkMode$;
  }

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      // Add entrance animations
      setTimeout(() => {
        document.querySelectorAll('.animate-on-load').forEach((el, index) => {
          setTimeout(() => {
            el.classList.add('visible');
          }, index * 100);
        });
      }, 100);
    }
  }

  navigateToLocker(): void {
    this.router.navigate(['/locker']);
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }
}
