import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  // Signal for reactive theme state
  private themeSignal = signal<Theme>('dark');
  
  // Public readonly signal
  public readonly theme = this.themeSignal.asReadonly();
  
  // Local storage key
  private readonly THEME_KEY = 'explainnet-theme';

  constructor() {
    this.initializeTheme();
  }

  /**
   * Initialize theme from localStorage or system preference
   */
  private initializeTheme(): void {
    // Check localStorage first
    const savedTheme = localStorage.getItem(this.THEME_KEY) as Theme | null;
    
    if (savedTheme) {
      this.setTheme(savedTheme);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem(this.THEME_KEY)) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  /**
   * Set the theme
   */
  setTheme(theme: Theme): void {
    this.themeSignal.set(theme);
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.THEME_KEY, theme);
    
    // Dispatch event for other components that might need to know
    window.dispatchEvent(new CustomEvent('theme-changed', { detail: { theme } }));
  }

  /**
   * Toggle between light and dark theme
   */
  toggleTheme(): void {
    const currentTheme = this.themeSignal();
    const newTheme: Theme = currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }

  /**
   * Get current theme value
   */
  getCurrentTheme(): Theme {
    return this.themeSignal();
  }

  /**
   * Check if current theme is dark
   */
  isDark(): boolean {
    return this.themeSignal() === 'dark';
  }

  /**
   * Check if current theme is light
   */
  isLight(): boolean {
    return this.themeSignal() === 'light';
  }

  /**
   * Reset theme to system preference
   */
  resetToSystemPreference(): void {
    localStorage.removeItem(this.THEME_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.setTheme(prefersDark ? 'dark' : 'light');
  }
}
