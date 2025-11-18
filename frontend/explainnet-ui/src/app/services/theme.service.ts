import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private darkMode = true;
  private isBrowser: boolean;
  private darkModeSubject = new BehaviorSubject<boolean>(true);
  public isDarkMode$: Observable<boolean> = this.darkModeSubject.asObservable();

  constructor(@Inject(PLATFORM_ID) platformId: object) {
    this.isBrowser = isPlatformBrowser(platformId);
    
    if (this.isBrowser) {
      // Load theme from localStorage or default to dark (only in browser)
      const savedTheme = localStorage.getItem('theme');
      this.darkMode = savedTheme !== 'light';
      this.darkModeSubject.next(this.darkMode);
      this.applyTheme();
    }
  }

  isDark(): boolean {
    return this.darkMode;
  }

  toggleTheme(): void {
    this.darkMode = !this.darkMode;
    this.darkModeSubject.next(this.darkMode);
    this.applyTheme();
    
    if (this.isBrowser) {
      localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
    }
  }

  private applyTheme(): void {
    if (this.isBrowser) {
      if (this.darkMode) {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
      } else {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
      }
    }
  }
}
