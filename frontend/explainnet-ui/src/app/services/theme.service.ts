import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private darkMode = true;

  constructor() {
    // Load theme from localStorage or default to dark
    const savedTheme = localStorage.getItem('theme');
    this.darkMode = savedTheme !== 'light';
    this.applyTheme();
  }

  isDark(): boolean {
    return this.darkMode;
  }

  toggleTheme(): void {
    this.darkMode = !this.darkMode;
    this.applyTheme();
    localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
  }

  private applyTheme(): void {
    if (this.darkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  }
}
